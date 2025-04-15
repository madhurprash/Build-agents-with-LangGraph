import os
import sys
import json
import asyncio
import argparse
from contextlib import AsyncExitStack
from typing import Optional, Dict, List

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

# Import LangChain libraries for ReAct agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_aws import ChatBedrock  # For AWS Bedrock
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.tools import load_mcp_tools

def parse_arguments():
    """Parse command line arguments, falling back to environment variables when available"""
    parser = argparse.ArgumentParser(description='Trip Planner Client')
    
    # Model configuration
    parser.add_argument('--model-id', type=str, 
                        default=os.environ.get('MODEL_ID', 'us.anthropic.claude-3-haiku-20240307-v1:0'),
                        help='Bedrock model ID')
    
    # Python executable path
    parser.add_argument('--python-path', type=str,
                        default=sys.executable,
                        help='Full path to the Python executable')
    
    # Server script path
    parser.add_argument('--server-script', type=str,
                        default=os.environ.get('SERVER_SCRIPT', 'trip_itinerary_server.py'),
                        help='Path to the trip itinerary server script')
    
    args = parser.parse_args()
    return args

class TripPlannerReactClient:
    def __init__(self, args):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Store arguments
        self.args = args
        
        # For storing loaded tools and prompts
        self.tools = None
        self.system_prompt = None
        
        # Print startup information
        print(f"Using Python executable: {args.python_path}")
        print(f"Using model: {args.model_id}")
        print(f"Server script: {args.server_script}")
        
    async def connect_to_server(self):
        """Connect to the trip itinerary MCP server"""
        server_script_path = self.args.server_script
        
        # Determine the correct command based on file extension
        if server_script_path.endswith('.py'):
            # For Python scripts
            server_params = StdioServerParameters(
                command=self.args.python_path,
                args=[server_script_path]
            )
        else:
            raise ValueError("Server script must be a .py file")

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

        # Initialize the MCP server
        await self.session.initialize()
        print(f"Connected to trip itinerary server")
        
        # List available tools
        tools_response = await self.session.list_tools()
        print("\nAvailable tools:")
        for tool in tools_response.tools:
            print(f"- {tool.name}: {tool.description}")
            
        # List available resources
        resources_response = await self.session.list_resources()
        print("\nAvailable resources:")
        for resource in resources_response.resources:
            print(f"- {resource.name}: {resource.uri}")
        
        # Load MCP tools for the ReAct agent
        self.tools = await load_mcp_tools(self.session)
        print(f"Loaded {len(self.tools)} tools for ReAct agent")
        
        # Get system prompt from server or use default
        try:
            prompt_response = await self.session.get_prompt("create_travel_itinerary")
            
            if hasattr(prompt_response, 'messages') and prompt_response.messages:
                self.system_prompt = prompt_response.messages[0].content.text
                print(f"System prompt loaded from server")
            else:
                # Use default prompt if not available from server
                self.system_prompt = """
                IMPORTANT - TOOL USAGE INSTRUCTIONS:
                You MUST use the specific tools provided to you for different parts of the travel planning process. Do not try to create travel plans without using these tools.

                1. Whenever a user mentions a city or asks about attractions, ALWAYS use the search_tourist_attractions tool first.
                Example: search_tourist_attractions(city="London")

                2. Whenever a user asks about weather or when planning outdoor activities, ALWAYS use the get_weather_forecast tool.
                Example: get_weather_forecast(city="Paris")

                3. Whenever a user wants a complete itinerary, ALWAYS use the create_trip_itinerary tool with all relevant parameters.
                Example: create_trip_itinerary(city="Rome", days=3, interests="museums, food")

                Remember to NEVER skip using these tools. They are essential for providing accurate and personalized travel recommendations.

                Process:
                1. When a user asks about travel plans, first identify the city they want to visit.
                2. Use the search_tourist_attractions tool to get information about the city's attractions.
                3. Use the get_weather_forecast tool to check current weather conditions.
                4. Finally, use the create_trip_itinerary tool to generate a complete itinerary.

                Follow this exact process for every travel planning request.
                """
        except Exception as e:
            print(f"Error extracting prompt: {e}")
            # Use default prompt if error occurs
            self.system_prompt = """
            IMPORTANT - TOOL USAGE INSTRUCTIONS:
            You MUST use the specific tools provided to you for different parts of the travel planning process. Do not try to create travel plans without using these tools.

            1. Whenever a user mentions a city or asks about attractions, ALWAYS use the search_tourist_attractions tool first.
            Example: search_tourist_attractions(city="London")

            2. Whenever a user asks about weather or when planning outdoor activities, ALWAYS use the get_weather_forecast tool.
            Example: get_weather_forecast(city="Paris")

            3. Whenever a user wants a complete itinerary, ALWAYS use the create_trip_itinerary tool with all relevant parameters.
            Example: create_trip_itinerary(city="Rome", days=3, interests="museums, food")

            Remember to NEVER skip using these tools. They are essential for providing accurate and personalized travel recommendations.

            Process:
            1. When a user asks about travel plans, first identify the city they want to visit.
            2. Use the search_tourist_attractions tool to get information about the city's attractions.
            3. Use the get_weather_forecast tool to check current weather conditions.
            4. Finally, use the create_trip_itinerary tool to generate a complete itinerary.

            Follow this exact process for every travel planning request.
            """

    async def process_query(self, query: str, conversation_history=None):
        """Process a query using ReAct agent and available tools"""
        if not self.session or not self.tools:
            return "Error: Not connected to server or tools not loaded. Please connect first."
        
        # Initialize conversation history if not provided
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Create a model instance
            model = ChatBedrock(model_id=self.args.model_id)
            
            # Create a ReAct agent with all tools
            agent = create_react_agent(
                model,
                self.tools
            )
            print(f"Initialized the Trip Planner ReAct agent...")
            
            # Format messages including conversation history
            formatted_messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add conversation history
            for message in conversation_history:
                formatted_messages.append(message)
                
            # Add current query
            formatted_messages.append({"role": "user", "content": query})
            
            print(f"Formatted messages prepared")
            
            # Invoke the agent
            response = await agent.ainvoke({"messages": formatted_messages})
            print(f"Raw response: {response}")
            
            # Process the response
            if response and "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    # Save this interaction in the conversation history
                    conversation_history.append({"role": "user", "content": query})
                    conversation_history.append({"role": "assistant", "content": last_message["content"]})
                    return last_message["content"], conversation_history
                else:
                    conversation_history.append({"role": "user", "content": query})
                    conversation_history.append({"role": "assistant", "content": str(last_message.content)})
                    return str(last_message.content), conversation_history
            else:
                return "No valid response received", conversation_history
                
        except Exception as e:
            print(f"Error details: {e}")
            import traceback
            traceback.print_exc()
            return f"Error processing query: {str(e)}", conversation_history

    async def access_resource(self, resource_uri: str) -> str:
        """Access a resource file by URI"""
        if not self.session:
            return "Error: Not connected to server. Please connect first."
            
        result = await self.session.read_resource(resource_uri)
        
        if not result.contents:
            return "No content found"
            
        for content in result.contents:
            if hasattr(content, 'text') and content.text:
                return content.text
                
        return "No text content found"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nTrip Planner Client Started!")
        print("Type your queries or commands, or 'quit' to exit.")
        print("\nExample queries you can try:")
        print("- I'm planning a trip to London for 3 days and I am interesting in Rivers. Plan a trip itinerary and provide the weather too.")

        # Initialize conversation history
        conversation_history = []

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                # Handle special commands
                if query.lower() == 'resources':
                    resources_response = await self.session.list_resources()
                    print("\nAvailable resources:")
                    for resource in resources_response.resources:
                        print(f"- {resource.name}: {resource.uri}")
                    continue

                # Command parsing
                parts = query.split()
                
                if len(parts) >= 3 and parts[0].lower() == 'show' and parts[1].lower() == 'attractions':
                    # Direct tool call for attractions
                    city = ' '.join(parts[2:])
                    result = await self.session.call_tool("search_tourist_attractions", {"city": city})
                    print("\n" + result.content[0].text)
                    
                elif len(parts) >= 3 and parts[0].lower() == 'show' and parts[1].lower() == 'weather':
                    # Direct tool call for weather
                    city = ' '.join(parts[2:])
                    result = await self.session.call_tool("get_weather_forecast", {"city": city})
                    print("\n" + result.content[0].text)
                    
                elif parts[0].lower() == 'resource' and len(parts) >= 2:
                    # Direct resource access
                    uri = parts[1]
                    result = await self.access_resource(uri)
                    print("\n" + result)
                    
                else:
                    # Use the ReAct agent for natural language queries
                    response, conversation_history = await self.process_query(query, conversation_history)
                    print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    # Parse arguments
    args = parse_arguments()
    
    client = TripPlannerReactClient(args)
    try:
        await client.connect_to_server()
        await client.chat_loop()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())