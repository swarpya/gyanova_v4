import os
import json
import re
from typing import List, Dict, Any, Union, Tuple
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_search_data(data: Union[List[Dict[str, Any]], str]) -> List[Dict[str, Any]]:
    """
    Clean search data to extract only natural language content.
    Removes links, displayed links, favicons, and other technical data.
    
    Args:
        data: Either a JSON string or a list of result dictionaries (organic_results)
        
    Returns:
        List of cleaned entries with only natural language content
    """
    try:
        # Handle string input (convert to list)
        if isinstance(data, str):
            data = json.loads(data)
        
        # List to store cleaned entries
        cleaned_data = []
        
        for entry in data:
            # Extract only the natural language fields
            clean_entry = {
                "title": entry.get("title", "").strip(),
                "snippet": entry.get("snippet", "").strip(),
                "source": entry.get("source", "").strip() if "source" in entry else ""
            }
            
            # Add date if available
            if "date" in entry:
                clean_entry["date"] = entry.get("date", "")
            
            # Extract highlighted content (usually important information)
            if "snippet_highlighted_words" in entry:
                clean_entry["highlighted"] = ", ".join(entry.get("snippet_highlighted_words", []))
            
            # Keep rich snippets if they contain useful information
            if "rich_snippet" in entry and "top" in entry["rich_snippet"]:
                if "extensions" in entry["rich_snippet"]["top"]:
                    clean_entry["additional_info"] = ", ".join(entry["rich_snippet"]["top"]["extensions"])
            
            cleaned_data.append(clean_entry)
        
        return cleaned_data
    
    except json.JSONDecodeError:
        return [{"error": "Invalid JSON input"}]
    except Exception as e:
        return [{"error": str(e)}]

def generate_text_summary(cleaned_data: List[Dict[str, Any]]) -> str:
    """Generate a plain text summary from cleaned data"""
    summary_text = ""
    for entry in cleaned_data:
        if "error" in entry:
            return f"ERROR: {entry['error']}"
            
        summary_text += f"TITLE: {entry['title']}\n"
        summary_text += f"CONTENT: {entry['snippet']}\n"
        if "date" in entry:
            summary_text += f"DATE: {entry['date']}\n"
        if "highlighted" in entry:
            summary_text += f"HIGHLIGHTED: {entry['highlighted']}\n"
        if "additional_info" in entry:
            summary_text += f"INFO: {entry['additional_info']}\n"
        if entry['source']:
            summary_text += f"SOURCE: {entry['source']}\n"
        summary_text += "-" * 60 + "\n"
    
    return summary_text

def process_results(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Process search results to get cleaned data and summary
    
    Args:
        data: Raw search results (organic_results)
    
    Returns:
        Tuple containing cleaned results and text summary
    """
    # Clean the data
    cleaned_results = clean_search_data(data)
    # print(cleaned_results)
    
    # Generate summary
    summary_text = generate_text_summary(cleaned_results)
    
    return cleaned_results, summary_text

def web_search(query: str) -> Dict[str, Any]:
    """
    Search web using query string and return cleaned results
    
    Args:
        query: The search query
        **kwargs: Additional parameters to pass to SerpAPI
    
    Returns:
        Dictionary with search results and metadata
    """
    # Set up search parameters
    params = {
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY"),

    }
    
    # Execute search
    search = GoogleSearch(params)
    results = search.get_dict()
    
    # Process results if available
    if "organic_results" in results:
        cleaned_results, summary = process_results(results["organic_results"])
        
        return {
            # "query": query,
            # "cleaned_results": cleaned_results,
            "summary": summary,
            # "result_count": len(cleaned_results)
        }
    else:
        return {
            "query": query,
            "error": "No organic results found",
            "result_count": 0
        }

# Example usage
if __name__ == "__main__":
    # Get search results
    search_data = web_search("who is swaroop ingavale")
    
    # Print summary
    print(f"Search query: {search_data['query']}")
    print(f"Found {search_data['result_count']} results")
    
    if "error" in search_data:
        print(f"Error: {search_data['error']}")
    else:
        print("\nSUMMARY:")
        # print(search_data["summary"])
        