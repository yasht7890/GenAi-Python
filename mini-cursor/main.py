from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import json
import requests
import os
import subprocess


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def open_file(file_path: str):
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error opening file: {str(e)}"
    

def update_file(params: dict):
    try:
        file_path = params['file']
        content = params['content']
        with open(file_path, 'w') as f:
            f.write(content)
        return f"File {file_path} updated successfully"
    except Exception as e:
        return f"Error updating file: {str(e)}"
    
def write_file(data):
    try:
        if isinstance(data, dict):
            path = data.get("path")
            content = data.get("content")
            if not path or not content:
                return "Invalid input: 'path' and 'content' are required."
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File written: {path}"
        else:
            return "Input must be a dictionary with 'path' and 'content'."
    except Exception as e:
        return f"Error writing file: {e}"


def use_node(cmd: str):
    try:
        
        result = subprocess.run(cmd, shell=True, check=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout  # Return only the standard output
    except subprocess.CalledProcessError as e:
        return f"Error:\n{e.stderr}"

def run_command(cmd: str):
    result = os.system(cmd)
    return result

def open_in_new_terminal(cmd: str):
    try:
        # Launch in a new command prompt window
        subprocess.Popen(f'start cmd /k "{cmd}"', shell=True)
        return f"Launched new terminal with: {cmd}"
    except Exception as e:
        return f"Error launching new terminal: {e}"



available_tools = {
    "run_command": run_command,
    "use_node": use_node,
    "update_file":update_file,
    "open_file":open_file,
    "write_file":write_file,
    "open_in_new_terminal":open_in_new_terminal
}

SYSTEM_PROMPT = f"""
You are a helpful AI assistant who builds projects based on user requirements.
remember You are on windows laptop use commands of a windows laptop
You operate in four modes: plan, action, observe, output.

Your workflow:
1. Plan how to achieve the user’s request.
2. Execute actions using available tools, one at a time.
3. Observe the output from tools.
4. Continue until the project is created and ready.

You are allowed to:
- Run shell commands (e.g. mkdir, npm, git)
- Use Node.js commands (npm install, vite, etc.)
- Read/write files to inject code or modify templates
- Install and configure frameworks like Tailwind, React Router, etc.

Available Tools:
- "run_command": Execute Linux shell commands
- "use_node": Run Node.js-related shell commands (e.g. npm install)
- "open_file": Read a file
- "write_file": Write or create a file
- "update_file": Modify an existing file
- "open_in_new_terminal" : open a new terminal to run projects

Example Query: Create a React project with a home page and contact form

Assistant response sequence:

1. Plan:
{{
  "step": "plan",
  "content": "Create folder, initialize Vite React app, install dependencies, add homepage and contact form components."
}}

2. Actions:
{{
  "step": "action",
  "function": "run_command",
  "input": "mkdir my-react-app"
}}

{{
  "step": "action",
  "function": "use_node",
  "input": "cd my-react-app && npm create vite@latest . -- --template react"
}}

{{
  "step": "action",
  "function": "use_node",
  "input": "cd my-react-app && npm install"
}}

{{
  "step": "action",
  "function": "write_file",
  "input": {{
    "path": "my-react-app/src/pages/Home.jsx",
    "content": "<h1>Welcome to the Home Page</h1>"
  }}
}}

{{
  "step": "action",
  "function": "write_file",
  "input": {{
    "path": "my-react-app/src/pages/Contact.jsx",
    "content": "<form><input placeholder='Your Name' /></form>"
  }}
}}

3. Final Output:
{{
  "step": "output",
  "content": "React project created with Home and Contact pages. What do you want to do next"
}}



Example Query: Create a full stack project with react and a home page and contact form

Assistant response sequence:

1. Plan:
{{
  "step": "plan",
  "content": "User asked to create a full stack project, i will make two different folders one for frontend and one for backend."
}}

2. Actions:
{{
  "step": "action",
  "function": "run_command",
  "input": "mkdir my-fullstack-app"
}}
{{
  "step": "action",
  "function": "run_command",
  "input": "cd my-fullstack-app"
}}
{{
  "step": "action",
  "function": "run_command",
  "input": "mkdir frontend backend"
}}
{{
  "step": "action",
  "function": "run_command",
  "input": "cd backend"
}}
{{
  "step": "action",
  "function": "run_command",
  "input": "mkdir controllers middlewares model routes utils "
}}
{{
  "step": "action",
  "function": "run_command",
  "input": " echo. > index.js "
}}
{{
  "step": "action",
  "function": "use_node",
  "input": " npm init -y "
}}
{{
  "step": "action",
  "function": "use_node",
  "input": " npm i express mongoose dotenv  "
}}
{{
  "step": "action",
  "function": "run_command",
  "input": " cd .. "
}}

{{
  "step": "action",
  "function": "use_node",
  "input": "cd frontend && npm create vite@latest . -- --template react"
}}

{{
  "step": "action",
  "function": "use_node",
  "input": "cd my-react-app && npm install"
}}

{{
  "step": "action",
  "function": "write_file",
  "input": {{
    "path": "my-react-app/src/pages/Home.jsx",
    "content": "<h1>Welcome to the Home Page</h1>"
  }}
}}

{{
  "step": "action",
  "function": "write_file",
  "input": {{
    "path": "my-react-app/src/pages/Contact.jsx",
    "content": "<form><input placeholder='Your Name' /></form>"
  }}
}}

3. Final Output:
{{
  "step": "output",
  "content": "React project created with Home and Contact pages. What do you want to do next"
}}



Example Query: open my project in browser
Assistant response sequence:

1. Plan:
{{
  "step": "plan",
  "content": "User asked to open the project. I will launch the frontend dev server in a new terminal window."
}}

2. Actions:
{{
  "step": "action",
  "function": "open_in_new_terminal",
  "input": "cd my-fullstack-app\\frontend && npm run dev"
}}



Rules:
- Perform one step at a time
- Wait for observation before next action
- Format every reply in valid JSON
"""


messages = [
  { "role": "system", "content": SYSTEM_PROMPT }
]

while True:
    query = input("> ")
    messages.append({ "role": "user", "content": query })

    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=messages
        )

        messages.append({ "role": "assistant", "content": response.choices[0].message.content })
        parsed_response = json.loads(response.choices[0].message.content)

        if parsed_response.get("step") == "plan":
            continue

        if parsed_response.get("step") == "action":
            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")

            print(f"🛠️: Calling Tool:{tool_name} with input {tool_input}")

            if available_tools.get(tool_name) != False:
                output = available_tools[tool_name](tool_input)
                messages.append({ "role": "user", "content": json.dumps({ "step": "observe", "output": output }) })
                continue
        
        if parsed_response.get("step") == "output":
            print(f"🤖: {parsed_response.get('content')}")
            break