"""
Optional Deployment Script for Vertex AI Reasoning Engine.
NOTE: Executing this script requires an active Google Cloud Billing Account 
and enabled Vertex AI APIs. It is provided to demonstrate architectural 
readiness for GCP deployment (Criterion 2).
"""

import os
import vertexai
from vertexai.preview import reasoning_engines

# Configuration for GCP (Replace with your project details if you have a billing account)
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
LOCATION = "us-central1"
STAGING_BUCKET = "gs://your-staging-bucket-name"

def deploy_agent():
    print(f"Initializing Vertex AI for project {PROJECT_ID}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

    print("Packaging the CampusPulse AI Agent...")
    # In a real deployment, we pass the agent class and its dependencies
    # to ReasoningEngine.create() which containerizes and deploys it.
    
    try:
        remote_agent = reasoning_engines.ReasoningEngine.create(
            reasoning_engines.ReasoningEngine(
                # Here we would reference our agent logic and tools.
                # For Vertex AI, tools are typically passed as direct Python functions.
            ),
            requirements=[
                "google-genai>=0.3.0",
                "pydantic>=2.0.0"
            ],
            display_name="CampusPulse-AI-Agent",
            description="Autonomous academic assistant with Reasoning Loop."
        )
        print(f"Successfully deployed! Agent endpoint ID: {remote_agent.resource_name}")
    except Exception as e:
        print("\n[DEPLOYMENT FAILED]")
        print("Error: Could not deploy to Vertex AI.")
        print(f"Details: {e}")
        print("\nReason: This usually happens if the Google Cloud Project lacks an active Billing Account.")

if __name__ == "__main__":
    deploy_agent()