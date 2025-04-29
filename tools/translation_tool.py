# tools/translate_tool.py
import requests
import time
import random
#done
def translate_text(to: str = None, text: str = None, target_language: str = None, source_language: str = "auto", **kwargs):
    """
    Translate text using Google Translate's unofficial API.
    
    Args:
        text (str): Text to translate
        target_language (str): Language code to translate to
        source_language (str, optional): Language code to translate from. Defaults to "auto".
        **kwargs: Additional parameters that might be passed
    
    Returns:
        dict: Translation result containing translated text and detected source language
    """
    try:
        # Handle nested parameters if present
        if 'parameters' in kwargs and isinstance(kwargs['parameters'], dict):
            params = kwargs['parameters']
            text = params.get('text', text)
            target_language = params.get('target_language', target_language)
            source_language = params.get('source_language', source_language)
        
        # Use 'to' as target_language if provided (for compatibility with different parameter naming)
        if not target_language and to:
            target_language = to
            
        # Validate required parameters
        if not text:
            return {"status": "error", "message": "No text provided for translation"}
        if not target_language:
            return {"status": "error", "message": "No target language provided"}
            
        # Add a small random delay to avoid rate limiting
        time.sleep(random.uniform(0.1, 0.5))
        
        # Google Translate URL
        url = "https://translate.googleapis.com/translate_a/single"
        
        # Parameters
        params = {
            "client": "gtx",
            "sl": source_language,
            "tl": target_language,
            "dt": "t",
            "q": text
        }
        
        # Add multiple user agents to rotate between them
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # Make request
        response = requests.get(url, params=params, headers=headers)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse response
            result = response.json()
            
            # Extract translated text
            translated_text = ""
            for sentence in result[0]:
                if sentence[0]:
                    translated_text += sentence[0]
            
            # Get detected language if source was auto
            detected_language = source_language
            if source_language == "auto" and len(result) > 2:
                detected_language = result[2]
            
            return {
                "status": "success",
                "translated_text": translated_text,
                "source_language": detected_language,
                "target_language": target_language
            }
        else:
            # Handle error
            # Try a backup method
            return backup_translate(text, target_language, source_language)
            
    except Exception as e:
        # If primary method fails, try backup
        try:
            return backup_translate(text, target_language, source_language)
        except Exception as backup_error:
            return {
                "status": "error",
                "message": f"Both translation methods failed. Primary error: {str(e)}, Backup error: {str(backup_error)}"
            }

def backup_translate(text, target_language, source_language="auto"):
    """Backup translation method using a different Google Translate endpoint"""
    try:
        # Alternative Google Translate endpoint
        url = "https://clients5.google.com/translate_a/t"
        
        params = {
            "client": "dict-chrome-ex",
            "sl": source_language,
            "tl": target_language,
            "q": text
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            # This endpoint returns a different format
            result = response.json()
            
            # Extract translated text based on response structure
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], str):
                    translated_text = result[0]
                elif isinstance(result[0], list) and len(result[0]) > 0:
                    translated_text = result[0][0]
                else:
                    translated_text = str(result)
            else:
                translated_text = str(result)
            
            return {
                "status": "success",
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language
            }
        else:
            return {
                "status": "error",
                "message": f"Backup translation API returned status code {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Backup translation failed: {str(e)}"
        }