#!/usr/bin/env python
# coding: utf-8

# # Build and deploy Agents
# ---
# 
# In this notebook, we will create the simple travel agent as before and then deploy it. This sample will go over how you can build and deploy LangGraph agents with a progression from local development to serverless deployment. For deployment, we will do as follows:
# 
# 1. **Create a simple travel agent using LangGraph**: We will create a simple travel agent with memory enabled. This agent will be responsible for taking in a user query and returning a response based on the query. The agent will be able to remember the context of the conversation and provide relevant information. We will also bind tools to the agent that we will create.
# 
# 1. **Fast API server**: `FastAPI` is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints. We will use `FastAPI` to create a simple web server that will host our agent. The server will accept user queries and return responses from the agent.
# 
# 1. **Docker containerization**: We will then package the application into a Docker container. Docker is a platform that enables developers to automate the deployment of applications inside lightweight, portable containers. This will allow us to run our application in any environment that supports Docker.
# 
# 1. **AWS Lambda deployment**: Next, we will deploy the docker container to AWS lambda with API gateway. AWS Lambda is a serverless compute service that runs your code in response to events and automatically manages the underlying compute resources for you. This will allow us to run our application without having to manage any servers.


# first, lets import the necessary libraries required to build the agent in this notebook
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables.graph import MermaidDrawMethod
from IPython.display import Image, display

class PlannerState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], "The messages in the conversation"]
    itinerary: Optional[str]
    city: str
    user_message: str
    weather_info: Optional[str]
    attractions_info: Optional[str]

# represents the global variables used across this notebook
BEDROCK_RUNTIME: str = 'bedrock-runtime'
# Model ID used by the agent
AMAZON_NOVA_LITE_MODEL_ID: str = "us.amazon.nova-lite-v1:0"
PROVIDER_ID : str = 'amazon'
# Inference parameters
TEMPERATURE: float = 0.1
MAX_TOKENS: int = 512

