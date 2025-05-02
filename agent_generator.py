import os
import re
import json
import argparse
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AgentGenerator:
    def __init__(self):
        """Initialize the Agent Generator with Groq API client"""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
            
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        
        # Define paths to important files
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.tools_dir = os.path.join(self.project_root, "tools")
        self.tools_init = os.path.join(self.tools_dir, "__init__.py")
        self.config_path = os.path.join(self.project_root, "core", "config.py")
        
    def get_file_content(self, file_path):
        """Read and return the content of a file"""
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return f"File not found: {file_path}"
            
    def write_file_content(self, file_path, content):
        """Write content to a file"""
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Updated: {file_path}")
    
    def parse_tool_definition(self, agent_description):
        """Parse LLM response to extract tool information"""
        # Let's extract key components from the description
        patterns = {
            "tool_name": r'tool_name\s*:\s*"([^"]+)"',
            "file_name": r'file_name\s*:\s*"([^"]+)"',
            "function_name": r'function_name\s*:\s*"([^"]+)"',
            "description": r'description\s*:\s*"([^"]+)"',
            "code": r'```python\s*(.*?)```',
            "parameters": r'parameters\s*:\s*(\{.*?\})',
        }
        
        results = {}
        
        for key, pattern in patterns.items():
            if key == "code":
                # Special handling for code block
                matches = re.findall(pattern, agent_description, re.DOTALL)
                if matches:
                    results[key] = matches[0].strip()
            elif key == "parameters":
                # Find JSON parameters
                matches = re.search(pattern, agent_description, re.DOTALL)
                if matches:
                    try:
                        json_text = matches.group(1)
                        # Clean up any leading/trailing spaces or quotes
                        json_text = re.sub(r'^[\s"\']+|[\s"\']+$', '', json_text)
                        results[key] = json.loads(json_text)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse JSON for parameters")
                        results[key] = {}
            else:
                # For other keys, get the first match
                matches = re.search(pattern, agent_description)
                if matches:
                    results[key] = matches.group(1)
        
        # Set defaults for missing values
        if "tool_name" not in results:
            results["tool_name"] = "unknown_tool"
        if "file_name" not in results:
            results["file_name"] = f"{results.get('tool_name', 'unknown')}_tool.py"
        if "function_name" not in results:
            results["function_name"] = results.get("tool_name", "unknown_function")
            
        return results
        
    def generate_agent_definition(self, user_query):
        """Use Groq to generate agent code and configuration based on user query"""
        # Create the prompt for the LLM
        system_prompt = """You are an expert Python developer specializing in creating tools for an AI agent system. 
Your task is to generate a complete tool definition based on the user's natural language query.

The agent system is called "Gyanova" and follows a specific format for adding new tools. You must provide the following:

1. A tool_name: The name of the function that will be called (snake_case)
2. A file_name: The Python file where the tool will be defined (snake_case followed by _tool.py)
3. A function_name: The actual function that implements the tool's functionality (same as tool_name)
4. A detailed description: What the tool does (for documentation purposes)
5. Parameters: A JSON object defining the parameters the tool accepts
6. Complete Python code for implementing the tool

Format your response as follows:

tool_name: "your_tool_name"
file_name: "your_tool_name_tool.py"
function_name: "your_tool_name"
description: "Your detailed description"
parameters: {
  "param1": "string - Description of parameter 1",
  "param2": "string - Description of parameter 2"
}

```python
# Complete Python implementation of the tool
import necessary_modules

def your_tool_name(param1: str, param2: str):
    \"\"\"Detailed docstring describing what the function does\"\"\"
    # Implementation code
    return {"result": "some result"}
```

Please ensure that:
1. The tool follows Python best practices
2. The tool has proper error handling
3. The tool returns results as a dictionary
4. The code is complete and ready to be used
5. The function has type hints for parameters
6. The function includes a detailed docstring
7. The parameters dictionary follows the format shown above

Make sure to include all necessary imports and dependencies. If the tool requires external API access, include comments about any required environment variables."""

        # Query the model
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a tool that can {user_query}"}
            ],
            max_completion_tokens=4096
        )
        
        agent_description = response.choices[0].message.content
        return agent_description
        
    def update_tool_init(self, function_name, file_name_without_ext):
        """Update the tools/__init__.py file to import and export the new tool"""
        init_content = self.get_file_content(self.tools_init)
        
        # Add import statement
        import_pattern = r'# Import all tools to make them accessible from the tools package\n'
        import_statement = f'from .{file_name_without_ext} import {function_name}\n'
        
        if import_statement not in init_content:
            init_content = re.sub(
                import_pattern,
                f'{import_pattern}{import_statement}',
                init_content
            )
        
        # Add to __all__ list
        all_pattern = r"__all__ = \[(.*?)\]"
        all_match = re.search(all_pattern, init_content, re.DOTALL)
        
        if all_match:
            current_all = all_match.group(1)
            # Check if our function is already in __all__
            if f"'{function_name}'" not in current_all:
                # Add it to the end of the list
                new_all = current_all.rstrip() + f", '{function_name}'" if current_all.strip() else f"'{function_name}'"
                init_content = re.sub(all_pattern, f"__all__ = [{new_all}]", init_content, flags=re.DOTALL)
        
        self.write_file_content(self.tools_init, init_content)
        
    def update_config(self, tool_name, description, parameters):
        """Update the core/config.py file to add the new tool"""
        config_content = self.get_file_content(self.config_path)
        
        # Step 1: Add import statement
        import_statement = f"from tools import {tool_name}"
        import_line = "from tools import "
        
        # Check if the import already exists
        if import_statement not in config_content:
            # Find the import line and add our new import
            import_match = re.search(r'from tools import .*', config_content)
            if import_match:
                old_import = import_match.group(0)
                new_import = f"{old_import}, {tool_name}"
                config_content = config_content.replace(old_import, new_import)
        
        # Step 2: Add to AVAILABLE_TOOLS list
        available_tools_pattern = r'AVAILABLE_TOOLS = \[(.*?)\]'
        available_tools_match = re.search(available_tools_pattern, config_content, re.DOTALL)
        
        if available_tools_match:
            tool_json = json.dumps({
                "name": tool_name,
                "description": description,
                "parameters": parameters
            }, indent=4)
            
            # Format the tool entry properly with correct indentation
            tool_entry = f"""    {{
        "name": "{tool_name}",
        "description": "{description}",
        "parameters": {json.dumps(parameters, indent=8).replace('{', '{').replace('}', '}')}
    }}"""
            
            # Add to the end of the list, before the closing bracket
            tools_content = available_tools_match.group(1)
            if f'"name": "{tool_name}"' not in tools_content:
                end_position = available_tools_match.end() - 1  # Position before the closing bracket
                new_tools_content = config_content[:end_position] + ",\n" + tool_entry + "\n" + config_content[end_position:]
                config_content = new_tools_content
        
        # Step 3: Add to tools configuration (for function calling format)
        tools_pattern = r'tools = \[(.*?)\]'
        tools_match = re.search(tools_pattern, config_content, re.DOTALL)
        
        if tools_match:
            tool_params_properties = {}
            tool_params_required = []
            
            for param_name, param_desc in parameters.items():
                # Extract the type from description (usually "string - Description")
                param_type = "string"  # Default type
                if " - " in param_desc:
                    param_type = param_desc.split(" - ")[0].lower()
                
                tool_params_properties[param_name] = {
                    "type": param_type,
                    "description": param_desc.split(" - ")[-1] if " - " in param_desc else param_desc
                }
                tool_params_required.append(param_name)
            
            tool_config = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": tool_params_properties,
                        "required": tool_params_required
                    }
                }
            }
            
            # Format the tool config properly
            tool_config_str = f"""    {{
        "type": "function",
        "function": {{
            "name": "{tool_name}",
            "description": "{description}",
            "parameters": {{
                "type": "object",
                "properties": {{
"""
            
            # Add each property
            for param_name, param_desc in parameters.items():
                param_type = "string"
                if " - " in param_desc:
                    param_type = param_desc.split(" - ")[0].lower()
                param_description = param_desc.split(" - ")[-1] if " - " in param_desc else param_desc
                
                tool_config_str += f"""                    "{param_name}": {{
                        "type": "{param_type}",
                        "description": "{param_description}"
                    }},
"""
            
            # Remove the last comma
            tool_config_str = tool_config_str.rstrip(",\n") + "\n"
            
            # Add required parameters and close the brackets
            tool_config_str += f"""                }},
                "required": {json.dumps(tool_params_required)}
            }}
        }}
    }}"""
            
            # Add to the end of the list, before the closing bracket
            tools_content = tools_match.group(1)
            if f'"name": "{tool_name}"' not in tools_content:
                end_position = tools_match.end() - 1  # Position before the closing bracket
                new_tools_content = config_content[:end_position] + ",\n" + tool_config_str + "\n" + config_content[end_position:]
                config_content = new_tools_content
        
        # Step 4: Add to available_functions mapping
        functions_pattern = r'available_functions = {(.*?)}'
        functions_match = re.search(functions_pattern, config_content, re.DOTALL)
        
        if functions_match:
            functions_entry = f'    "{tool_name}": {tool_name},'
            functions_content = functions_match.group(1)
            
            if f'"{tool_name}":' not in functions_content:
                end_position = functions_match.end() - 1  # Position before the closing bracket
                new_functions_content = config_content[:end_position] + "\n" + functions_entry + "\n" + config_content[end_position:]
                config_content = new_functions_content
        
        self.write_file_content(self.config_path, config_content)
        
    def create_agent(self, user_query):
        """Main function to create a new agent based on user query"""
        print(f"Generating agent for: '{user_query}'")
        
        # Generate agent definition using Groq
        agent_description = self.generate_agent_definition(user_query)
        print("\nAgent description generated:")
        print("-" * 50)
        print(agent_description)
        print("-" * 50)
        
        # Parse the tool definition
        tool_info = self.parse_tool_definition(agent_description)
        
        # Extract important information
        tool_name = tool_info.get("tool_name")
        file_name = tool_info.get("file_name")
        function_name = tool_info.get("function_name", tool_name)
        description = tool_info.get("description", "")
        code = tool_info.get("code", "")
        parameters = tool_info.get("parameters", {})
        
        # Create the Python file for the tool
        file_path = os.path.join(self.tools_dir, file_name)
        self.write_file_content(file_path, code)
        
        # Update the tools/__init__.py file
        file_name_without_ext = os.path.splitext(file_name)[0]
        self.update_tool_init(function_name, file_name_without_ext)
        
        # Update the core/config.py file
        self.update_config(tool_name, description, parameters)
        
        print(f"\nSuccessfully created agent: {tool_name}")
        print(f"- Tool file: {file_path}")
        print(f"- Updated __init__.py to import {function_name}")
        print(f"- Updated config.py to include the new tool")
        print("\nYour new agent is ready to use! 🚀")
        
        return {
            "tool_name": tool_name,
            "file_path": file_path,
            "function_name": function_name,
            "description": description
        }

def main():
    """Command line interface for the Agent Generator"""
    parser = argparse.ArgumentParser(description="Generate a new agent for Gyanova")
    parser.add_argument("query", nargs="+", help="Natural language description of what the agent should do")
    args = parser.parse_args()
    
    # Combine all arguments into a single query
    user_query = " ".join(args.query)
    
    # Create and use the agent generator
    generator = AgentGenerator()
    generator.create_agent(user_query)

if __name__ == "__main__":
    main()