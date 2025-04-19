import os
from groq import Groq
from dotenv import load_dotenv

def code_execution(query: str):
    """
    Send a query to the Groq API and return the response.
    
    Args:
        query (str): The query to send to the Groq API
       
    Returns:
        str: The response content from Groq
    """
    # Load environment variables
    load_dotenv()
    model= os.getenv("advance_tool_model")

    
    # Initialize Groq client
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Make the API call
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        model=model,
    )
    
    # Return just the response content
    return chat_completion.choices[0].message.content

def deep_web_search(query: str):
    """
    The query to search
    """
    # Load environment variables
    load_dotenv()

    model= os.getenv("advance_tool_model")
    # Initialize Groq client
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Make the API call
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        model=model,
    )
    
    # Return just the response content
    return chat_completion.choices[0].message.content