import boto3
import logging
# We are importing this to use any model supported on Amazon Bedrock. In this example
# we will be using the Amazon Nova lite model.
from langchain_aws import ChatBedrockConverse
# This helps checkpoint the memory state of the agent for short term/long term memory
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.config import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# set a logger
logging.basicConfig(format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

session = boto3.session.Session()
region = session.region_name
logger.info(f"Running this example in region: {region}")

# Initialize the bedrock client placeholder
bedrock_client = boto3.client("bedrock-runtime")

# Create the llm used by the agent
llm = ChatBedrockConverse(
    model=AMAZON_NOVA_LITE_MODEL_ID,
    provider=PROVIDER_ID, 
    temperature=TEMPERATURE, 
    max_tokens=MAX_TOKENS,
    client=bedrock_client,
)


from langchain_core.tools import tool
import json
import os

@tool
def mock_search_tourist_attractions(city: str) -> str:
    """
    Search for tourist attractions in the specified city using a local JSON file.
    
    Args:
        city: The name of the city to search for attractions
        
    Returns:
        A string containing information about tourist attractions in the city
    """
    try:
        # Path to the JSON file containing the attraction data
        file_path = os.path.join("data", "attractions.json")
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return f"Error: Attractions data file not found. Please make sure '{file_path}' exists."
        
        # Load the attractions data from the JSON file
        with open(file_path, 'r') as f:
            attractions_data = json.load(f)
        
        # Check if the city exists in the data
        if city.lower() not in attractions_data:
            return f"No information available for tourist attractions in {city}. Try another city."
        
        # Get the attractions for the specified city
        city_attractions = attractions_data[city.lower()]
        
        # Format the attractions information
        attractions = f"Top boating and swimming attractions in {city}:\n"
        for i, attraction in enumerate(city_attractions, 1):
            attractions += f"{i}. {attraction['title']}: {attraction['description'][:150]}...\n"
        
        return attractions
    
    except Exception as e:
        return f"An error occurred while searching for tourist attractions in {city}: {str(e)}"

@tool
def mock_get_weather_forecast(city: str) -> str:
    """
    Get the current weather forecast for the specified city using a local JSON file.
    
    Args:
        city: The name of the city to get the weather forecast for
        
    Returns:
        A string containing the weather forecast for the city
    """
    try:
        # Path to the JSON file containing the weather data
        file_path = os.path.join("data", "weather.json")
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return f"Error: Weather data file not found. Please make sure '{file_path}' exists."
        
        # Load the weather data from the JSON file
        with open(file_path, 'r') as f:
            weather_data = json.load(f)
        
        # Check if the city exists in the data
        if city.lower() not in weather_data:
            return f"No weather information available for {city}. Try another city."
        
        # Get the weather data for the specified city
        city_weather = weather_data[city.lower()]
        
        # Extract location and current weather information
        location = city_weather["location"]
        current = city_weather["current"]
        
        # Format the weather information
        forecast = f"Current weather in {location['name']}, {location['country']}:\n"
        forecast += f"Local time: {location['localtime']}\n"
        forecast += f"Temperature: {current['temperature']}°C\n"
        forecast += f"Weather: {', '.join(current['weather_descriptions'])}\n"
        forecast += f"Feels like: {current['feelslike']}°C\n"
        forecast += f"Humidity: {current['humidity']}%\n"
        forecast += f"Wind: {current['wind_speed']} km/h, {current['wind_dir']}\n"
        forecast += f"Pressure: {current['pressure']} mb\n"
        forecast += f"Visibility: {current['visibility']} km\n"
        forecast += f"UV Index: {current['uv_index']}\n"
        
        # Add precipitation information if available
        if 'precip' in current:
            forecast += f"Precipitation: {current['precip']} mm\n"
            
        # Add cloud cover information if available
        if 'cloudcover' in current:
            forecast += f"Cloud cover: {current['cloudcover']}%\n"
            
        # Add air quality information if available
        if 'air_quality' in current:
            aq = current['air_quality']
            forecast += "\nAir Quality:\n"
            forecast += f"US EPA Index: {aq['us-epa-index']} "
            
            # Add interpretation of EPA index
            epa_index = aq['us-epa-index']
            if epa_index == 1:
                forecast += "(Good)\n"
            elif epa_index == 2:
                forecast += "(Moderate)\n"
            elif epa_index == 3:
                forecast += "(Unhealthy for sensitive groups)\n"
            elif epa_index == 4:
                forecast += "(Unhealthy)\n"
            elif epa_index == 5:
                forecast += "(Very Unhealthy)\n"
            elif epa_index == 6:
                forecast += "(Hazardous)\n"
            else:
                forecast += "\n"
                
        return forecast
    
    except Exception as e:
        return f"An error occurred while getting the weather forecast for {city}: {str(e)}"

tools = [mock_search_tourist_attractions, mock_get_weather_forecast]


from langgraph.prebuilt import create_react_agent

# Create the ReAct agent with the correct prompt
get_realtime_info_react_llm = create_react_agent(
    llm,
    tools=tools
)

# The first node that solely inputs a user message
# The first node that takes in user input
def input_interest(state: PlannerState) -> PlannerState:
    """
    This function processes the user's message.
    """
    # Initialize messages if needed
    if not state.get('messages'): 
        state['messages'] = []
    
    # Return updated state
    return {
        **state
    }

def create_itinerary(state: PlannerState) -> PlannerState:
    try:
        messages = [
            HumanMessage(content=state['user_message'])
        ]
        agent_input = {
            "messages": messages
        }
        
        # Invoke the agent
        result = get_realtime_info_react_llm.invoke(agent_input)
        
        # Extract the output
        if isinstance(result, dict) and "output" in result:
            itinerary = result["output"]
        else:
            itinerary = str(result)
        
        # Return state
        return {
            **state,
            'messages': [
                *state.get('messages', []),
                HumanMessage(content=state['user_message']),
                AIMessage(content=itinerary)
            ],
            'itinerary': itinerary
        }
    except Exception as e:
        logger.error(f"Error creating itinerary: {e}")
        error_message = f"I apologize, but I encountered an error while creating your itinerary: {str(e)}"
        
        # Print the exception for debugging
        import traceback
        traceback.print_exc()
        
        # Return updated state with error
        return {
            **state,
            'messages': [
                *state['messages'],
                HumanMessage(content=state['user_message']),
                AIMessage(content=error_message)
            ],
            'itinerary': error_message
        }

# initialize the StateGraph
workflow = StateGraph(PlannerState)
# Next, we will add our nodes to this workflowa
workflow.add_node("input_user_interests", input_interest)
workflow.add_node("create_itinerary", create_itinerary)
workflow.set_entry_point("input_user_interests")
# Next, we will add a direct edge between input interests and create itinerary
workflow.add_edge("input_user_interests", "create_itinerary")
workflow.add_edge("create_itinerary", END)
app = workflow.compile()

display(
    Image(
        app.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
        )
    )
)

