import os
import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def findDateTime(location: str):
    """Returns current date and time at the given city location"""
    try:
        # Initialize geocoder and timezone finder
        geolocator = Nominatim(user_agent=os.getenv("USER_AGENT", "time_app"))
        tf = TimezoneFinder()
        
        # Get coordinates for the location
        location_info = geolocator.geocode(location)
        if not location_info:
            return f"Could not find location: {location}"
        
        # Get timezone string from coordinates
        timezone_str = tf.timezone_at(lng=location_info.longitude, lat=location_info.latitude)
        if not timezone_str:
            return f"Could not determine timezone for: {location}"
        
        # Get current time in that timezone
        timezone = pytz.timezone(timezone_str)
        now = datetime.now(timezone)
        
        # Format result
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        formatted_location = f"{location_info.address}"
        
        return {
            "location": formatted_location,
            "timezone": timezone_str,
            "current_datetime": formatted_time,
            "timestamp": now.timestamp()
        }
    except Exception as e:
        return f"Error finding time for location '{location}': {str(e)}"