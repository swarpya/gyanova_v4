import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import json
import re
from typing import List, Dict, Any, Union

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
            
            # Extract name if it appears in title or snippet
            name_match = re.search(r'Swaroop (?:Sanjeev )?Ingavale', 
                                  clean_entry["title"] + " " + clean_entry["snippet"], 
                                  re.IGNORECASE)
            if name_match:
                clean_entry["name"] = name_match.group(0)
            
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
        if "name" in entry:
            summary_text += f"NAME: {entry['name']}\n"
        summary_text += f"CONTENT: {entry['snippet']}\n"
        if "date" in entry:
            summary_text += f"DATE: {entry['date']}\n"
        if "additional_info" in entry:
            summary_text += f"INFO: {entry['additional_info']}\n"
        if entry['source']:
            summary_text += f"SOURCE: {entry['source']}\n"
        summary_text += "-" * 60 + "\n"
    
    return summary_text

# Example of how to use with a file
def process_file(json_string):
    
    
    # Clean the data
    cleaned_results = clean_search_data(json_string)
    
    # Generate summary
    summary_text = generate_text_summary(cleaned_results)
    
    # Save outputs
    
    
    return cleaned_results, summary_text

def web_search(query: str):
    """Search web using query string and return results by analyzing them"""
    params = {
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY")
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    cleaned_results, summary_text = process_file(results["organic_results"])
    # print(cleaned_results)
    # print("/n/n",summary_text)
    return cleaned_results



#done
