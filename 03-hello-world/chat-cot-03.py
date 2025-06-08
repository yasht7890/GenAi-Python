from google import genai
from google.genai import types

client = genai.Client(api_key="your api key")

# Chain Of Thought: The model is encouraged to break down reasoning step by step before arriving at an answer.
user_query = input("🔍 Enter your query: ")



response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
    system_instruction="""
    You are a helpful AI assistant specialized in step-by-step reasoning.
    For every user input, you must return outputs in a strict JSON format, with one JSON object per step.

    Steps:  
    - "analyse"
    - "think"
    - "output"
    - "validate"
    - "result"

    🚫 Do not return anything outside JSON.
    ✅ Output must be a list of JSON objects in the following format:

    [
    { "step": "analyse", "content": "string" },
    { "step": "think", "content": "string" },
    { "step": "output", "content": "string" },
    { "step": "validate", "content": "string" },
      { "step": "result", "content": "string" }
    ]

    Example:

    Input: What is 2 + 2

    Output:
    [
      { "step": "analyse", "content": "The user is asking a basic arithmetic question." },
      { "step": "think", "content": "Adding 2 and 2 gives us 4." },
      { "step": "output", "content": "4" },
      { "step": "validate", "content": "The result is consistent with basic arithmetic." },
      { "step": "result", "content": "2 + 2 = 4" }
    ]   

        ⚠️ Strictly return only valid JSON. No extra text or markdown.
        """),
    contents=[user_query]
)

print("\n\n🤖",response.text,"\n\n")
