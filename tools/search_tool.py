import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def web_search(query: str):
    """Search web using query string and return results by analyzing them"""
    params = {
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY")
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    return results["organic_results"]
#done