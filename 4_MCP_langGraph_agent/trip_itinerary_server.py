import os
import json
from typing import Dict, Any
# Import fastMCP - this gives the standard protocol connection
# between the MCP server and the client
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
trip_server = FastMCP("trip-itinerary-server")

# Define paths to data files - ideally you would access your data or something
# and provide these files as environment variables. For now, we will have them
# be hardcoded here.
WEATHER_FILE = os.path.join("..", "data", "weather.json")
ATTRACTIONS_FILE = os.path.join("..", "data", "attractions.json")

# Check if files exist
if not os.path.exists(WEATHER_FILE):
    print(f"Warning: Weather data file not found at {WEATHER_FILE}")
if not os.path.exists(ATTRACTIONS_FILE):
    print(f"Warning: Attractions data file not found at {ATTRACTIONS_FILE}")

# Load data files
try:
    with open(WEATHER_FILE, 'r') as f:
        weather_data = json.load(f)
    print(f"Successfully loaded weather data for {len(weather_data)} cities")
except Exception as e:
    print(f"Error loading weather data: {e}")
    weather_data = {}

try:
    with open(ATTRACTIONS_FILE, 'r') as f:
        attractions_data = json.load(f)
    print(f"Successfully loaded attractions data for {len(attractions_data)} cities")
except Exception as e:
    print(f"Error loading attractions data: {e}")
    attractions_data = {}

# Tool for searching tourist attractions
@trip_server.tool()
def search_tourist_attractions(city: str) -> str:
    """
    Search for tourist attractions in the specified city using a local JSON file.
    
    Args:
        city: The name of the city to search for attractions
        
    Returns:
        A string containing information about tourist attractions in the city
    """
    try:
        # Check if the city exists in the data
        if city.lower() not in attractions_data:
            return f"No information available for tourist attractions in {city}. Try another city."
        
        # Get the attractions for the specified city
        city_attractions = attractions_data[city.lower()]
        
        # Format the attractions information
        attractions = f"Top attractions in {city}:\n"
        for i, attraction in enumerate(city_attractions, 1):
            attractions += f"{i}. {attraction['title']}: {attraction['description'][:150]}...\n"
        
        return attractions
    
    except Exception as e:
        return f"An error occurred while searching for tourist attractions in {city}: {str(e)}"

# Tool for getting weather forecast
@trip_server.tool()
def get_weather_forecast(city: str) -> str:
    """
    Get the current weather forecast for the specified city using a local JSON file.
    
    Args:
        city: The name of the city to get the weather forecast for
        
    Returns:
        A string containing the weather forecast for the city
    """
    try:
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

# Tool for generating an itinerary
@trip_server.tool()
def create_trip_itinerary(city: str, days: int, interests: str = "") -> str:
    """
    Create a detailed trip itinerary based on city, number of days, and optional interests.
    
    Args:
        city: The city to visit
        days: Number of days for the trip
        interests: Optional comma-separated list of interests (e.g., "museums, food, outdoors")
        
    Returns:
        A detailed day-by-day itinerary
    """
    try:
        # Get attractions info
        attractions_info = search_tourist_attractions(city)
        
        # Get weather info
        weather_info = get_weather_forecast(city)
        
        # Generate a basic itinerary structure
        itinerary = f"# {days}-Day Trip Itinerary for {city}\n\n"
        itinerary += f"## Current Weather Information\n{weather_info}\n\n"
        itinerary += f"## Available Attractions\n{attractions_info}\n\n"
        
        # Add interests if provided
        if interests:
            itinerary += f"## Trip Focus: {interests}\n\n"
        
        # Create a day-by-day schedule
        for day in range(1, days + 1):
            itinerary += f"## Day {day}\n\n"
            
            # Morning
            itinerary += "### Morning\n"
            itinerary += "- Breakfast at local café\n"
            itinerary += "- Visit first attraction\n\n"
            
            # Afternoon
            itinerary += "### Afternoon\n"
            itinerary += "- Lunch at recommended restaurant\n"
            itinerary += "- Visit second attraction\n\n"
            
            # Evening
            itinerary += "### Evening\n"
            itinerary += "- Dinner at local restaurant\n"
            itinerary += "- Evening activity or relaxation time\n\n"
        
        # Add final recommendations
        itinerary += "## Additional Recommendations\n\n"
        itinerary += "- Local transportation options\n"
        itinerary += "- Safety tips\n"
        itinerary += "- Recommended local foods to try\n"
        
        return itinerary
    
    except Exception as e:
        return f"An error occurred while creating the itinerary: {str(e)}"

# Define a prompt for creating travel itineraries
@trip_server.prompt()
def create_travel_itinerary() -> str:
    """Prompt for creating comprehensive travel itineraries."""
    return """
    You are an expert travel planner with extensive knowledge about destinations worldwide.
    
    Your task is to create detailed, personalized travel itineraries based on the user's preferences:
    
    1. Ask for the destination city they want to visit.
    2. Ask how many days they'll be staying.
    3. Ask about their interests (museums, food, outdoors, shopping, etc.)
    4. Use the search_tourist_attractions tool to find key attractions.
    5. Use the get_weather_forecast tool to check current weather conditions.
    6. Create a day-by-day itinerary using the create_trip_itinerary tool.
    
    Important guidelines:
    - Consider the current weather when suggesting outdoor activities
    - Provide a balanced mix of popular attractions and hidden gems
    - Include recommendations for local food and dining experiences
    - Add practical information about transportation and logistics
    - Consider the traveler's interests and preferences in your suggestions
    
    Start by greeting the user and asking about their travel destination!
    """

# Expose the data files as resources
@trip_server.resource(uri="file:///data/weather.json", name="Weather Data")
def serve_weather_data():
    try:
        with open(WEATHER_FILE, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading weather data: {str(e)}"

@trip_server.resource(uri="file:///data/attractions.json", name="Attractions Data")
def serve_attractions_data():
    try:
        with open(ATTRACTIONS_FILE, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading attractions data: {str(e)}"

if __name__ == "__main__":
    print("Starting Trip Itinerary MCP Server...")
    print(f"Using weather data from: {WEATHER_FILE}")
    print(f"Using attractions data from: {ATTRACTIONS_FILE}")
    trip_server.run(transport='stdio')