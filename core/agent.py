import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from core.config import AVAILABLE_TOOLS, tools, available_functions

# Load environment variables
load_dotenv()
#done
# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

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

IMPORTANT: If a task needs data from previous tasks, include a "requires" field with a list of task indices it depends on.
Example: 
[
  {{"tool_name": "get_weather", "parameters": {{"location": "Toronto"}}}},
  {{"tool_name": "send_email", "parameters": {{"to": "example@example.com", "subject": "Weather Report"}}, "requires": [0]}}
]

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
    task_results_by_index = {}  # Store results by task index for context sharing
    
    for i, task in enumerate(tasks):
        tool_name = task["tool_name"]
        parameters = task["parameters"].copy()  # Create a copy to modify if needed
        
        # Check if this task requires data from previous tasks
        if "requires" in task:
            context_data = {}
            for req_idx in task["requires"]:
                if req_idx < i and req_idx in task_results_by_index:  # Ensure the required task has been processed
                    context_data[f"task_{req_idx+1}_result"] = task_results_by_index[req_idx]
            
            # If we have context data, we need to prepare it for the current task
            if context_data:
                print(f"Task {i+1} requires data from previous tasks: {task['requires']}")
                
                # Set up model to process the context and update parameters
                context_prompt = [
    {"role": "system", "content": f"""You are a helpful assistant that processes task results and updates parameters for the next task.

Previous task results: {json.dumps(context_data, indent=2)}

Current task: {json.dumps(task, indent=2)}

IMPORTANT: If this task needs to use text content from a previous task result, extract the FULL TEXT CONTENT from the previous result and use it directly.
DO NOT just refer to "the result from task X" - use the actual content.

For translation tasks: use the full text content as the 'text' parameter.
For email tasks: use the full translated content as the 'body' parameter.

Return only a JSON object with the updated parameters. Do not include any explanations."""},
]
                
                context_response = client.chat.completions.create(
                    model=model,
                    messages=context_prompt,
                    max_completion_tokens=4096
                )
                
                try:
                    updated_params_text = context_response.choices[0].message.content
                    # Extract JSON from the response
                    json_match = re.search(r'\{.*\}', updated_params_text, re.DOTALL)
                    if json_match:
                        updated_params = json.loads(json_match.group(0))
                        parameters.update(updated_params)
                        print(f"Updated parameters based on previous task results: {parameters}")
                    else:
                        # If no JSON is found, try to use the context directly
                        parameters["context"] = context_data
                        print("Added raw context data to parameters")
                except Exception as e:
                    print(f"Error updating parameters with context: {str(e)}")
                    # Fallback: Add context as a separate parameter
                    parameters["context"] = context_data
        
        print(f"Task {i+1}: Executing {tool_name} with parameters {parameters}")
        
        # Execute the tool function
        function_to_call = available_functions[tool_name]
        tool_result = function_to_call(**parameters)
        
        # Store the result for potential future use
        task_results_by_index[i] = tool_result
        
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