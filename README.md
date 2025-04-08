# gyanova_v4


# How to Add a New Tool

To add a new function to the agent system, follow these steps:

1. **Create the tool function**:
   - Add a new Python file in the `tools` directory (e.g., `tools/calculator_tool.py`)
   - Define your function with proper documentation

   Example:
   ```python
   # tools/calculator_tool.py
   def calculate(expression: str):
       """Evaluate a mathematical expression and return the result"""
       try:
           # Use a safe eval implementation in production
           return {"result": eval(expression)}
       except Exception as e:
           return {"error": str(e)}
   ```

2. **Import the function in `tools/__init__.py`**:
   ```python
   from .calculator_tool import calculate
   
   __all__ = ['findDateTime', 'web_search', 'calculate']
   ```

3. **Update `core/config.py` to include the new tool in three places**:

   a. Add to `AVAILABLE_TOOLS`:
   ```python
   {
       "name": "calculate",
       "description": "Evaluate a mathematical expression",
       "parameters": {
           "expression": "string - Mathematical expression to evaluate"
       }
   }
   ```

   b. Add to `tools`:
   ```python
   {
       "type": "function",
       "function": {
           "name": "calculate",
           "description": "Evaluate a mathematical expression",
           "parameters": {
               "type": "object",
               "properties": {
                   "expression": {
                       "type": "string",
                       "description": "Mathematical expression to evaluate"
                   }
               },
               "required": ["expression"]
           }
       }
   }
   ```

   c. Add to `available_functions`:
   ```python
   "calculate": calculate
   ```

4. **Import the new function in `core/config.py`**:
   ```python
   from tools import findDateTime, web_search, calculate
   ```

That's it! Your new tool is now integrated into the system and will be available for the AI to use.