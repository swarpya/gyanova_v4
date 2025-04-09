import os
import requests
from typing import Dict, Any, Union
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

# Load environment variables
load_dotenv()

def get_weather(location: str) -> Union[Dict[str, Any], str]:
    """
    Returns current weather information for the given location
    
    Args:
        location (str): Name of the city or location
        
    Returns:
        dict: Dictionary containing weather information
              or error message as string if unsuccessful
    """
    try:
        # Initialize geocoder with user agent from environment variable or default
        user_agent = os.getenv("GEOLOCATION_USER_AGENT", "weather_tool")
        geolocator = Nominatim(user_agent=user_agent)
        
        # Get API key from environment variables (required)
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            raise ValueError("WEATHER_API_KEY not set in .env file")
        
        # Get geographic coordinates for the location
        location_info = geolocator.geocode(location)
        if not location_info:
            return f"Location not found: {location}"
        
        # Extract coordinates
        lat = location_info.latitude
        lon = location_info.longitude
        
        # Make API request to OpenWeatherMap
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(weather_url)
        
        if response.status_code != 200:
            return f"Weather API error: {response.status_code} - {response.text}"
        
        # Parse the weather data
        weather_data = response.json()
        
        # Format the response
        result = {
            "location": location_info.address,
            "coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "weather": {
                "condition": weather_data["weather"][0]["main"],
                "description": weather_data["weather"][0]["description"],
                "temperature": {
                    "current": weather_data["main"]["temp"],
                    "feels_like": weather_data["main"]["feels_like"],
                    "min": weather_data["main"]["temp_min"],
                    "max": weather_data["main"]["temp_max"]
                },
                "humidity": weather_data["main"]["humidity"],
                "wind": {
                    "speed": weather_data["wind"]["speed"],
                    "degrees": weather_data["wind"].get("deg", "N/A")
                },
                "pressure": weather_data["main"]["pressure"],
                "visibility": weather_data.get("visibility", "N/A")
            },
            "timestamp": weather_data["dt"],
            "sunrise": weather_data["sys"]["sunrise"],
            "sunset": weather_data["sys"]["sunset"]
        }
        
        return result
    
    except Exception as e:
        return f"Error getting weather for '{location}': {str(e)}"
