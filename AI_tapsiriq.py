#Murad
import discord
import requests
import os
import random

# Load tokens from environment variables
DISCORD_BOT_TOKEN = os.getenv('Discord_token')
HUGGINGFACE_API_TOKEN = os.getenv('HuggingFace')

# Choose model
MODEL = "google/flan-t5-large"
# MODEL = "mistralai/Mistral-7B-Instruct"

# Set up Discord bot with message content intent
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Character personality prompt for Hugging Face
CHARACTER_PERSONA = (
    "You are a helpful and informative AI assistant. Respond in a friendly and concise manner."
)

# Function to query Hugging Face API
def query_huggingface(message):
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"
    }
    payload = {
        "inputs": f"{CHARACTER_PERSONA}\nUser: {message}\nAI:",
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }
    }

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{MODEL}",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            generated = result[0]["generated_text"]
            reply = generated.replace(message, "").strip()
            return reply if reply else "🤔 I couldn't come up with a response this time!"
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        elif isinstance(result, dict) and "error" in result:
            return "🕒 The model is still warming up, please try again shortly."
        else:
            return str(result)
    else:
        return f"❌ Error: API call failed with status code {response.status_code}"

# Bot startup message
@client.event
async def on_ready():
    print(f"🤖 ChatBuddy is online as {client.user} and ready to assist!")

# Handle incoming messages
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_message = message.content.lower()

    if user_message.startswith("!help"):
        help_text = (
            "📚 **ChatBuddy Commands:**\n"
            "`!ai <your question>` – Ask me anything, I'll try to help!\n"
            "`!joke` – Want a laugh? I got you.\n"
            "`!task` – Get an AI-generated task!\n"
            "`!homework` – Get an AI-generated study question!\n"
            "`!subject <subject>` – Get AI-powered questions about a specific subject!\n"
            "`!help` – Show this help message.\n"
        )
        await message.channel.send(help_text)
        return

    elif user_message.startswith("!joke"):
        jokes = [
            "Why did the computer get cold? Because it left its Windows open! 🧊",
            "I'm reading a book on anti-gravity. It's impossible to put down! 😄",
            "Why did the robot go on vacation? It needed to recharge! 🔋",
        ]
        await message.channel.send(random.choice(jokes))
        return

    elif user_message.startswith("!ai"):
        user_input = message.content[4:].strip()
        if not user_input:
            await message.channel.send("✏️ Please type your question after `!ai`.")
            return

        thinking_lines = [
            "🤖 Thinking really hard...",
            "🔍 Looking that up in my brain-database...",
            "💡 One moment while I craft a smart answer...",
            "✨ Summoning the AI powers..."
        ]
        await message.channel.send(random.choice(thinking_lines))

        response = query_huggingface(user_input)
        await message.channel.send(response)

    elif user_message.startswith("!task"):
        response = query_huggingface("Generate a simple task.")
        await message.channel.send(response)

    elif user_message.startswith("!homework"):
        user_input = message.content[10:].strip()
        if not user_input:
            await message.channel.send("✏️ Please type your question after `!homework`.")
            return

        thinking_lines = [
            "🤖 Thinking really hard...",
            "🔍 Looking that up in my brain-database...",
            "💡 One moment while I craft a smart answer...",
            "✨ Summoning the AI powers..."
        ]
        await message.channel.send(random.choice(thinking_lines))

        response = query_huggingface(user_input)
        await message.channel.send(response)

    elif user_message.startswith("!subject"):
        subject = user_message[9:].strip()
        if not subject:
            await message.channel.send("Please specify a subject after '!subject'.")
            return
        response = query_huggingface(f"Generate a question about {subject}.")
        await message.channel.send(response)


# Run the bot
client.run(DISCORD_BOT_TOKEN)
