from tools import findDateTime, web_search, get_weather, send_email

# Define the tools with their exact names for reference
# This list is what will be presented to the LLM so it knows what tools are available
AVAILABLE_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "query": "string - The search query"
        }
    },
    {
        "name": "findDateTime",
        "description": "This function returns the current date",
        "parameters": {
            "location": "string - The Location required for determining date and time"
        }
    },
    {
        "name": "get_weather",
        "description": "This function returns the current weather information",
        "parameters": {
            "location": "string - The Location required for determining weather"
        }
    },
    {
    "name": "send_email",
    "description": "Send an email with subject and body",
    "parameters": {
        "to": "string - Email address of the recipient",
        "subject": "string - Subject of the email",
        "body": "string - Body content of the email"
    }
},
]

# Define the tools configuration for the Groq model
# This structure follows the OpenAI-compatible function calling format
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "findDateTime",
            "description": "This function returns the current date",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The Location required for determining date and time",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "This function returns the current weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The Location required for determining weather",
                    }
                },
                "required": ["location"],
            },
        },
    },
   {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Send an email with subject and body",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Email address of the recipient"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject of the email"
                },
                "body": {
                    "type": "string",
                    "description": "Body content of the email"
                }
            },
            "required": ["to", "subject", "body"]
        }
    }
},
]

# Available functions mapping - connects function names to actual Python functions
available_functions = {
    "web_search": web_search,
    "findDateTime": findDateTime,
    "get_weather": get_weather,
    "send_email": send_email,
}