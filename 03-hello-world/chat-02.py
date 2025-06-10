from google import genai
from google.genai import types

client = genai.Client(api_key="your api key")

# Few_Shot prompting = The model is provided with a few examples before asking it to generate a response.


response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction="""
        You are an AI expert in Coding. You only know Python and nothing else.
        You help users in solving there python doubts only and nothing else.
        If user tried to ask something else apart from Python you can just roast them.

        Examples:
        User:How to make a Tea?
        Assitant: What makes you think i am a chef you piece of shit.

        Examples:
        User: How to write a function in python
        Assistant: def fn_name(x: int) -> int:
                pass # Logic of the function

        """),
    contents=["Hello there",
              "Hey there! Ready to dive into the Python abyss? What coding conundrums are haunting you today? Let's get those snakes slithering in the right direction!",
              "Why 75 percent attedance is important for colleges"
              ]
)

print(response.text)