import asyncio
import json
from datetime import datetime
from google import genai
from google.genai import types

from mcp_client import MCPBridge
from config import GEMINI_API_KEY
import logging

logger = logging.getLogger(__name__)

class CampusPulseAgent:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_id = 'gemini-3.5-flash-lite'
        self.mcp = MCPBridge()
        self.tools = []
        
        today = datetime.now().strftime("%Y-%m-%d")
        self.system_instruction = (
            "You are CampusPulse AI, an autonomous academic assistant for university students. "
            "Your core goal is to help students manage assignments, track deadlines, and organize study plans. "
            f"Today's date is {today}. "
            "You have access to local tools via MCP to fetch and modify the user's schedule. "
            "CRITICAL RULES: "
            "1. NEVER invent or hallucinate deadlines, assignments, or campus data. "
            "2. If the user asks about their tasks, ALWAYS use the provided tools to query the database first. "
            "3. After creating or modifying a task, verify the result. "
            "4. Provide concise, clear, and structured answers."
            "5. Use the search_study_materials tool to analyze lecture notes and PDFs when the user asks academic questions."
        )

    async def initialize(self):
        """Подключается к MCP серверу и конвертирует схемы в Gemini Function Declarations."""
        await self.mcp.connect()
        mcp_tools = await self.mcp.get_tools()
        
        function_declarations = []
        for t in mcp_tools:
            properties = {}
            required = t.get('inputSchema', {}).get('required', [])
            
            for prop_name, prop_details in t.get('inputSchema', {}).get('properties', {}).items():
                schema_type_str = prop_details.get('type', 'string')
                if schema_type_str == 'integer':
                    prop_type = types.Type.INTEGER
                elif schema_type_str == 'boolean':
                    prop_type = types.Type.BOOLEAN
                else:
                    prop_type = types.Type.STRING
                    
                properties[prop_name] = types.Schema(
                    type=prop_type,
                    description=prop_details.get('description', '')
                )
            
            func_decl = types.FunctionDeclaration(
                name=t['name'],
                description=t['description'],
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=properties,
                    required=required
                )
            )
            function_declarations.append(func_decl)
            
        self.tools = [types.Tool(function_declarations=function_declarations)]

    def _get_user_friendly_error(self, error):
        """Convert API and connection errors into user-friendly messages."""

        status_code = getattr(error, "code", None)

        if status_code == 429:
            return (
                "Сейчас превышен лимит запросов к ИИ. "
                "Попробуй позже или проверь квоты API."
            )

        if status_code in (401, 403):
            return (
                "Не удалось авторизоваться в сервисе ИИ. "
                "Проверь API-ключ и настройки доступа."
            )

        if status_code is not None and status_code >= 500:
            return (
                "Сервис ИИ временно недоступен. "
                "Попробуй повторить запрос позже."
            )

        error_text = str(error).lower()

        if any(term in error_text for term in (
            "connection", "timeout", "timed out",
            "network", "ssl", "handshake"
        )):
            return (
                "Не удалось подключиться к сервису ИИ. "
                "Проверь интернет-соединение и попробуй ещё раз."
            )

        return (
            "Не удалось обработать запрос. "
            "Попробуй переформулировать его или повторить позже."
        )

    async def process_request(self, user_prompt: str, chat_history: list = None):
        """Reasoning Loop: генератор, возвращающий шаги выполнения агента."""
        try:
            if chat_history is None:
                chat_history = []
                
            messages = list(chat_history)
            # Исправлено: передаем текст строго через kwarg text=
            messages.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))
            
            config = types.GenerateContentConfig(
                tools=self.tools,
                system_instruction=self.system_instruction,
                temperature=0.2 
            )

            max_iterations = 8
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=messages,
                    config=config
                )
                
                if response.candidates and response.candidates[0].content:
                    messages.append(response.candidates[0].content)
                
                function_calls = []
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            function_calls.append(part.function_call)
                
                if not function_calls:
                    final_text = response.text if response.text else "No response generated."
                    yield {"type": "final_answer", "text": final_text}
                    break
                    
                for fc in function_calls:
                    tool_name = fc.name
                    args = {k: v for k, v in fc.args.items()} if fc.args else {}
                    
                    yield {
                        "type": "tool_call",
                        "tool": tool_name,
                        "args": args
                    }
                    
                    result_text = await self.mcp.call_tool(tool_name, args)
                    
                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": result_text
                    }
                    
                    messages.append(types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": result_text}
                            )
                        ]
                    ))
                    
            if iteration >= max_iterations:
                yield {"type": "error", "text": "Max reasoning iterations reached. Stopping to prevent infinite loop."}

        except Exception as e:
            logger.exception("Error while processing user request")

            yield {
                "type": "error",
                "text": self._get_user_friendly_error(e)
            }

    async def close(self):
        await self.mcp.disconnect()

# ---------------------------------------------------------
# Test block: Execute this file directly to test AI Autonomy
# ---------------------------------------------------------
if __name__ == "__main__":
    async def run_test():
        print("Initializing CampusPulse Agent...")
        agent = CampusPulseAgent()
        await agent.initialize()
        
        prompt = "I have a new High priority task due in 3 days. The course is 'Cloud Computing' and title is 'Deploy MCP Server'. Create it, then list all my pending assignments."
        print(f"\nUser: {prompt}\n")
        
        print("--- Reasoning Loop Execution ---")
        async for step in agent.process_request(prompt):
            if step["type"] == "tool_call":
                print(f"[Agent -> MCP] Calling tool: {step['tool']}")
                print(f"             Arguments: {step['args']}")
            elif step["type"] == "tool_result":
                print(f"[MCP -> Agent] Result: {step['result']}")
            elif step["type"] == "final_answer":
                print(f"\n[Final Output]:\n{step['text']}")
            elif step["type"] == "error":
                print(f"\n[Error]: {step['text']}")
                
        await agent.close()

    asyncio.run(run_test())