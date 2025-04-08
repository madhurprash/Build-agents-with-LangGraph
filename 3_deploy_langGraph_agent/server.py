import json
import logging
import os

# Set up logging immediately
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store initialized resources
global_app = None
global_bedrock_client = None
global_fastapi_app = None

# Import FastAPI-related modules at the top
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from mangum import Mangum

# Create pydantic model for the input
class ItineraryInput(BaseModel):
    """
    Request the agent for itinerary generation
    """
    user_message: str = Field(
        ...,
        description="The user's message containing their interests and preferences for the itinerary."
    )

# Create FastAPI app at the top level
fastAPI_app = FastAPI(
    title="Travel Itinerary Generator API",
    description="API for generating travel itineraries based on user interests.",
    version="1.0.0",
)

def initialize_resources():
    """
    Lazy initialization of expensive resources.
    Only called when needed, not during cold start.
    """
    global global_app, global_bedrock_client
    
    # Check if already initialized
    if global_app is not None:
        return global_app
    
    logger.info("Initializing resources...")
    
    import boto3
    from typing import TypedDict, Annotated, List, Optional
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_aws import ChatBedrockConverse
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import tool
    
    # Define PlannerState class for StateGraph
    class PlannerState(TypedDict):
        messages: Annotated[List[HumanMessage | AIMessage], "The messages in the conversation"]
        itinerary: Optional[str]
        city: str
        user_message: str
        weather_info: Optional[str]
        attractions_info: Optional[str]
    
    # Initialize bedrock client
    global_bedrock_client = boto3.client("bedrock-runtime")
    
    # Create the llm
    llm = ChatBedrockConverse(
        model="us.amazon.nova-lite-v1:0",
        provider='amazon', 
        temperature=0.1, 
        max_tokens=512,
        client=global_bedrock_client,
    )
    
    # Define tool functions
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
            file_path = os.path.join("data", "attractions.json")
            if not os.path.exists(file_path):
                return f"Error: Attractions data file not found. Please make sure '{file_path}' exists."
            
            with open(file_path, 'r') as f:
                attractions_data = json.load(f)
            
            if city.lower() not in attractions_data:
                return f"No information available for tourist attractions in {city}. Try another city."
            
            city_attractions = attractions_data[city.lower()]
            
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
            file_path = os.path.join("data", "weather.json")
            if not os.path.exists(file_path):
                return f"Error: Weather data file not found. Please make sure '{file_path}' exists."
            
            with open(file_path, 'r') as f:
                weather_data = json.load(f)
            
            if city.lower() not in weather_data:
                return f"No weather information available for {city}. Try another city."
            
            city_weather = weather_data[city.lower()]
            location = city_weather["location"]
            current = city_weather["current"]
            
            forecast = f"Current weather in {location['name']}, {location['country']}:\n"
            forecast += f"Temperature: {current['temperature']}°C\n"
            # Shortened for brevity
            
            return forecast
        except Exception as e:
            return f"An error occurred while getting the weather forecast for {city}: {str(e)}"
    
    tools = [mock_search_tourist_attractions, mock_get_weather_forecast]
    
    # Create the ReAct agent
    get_realtime_info_react_llm = create_react_agent(llm, tools=tools)
    
    # Define workflow nodes
    def input_interest(state: PlannerState) -> PlannerState:
        if not state.get('messages'): 
            state['messages'] = []
        return {**state}

    def create_itinerary(state: PlannerState) -> PlannerState:
        try:
            messages = [HumanMessage(content=state['user_message'])]
            agent_input = {"messages": messages}
            result = get_realtime_info_react_llm.invoke(agent_input)
            
            if isinstance(result, dict) and "output" in result:
                itinerary = result["output"]
            else:
                itinerary = str(result)
            
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
            error_message = f"Error creating itinerary: {str(e)}"
            
            return {
                **state,
                'messages': [
                    *state['messages'],
                    HumanMessage(content=state['user_message']),
                    AIMessage(content=error_message)
                ],
                'itinerary': error_message
            }
    
    # Create and compile workflow
    workflow = StateGraph(PlannerState)
    workflow.add_node("input_user_interests", input_interest)
    workflow.add_node("create_itinerary", create_itinerary)
    workflow.set_entry_point("input_user_interests")
    workflow.add_edge("input_user_interests", "create_itinerary")
    workflow.add_edge("create_itinerary", END)
    
    global_app = workflow.compile()
    logger.info("Resources initialized successfully")
    
    return global_app

# Define the FastAPI endpoint
@fastAPI_app.post("/generate-itinerary")
async def generate_itinerary(request: dict):
    # Extract user message from either user_message or question field
    user_message = request.get('user_message', '')
    if not user_message and 'question' in request:
        user_message = request.get('question', '')
    
    logger.info(f"Received request with message: {user_message}")
    app = initialize_resources()
    input_data = {"user_message": user_message}
    result = app.invoke(input_data)
    
    # Find the AI message with the final response
    ai_message_content = ""
    if "messages" in result and len(result["messages"]) > 0:
        # Look for the last AI message in the list
        for msg in reversed(result["messages"]):
            # Check if it's an AI message
            if hasattr(msg, "type") and msg.type == "ai":
                ai_message_content = msg.content
                break
            elif isinstance(msg, dict) and msg.get("type") == "ai":
                ai_message_content = msg.get("content", "")
                break
            # Special case for AIMessage objects
            elif hasattr(msg, "__class__") and msg.__class__.__name__ == "AIMessage":
                ai_message_content = msg.content
                break
    
    # If we didn't find an AI message, look for the itinerary field
    if not ai_message_content and "itinerary" in result:
        # The itinerary might be a string or an object
        if isinstance(result["itinerary"], str):
            ai_message_content = result["itinerary"]
        else:
            # Try to extract a human-readable version
            ai_message_content = str(result["itinerary"])
    
    # Extract just the final response text if the content contains thinking/tool use
    if isinstance(ai_message_content, list):
        # Sometimes AI content is a list of content parts
        for part in ai_message_content:
            if isinstance(part, dict) and part.get("type") == "text":
                # The last text part is usually the final response
                final_text = part.get("text", "")
                # Remove thinking sections if present
                final_text = final_text.split("<thinking>")[-1].split("</thinking>")[-1].strip()
                ai_message_content = final_text
    
    # If it's still not a clean string, do some final cleanup
    if not isinstance(ai_message_content, str):
        ai_message_content = str(ai_message_content)
    
    # Remove any thinking sections that might be in the string
    if "<thinking>" in ai_message_content:
        # Extract only the content after the last thinking section
        parts = ai_message_content.split("</thinking>")
        if len(parts) > 1:
            ai_message_content = parts[-1].strip()
    
    # Create the response format expected by Streamlit
    return {
        "result": [
            {"role": "user", "content": user_message},
            {"role": "ai", "content": ai_message_content.strip()}
        ]
    }

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

# Lambda Handler
def handler(event, context):
    """
    Lambda handler for AWS Lambda deployment using Mangum
    """
    logger.info("Lambda handler called with event type: %s", type(event))
    
    # Create Mangum handler
    mangum_handler = Mangum(
        fastAPI_app,
        lifespan="auto",
        api_gateway_base_path="/prod",
        text_mime_types=["application/json"],
    )
    
    # Use Mangum to handle the event
    return mangum_handler(event, context)