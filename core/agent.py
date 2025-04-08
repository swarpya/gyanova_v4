import json
import re
from groq import Groq
import os
from dotenv import load_dotenv
from core.config import AVAILABLE_TOOLS, tools, available_functions

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def process_user_query(user_query):
    # Step 1: Ask the model to analyze the query and break it down into subtasks
    # Provide the exact list of available tools to prevent hallucination
    tools_description = json.dumps(AVAILABLE_TOOLS, indent=2)
    
    planning_messages = [
        {"role": "system", "content": f"""You are a helpful assistant that breaks down complex queries into separate tasks. 
        
These are the ONLY tools available to you:
{tools_description}

For each task, you MUST specify a tool_name that EXACTLY matches one of the available tool names listed above.
Format your response as a JSON array of task objects, where each task has 'tool_name' and 'parameters' fields.
The tool_name MUST be one of the exact tool names provided.
DO NOT invent or hallucinate tool names that aren't in the list."""},
        {"role": "user", "content": f"Break down this query into separate subtasks: '{user_query}'"}
    ]
    
    # Get task breakdown from the model
    planning_response = client.chat.completions.create(
        model=model, 
        messages=planning_messages,
        max_completion_tokens=4096
    )
    
    # Extract and parse the tasks
    task_breakdown = planning_response.choices[0].message.content
    print("\n--- Task Breakdown ---")
    print(task_breakdown)
    
    # Try to parse the JSON tasks from the model's response
    try:
        # The model might wrap the JSON in markdown code blocks or add explanations
        # Let's try to extract just the JSON part
        json_match = re.search(r'\[.*\]', task_breakdown, re.DOTALL)
        if json_match:
            tasks = json.loads(json_match.group(0))
        else:
            # If no array is found, maybe it's a direct JSON object
            json_match = re.search(r'\{.*\}', task_breakdown, re.DOTALL)
            if json_match:
                tasks = json.loads(json_match.group(0))
                if not isinstance(tasks, list):
                    tasks = [tasks]
            else:
                raise ValueError("No valid JSON found in the response")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Failed to parse tasks as JSON: {e}. Using a simplified approach.")
        # Fallback: Create a simple web search task based on the query
        tasks = [{"tool_name": "web_search", "parameters": {"query": user_query}}]
    
    # Validate that we only have valid tool names
    valid_tasks = []
    for task in tasks:
        if task["tool_name"] in available_functions:
            valid_tasks.append(task)
        else:
            print(f"Invalid tool name: {task['tool_name']}. Skipping this task.")
    
    tasks = valid_tasks
    
    # Initialize conversation for the final response
    messages = [
        {"role": "system", "content": "You are a helpful assistant that responds to user queries by sequentially executing appropriate tools and providing a comprehensive final answer."},
        {"role": "user", "content": user_query}
    ]
    
    # Step 2: Execute each task sequentially and collect results
    print("\n--- Executing Tasks Sequentially ---")
    all_results = []
    
    for i, task in enumerate(tasks):
        tool_name = task["tool_name"]
        parameters = task["parameters"]
        
        print(f"Task {i+1}: Executing {tool_name} with parameters {parameters}")
        
        # Execute the tool function
        function_to_call = available_functions[tool_name]
        tool_result = function_to_call(**parameters)
        
        # Add the structured result to our collection
        task_result = {
            "task_number": i+1,
            "tool_name": tool_name,
            "parameters": parameters,
            "result": tool_result
        }
        all_results.append(task_result)
        
        # Add this as a tool message to the conversation
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": f"call_{i+1}",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(parameters)
                }
            }]
        })
        
        messages.append({
            "role": "tool",
            "content": str(tool_result),
            "tool_call_id": f"call_{i+1}"
        })
        
        print(f"Result: {str(tool_result)[:100]}..." if len(str(tool_result)) > 100 else tool_result)
    
    # Step 3: Generate the final comprehensive response
    print("\n--- Generating Final Response ---")
    final_response = client.chat.completions.create(
        model=model, 
        messages=messages,
        max_completion_tokens=4096
    )
    
    final_answer = final_response.choices[0].message.content
    return all_results, final_answer