# Gyanova v4

## Authors
- [Swaroop Ingavale](https://www.linkedin.com/in/swaroop-ingavale-31142619b/)
- [Pradeep Mokashi](https://www.linkedin.com/in/pradeep-mokashi/)

## How to Add a New Tool

To add a new function to the agent system, follow these steps:

### 1. Create the tool function

Add a new Python file in the `tools` directory (e.g., `tools/calculator_tool.py`) and define your function with proper documentation:

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

### 2. Import the function in `tools/__init__.py`

```python
from .calculator_tool import calculate

__all__ = ['findDateTime', 'web_search', 'calculate']
```

### 3. Update `core/config.py` to include the new tool in three places

#### a. Add to `AVAILABLE_TOOLS`:
```python
{
    "name": "calculate",
    "description": "Evaluate a mathematical expression",
    "parameters": {
        "expression": "string - Mathematical expression to evaluate"
    }
}
```

#### b. Add to `tools`:
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

#### c. Add to `available_functions`:
```python
"calculate": calculate
```

### 4. Import the new function in `core/config.py`
```python
from tools import findDateTime, web_search, calculate
```

That's it! Your new tool is now integrated into the system and will be available for the AI to use.

## Output Example

**User Query:** Who is Swaroop Ingavale and what time it is now at Kolhapur?

**--- Task Breakdown ---**
```
[
  {
    "tool_name": "web_search",
    "parameters": {
      "query": "Swaroop Ingavale"
    }
  },
  {
    "tool_name": "findDateTime",
    "parameters": {
      "location": "Kolhapur"
    }
  }
]
```

**--- Executing Tasks Sequentially ---**
```
Task 1: Executing web_search with parameters {'query': 'Swaroop Ingavale'}
Result: [{'position': 1, 'title': 'Swaroop Ingavale - Program Tutor - Georgian College', 'link': 'https://ca...
Task 2: Executing findDateTime with parameters {'location': 'Kolhapur'}
Result: {'location': 'Kolhapur, Karvir, Kolhapur, Maharashtra, 416003, India', 'timezone': 'Asia/Kolkata', '...
```

**--- Generating Final Response ---**

**--- Results from Each Tool ---**
```
Task 1: web_search
Parameters: {'query': 'Swaroop Ingavale'}
Result: [{'position': 1, 'title': 'Swaroop Ingavale - Program Tutor - Georgian College', 'link': 'https://ca.linkedin.com/in/swaroop-ingavale-31142619b', 'red...
Task 2: findDateTime
Parameters: {'location': 'Kolhapur'}
Result: {'location': 'Kolhapur, Karvir, Kolhapur, Maharashtra, 416003, India', 'timezone': 'Asia/Kolkata', 'current_datetime': '2025-04-08 23:11:41', 'timesta...
```

**--- Final Answer ---**

Swaroop Ingavale is an AI graduate student from Georgian College, and he has built a tool that uses deep reinforcement learning. He is also a Program Tutor at Georgian College.
The current time at Kolhapur is 2025-04-08 23:11:41.