def print_stream(result):
    """
    Pretty prints the raw response from a LangGraph workflow result.
    """
    import json
    from pprint import pprint
    
    print("\n" + "=" * 50 + "\n")
    
    # For dictionary results
    if isinstance(result, dict):
        if "messages" in result:
            # Print each message in a readable format
            for i, message in enumerate(result["messages"]):
                # Get message type
                msg_type = type(message).__name__
                print(f"[Message {i+1}] Type: {msg_type}")
                
                # Print content in readable format
                if hasattr(message, "content"):
                    print("\nContent:")
                    if isinstance(message.content, list):
                        for j, part in enumerate(message.content):
                            print(f"\n-- Part {j+1} --")
                            pprint(part)
                    else:
                        print(message.content)
                    
                print("\n" + "-" * 50 + "\n")
        else:
            # Just pretty print the dictionary
            pprint(result)
    
    # For list results
    elif isinstance(result, list):
        for i, item in enumerate(result):
            print(f"\n[Item {i+1}]\n")
            print_stream(item)  # Recursively handle items
    
    # For other types
    else:
        print(f"Type: {type(result)}")
        print("\nContent:")
        print(result)
        
    print("\n" + "=" * 50 + "\n")

# Create pydandic models for the input and output
from typing import Any
from pydantic import BaseModel, Field

class ItineraryInput(BaseModel):
    """
    Request the agent for itinerary generation
    """
    # input the user message
    user_message: str = Field(
        ...,
        description="The user's message containing their interests and preferences for the itinerary."
    )

class ItineraryOutput(BaseModel):
    """
    Response model for itinerary generation.
    """
    itinerary: Any = Field(..., description="Generated travel itinerary")
    status: str = Field(default="success", description="Status of the request")

# Next, we will create a FastAPI app
from fastapi import FastAPI, HTTPException

fastAPI_app = FastAPI(
    title="Travel Itinerary Generator API",
    description="API for generating travel itineraries based on user interests.",
    version="1.0.0",
)

# Create an endpoint that calls your workflow
@fastAPI_app.post("/generate-itinerary")
async def generate_itinerary(request: ItineraryInput):
    # Prepare input for the workflow
    input_data = {"user_message": request.user_message}
    
    # Call the workflow
    result = app.invoke(input_data)
    
    # Return the result
    return {"itinerary": result}


import nest_asyncio
import asyncio
import uvicorn
import sys

@fastAPI_app.get("/")
async def root():
    """
    Root endpoint that provides basic information about the API.
    """
    return {
        "message": "Welcome to the Travel Itinerary Planning API",
        "version": "1.0.0",
        "endpoints": {
            "/generate-itinerary": "POST endpoint to generate a travel itinerary",
            "/docs": "API documentation"
        }
    }


def start_server():
    config = uvicorn.Config(fastAPI_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # For running directly as a script
    if __name__ == "__main__":
        # Apply nest_asyncio to allow nested event loops
        nest_asyncio.apply()
        
        # Create and run the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the server
        loop.run_until_complete(server.serve())
    else:
        # For running in Jupyter notebooks
        asyncio.create_task(server.serve())
        
    print("Server started at http://localhost:8000")
    print("API documentation available at http://localhost:8000/docs")
    
from mangum import Mangum
handler = Mangum(fastAPI_app)

# Start the server
if __name__ == "__main__":
    print("Starting server...")
    import uvicorn
    uvicorn.run(fastAPI_app, host="0.0.0.0", port=8000, log_level="info")
else:
    # For Jupyter notebook environment
    nest_asyncio.apply()
    start_server()