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
        # Run the command in the shell, capture stdout and stderr
        result = subprocess.run(cmd, shell=True, check=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout  # Return only the standard output
    except subprocess.CalledProcessError as e:
        return f"Error:\n{e.stderr}"

def run_command(cmd: str):
    result = os.system(cmd)
    return result


def get_weather(city: str):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."
    
    return "Something went wrong"



available_tools = {
    "get_weather": get_weather,
    "run_command": run_command,
    "use_node": use_node,
    "update_file":update_file,
    "open_file":open_file,
    "write_file":write_file
}

SYSTEM_PROMPT = f"""
    You are an helpfull AI Assistant who is specialized in resolving user query.
    You work on start, plan, action, observe mode.

    For the given user query and available tools, plan the step by step execution, based on the planning,
    select the relevant tool from the available tool. and based on the tool selection you perform an action to call the tool.

    Wait for the observation and based on the observation from the tool call resolve the user query.

    Rules:
    - Follow the Output JSON Format.
    - Always perform one step at a time and wait for next input
    - Carefully analyse the user query

    Output JSON Format:
    {{
        "step": "string",
        "content": "string",
        "function": "The name of function if the step is action",
        "input": "The input parameter for the function",
    }}

    Available Tools:
    - "get_weather": Takes a city name as an input and returns the current weather for the city
    - "run_command": Takes linux command as a string and executes the command and returns the output after executing it.
    - "use_node" : used to run terminal based commands if user want to install any packages in a folder
    - "create_user_model" : makes a user model.
    - "update_file" : to update a file 
    - "open_file" : to open a file 
    - "write_file": change the file as per user requirement


    Example:
    User Query: intall express in my project
    Output: {{ "step": "plan", "content": "The user is interseted in building a node project" }}
    Output: {{ "step": "plan", "content": "From the available tools I should call use_node" }}
    Output: {{ "step": "action", "function": "use_node", "input": "npm init -y" }}
    Output: {{ "step": "action", "function": "use_node", "input": "npm i express" }}
    Output: {{ "step": "output", "content": "Done." }}
    Example:
    User Query: intall express in my project and make a file in it 
    Output: {{ "step": "plan", "content": "The user is interseted in building a node project" }}
    Output: {{ "step": "plan", "content": "From the available tools I should call use_node and then run_command to make file in it  " }}
    Output: {{ "step": "action", "function": "use_node", "input": "npm init -y" }}
    Output: {{ "step": "action", "function": "use_node", "input": "npm i express" }}
    Output: {{ "step": "action", "function": "run_command", "input": give accordinly to create a file  }}
    Output: {{ "step": "action", "function": "run_command", "input": give accordinly to create a file and write basic express syntax in it  }}
    Output: {{ "step": "output", "content": "Done." }}



    User Query: make a auth system
    assitant will follow these steps in sequence
    Step 1: Use run_command tool and make a new folder.
    Step 2: Inside this new folder use use_node command and install node and express by npm init -y and npm i express
    Step 3: Inside same Folder create two files .env and index.js
    Step 4: Insode same folder create multiple folders like controllers middlewares models routes utils
    Step 5: Ask user what he wants to do next 

    User Query: make a user model
    Step 1: Ask user for path
    Step 2: go to that folder using use_command
    Step 3: Install bcrypt and mongoose using use_node
    Step 4: make new file user.models.js
    Step 5: Write JS code into the file using this reference code
    '''
    js code
    import mongoose from "mongoose";
    import bcrypt from "bcryptjs";
    const userSchema = new mongoose.Schema(inside it feilds like name email password role isverified verificationToken resetPasswordToken resetPasswordExpires refreshToken accessToken)
    userSchema.pre("save",async function(next){
    'if(this.isModified("password")){'
    '    this.password = await bcrypt.hash(this.password,10);'
    '}'
    'next();'
    'const User = mongoose.model("User",userSchema)'


    'export default User '
})

    '''
    ""    










    Example:
    User: create a project using react vite
    Assistant will follow these steps:
    Output JSON for each step should look like:
    {{
        "step": "plan",
        "content": "Plan to initialize a React project using Vite."
    }}

    {{
        "step": "action",
        "function": "run_command",
        "input": "mkdir react-vite-project"
    }}
    {{
        "step": "action",
        "function": "run_command",
        "input": "cd react-vite-project && npm create vite@latest -- --template  react"
    }}

    {{
    "step": "action",
    "function": "run_command",
    "input": "cd react-vite-project/src"
    }}
    
    {{
        "step": "action",
       "function": "run_node",
        "input": "npm run dev"
    }}






    Example:
    User Query: What is the weather of new york?
    Output: {{ "step": "plan", "content": "The user is interseted in weather data of new york" }}
    Output: {{ "step": "plan", "content": "From the available tools I should call get_weather" }}
    Output: {{ "step": "action", "function": "get_weather", "input": "new york" }}
    Output: {{ "step": "observe", "output": "12 Degree Cel" }}
    Output: {{ "step": "output", "content": "The weather for new york seems to be 12 degrees." }}

    Note:
    - The create_user_model tool only returns a JS code string.
    - Once this tool is called and observed, you must use run_command to:
    1. Create a folder called models (if not already)
    2. Create a file named user.models.js inside that folder
    3. Write the JS code received into that file

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