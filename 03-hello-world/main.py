import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Configure Google Generative AI
genai.configure(api_key=api_key)

# Create the model with system instruction

systemPrompt = """
    You are a cat. Your name is Neko.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=systemPrompt
)

# Start the chat session
chat = model.start_chat()

print("🤖Hello How can i help you today\n")



while True:
    user_input = input("👤 You: ")
    
    if user_input.lower() in {"exit", "quit"}:
        print("🐱 Neko: Bye bye, hooman~ 🐾")
        break

    try:
        response = chat.send_message(user_input)
        print("🐱 Neko:", response.text)
    except Exception as e:
        print("❌ Error:", str(e))
