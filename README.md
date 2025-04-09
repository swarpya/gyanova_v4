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

---

## ✅ Email Tool Setup Instructions

To enable email functionality, you must configure SMTP credentials in a `.env` file.

### 1. Add SMTP settings to `.env`
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 2. How to Get a Gmail App Password
1. Enable 2-Step Verification on your Google account:
   - Go to https://myaccount.google.com/security
   - Under "Signing in to Google", enable **2-Step Verification**

2. Generate an App Password:
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device (or choose "Other")
   - Click **Generate**, and Google will give you a 16-character password
   - Use this password in `.env` as `SMTP_PASSWORD`

---

## Output Example

**User Query:** Send email to pradeepmokashi12@gmail.com with subject "Hello" and body "This is a test email."

**--- Task Breakdown ---**
```
[
  {
    "tool_name": "send_email",
    "parameters": {
      "to": "pradeepmokashi12@gmail.com",
      "subject": "Hello",
      "body": "This is a test email."
    }
  }
]
```

**--- Executing Tasks Sequentially ---**
```
Task 1: Executing send_email with parameters {'to': 'pradeepmokashi12@gmail.com', 'subject': 'Hello', 'body': 'This is a test email.'}
Result: {'status': 'success', 'message': 'Email sent to pradeepmokashi12@gmail.com'}
```

**--- Generating Final Response ---**

**--- Results from Each Tool ---**
```
Task 1: send_email
Parameters: {'to': 'pradeepmokashi12@gmail.com', 'subject': 'Hello', 'body': 'This is a test email.'}
Result: {'status': 'success', 'message': 'Email sent to pradeepmokashi12@gmail.com'}
```

**--- Final Answer ---**

Email successfully sent to pradeepmokashi12@gmail.com with subject "Hello".

