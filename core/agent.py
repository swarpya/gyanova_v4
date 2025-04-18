import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from core.config import AVAILABLE_TOOLS, tools, available_functions
import instructor
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Initialize Instructor-enabled Groq client
instructor_client = instructor.from_groq(client)

# Define Pydantic models for structured output
class TaskParameter(BaseModel):
    """Parameters for a specific task"""
    # This is a flexible model that will be dynamically defined based on the tool's requirements

class TaskDependency(BaseModel):
    """Task dependency information"""
    requires: List[int] = Field(description="List of task indices this task depends on")

class Task(BaseModel):
    """A single task in the query breakdown"""
    tool_name: str = Field(description="Name of the tool to use")
    parameters: Dict[str, Any] = Field(description="Parameters for the tool")
    requires: Optional[List[int]] = Field(None, description="List of task indices this task depends on")

class TaskBreakdown(BaseModel):
    """Complete breakdown of a user query into tasks"""
    tasks: List[Task] = Field(description="List of tasks needed to fulfill the query")

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
    
    # Get task breakdown from the model using Instructor to ensure schema compliance
    try:
        task_breakdown = instructor_client.chat.completions.create(
            model=model,
            messages=planning_messages,
            response_model=TaskBreakdown,
            max_completion_tokens=4096
        )
        tasks = task_breakdown.tasks
        print("\n--- Task Breakdown (via Instructor) ---")
        print(json.dumps([task.model_dump() for task in tasks], indent=2))
    except Exception as e:
        print(f"Error using Instructor for task breakdown: {e}. Falling back to regular approach.")
        # Fallback to original approach
        planning_response = client.chat.completions.create(
            model=model, 
            messages=planning_messages,
            max_completion_tokens=4096
        )
        
        # Extract and parse the tasks
        task_breakdown_text = planning_response.choices[0].message.content
        print("\n--- Task Breakdown ---")
        print(task_breakdown_text)
        
        # Try to parse the JSON tasks from the model's response
        try:
            # The model might wrap the JSON in markdown code blocks or add explanations
            # Let's try to extract just the JSON part
            json_match = re.search(r'\[.*\]', task_breakdown_text, re.DOTALL)
            if json_match:
                tasks_data = json.loads(json_match.group(0))
            else:
                # If no array is found, maybe it's a direct JSON object
                json_match = re.search(r'\{.*\}', task_breakdown_text, re.DOTALL)
                if json_match:
                    tasks_data = json.loads(json_match.group(0))
                    if not isinstance(tasks_data, list):
                        tasks_data = [tasks_data]
                else:
                    raise ValueError("No valid JSON found in the response")
                    
            # Convert to TaskBreakdown model
            tasks = []
            for task_data in tasks_data:
                try:
                    task = Task(**task_data)
                    tasks.append(task)
                except Exception as e:
                    print(f"Error validating task: {e}. Skipping invalid task.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse tasks as JSON: {e}. Using a simplified approach.")
            # Fallback: Create a simple web search task based on the query
            tasks = [Task(tool_name="web_search", parameters={"query": user_query})]
    
    # Validate that we only have valid tool names
    valid_tasks = []
    for task in tasks:
        if task.tool_name in available_functions:
            valid_tasks.append(task)
        else:
            print(f"Invalid tool name: {task.tool_name}. Skipping this task.")
    
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
        tool_name = task.tool_name
        parameters = task.parameters.copy()  # Create a copy to modify if needed
        
        # Check if this task requires data from previous tasks
        if task.requires:
            context_data = {}
            for req_idx in task.requires:
                if req_idx < i and req_idx in task_results_by_index:  # Ensure the required task has been processed
                    context_data[f"task_{req_idx+1}_result"] = task_results_by_index[req_idx]
            
            # If we have context data, we need to prepare it for the current task
            if context_data:
                print(f"Task {i+1} requires data from previous tasks: {task.requires}")
                
                # Define a model for the context processing
                class UpdatedParameters(BaseModel):
                    parameters: Dict[str, Any] = Field(description="Updated parameters for the next task")
                
                # Set up model to process the context and update parameters
                context_prompt = [
                    {"role": "system", "content": f"""You are a helpful assistant that processes task results and updates parameters for the next task.

Previous task results: {json.dumps(context_data, indent=2)}

Current task: {json.dumps(task.model_dump(), indent=2)}

IMPORTANT: If this task needs to use text content from a previous task result, extract the FULL TEXT CONTENT from the previous result and use it directly.
DO NOT just refer to "the result from task X" - use the actual content.

For translation tasks: use the full text content as the 'text' parameter.
For email tasks: use the full translated content as the 'body' parameter.

Return only the updated parameters as a JSON object."""}
                ]
                
                try:
                    # Use Instructor to get properly formatted parameters
                    updated_params_obj = instructor_client.chat.completions.create(
                        model=model,
                        messages=context_prompt,
                        response_model=UpdatedParameters,
                        max_completion_tokens=4096
                    )
                    parameters.update(updated_params_obj.parameters)
                    print(f"Updated parameters based on previous task results: {parameters}")
                except Exception as e:
                    print(f"Error using Instructor for parameter updates: {e}. Falling back.")
                    # Fallback to regular approach
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