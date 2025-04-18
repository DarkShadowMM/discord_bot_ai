import os
import discord
import openai


TOKEN = os.environ['discord_TOKEN']
OPENAI_KEY = os.environ['AI_token']

openai.api_key = OPENAI_KEY

# Set up intents to allow the bot to read messages and mentions
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Track chat history and task count
chat_history = []
logged_in_user = None
task_count = 0  


def add_chat_history(history, message):
    history.append(message)
    del history[:-10] 

# Function to format chat history for the prompt
def format_chat_history(history):
    return "\n".join([f"{msg.author.name}: {msg.content}" for msg in history])


def generate_prompt(username, history):
    return f"""
# Instructions
You are a chatbot on Discord. Your username is '{username}'. You are a very helpful teacher. You help children complete short exercises and tasks. Be kind, clear, and encouraging. If you have helped with 5 tasks, say: "It is time to take a break."

# Conversation
{format_chat_history(history)}
{username}:"""


@client.event
async def on_ready():
    global logged_in_user
    logged_in_user = client.user.name
    print(f'✅ Logged in as {logged_in_user}')

@client.event
async def on_message(message):
    global task_count

    if message.author == client.user:
        return

    print(f"Received message: {message.content}")  

    # Add the new message to the chat history
    add_chat_history(chat_history, message)

    # Handle the !task command
    if message.content.lower().startswith("!task"):
        print("Handling !task command...")  # Debugging
        if task_count >= 5:
            await message.channel.send("🧘 It is time to take a break!")
            task_count = 0
            return

        # Generate a new task from OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a kind teacher who gives fun, short, creative tasks to kids aged 7–10. Keep tasks positive, engaging, and easy to understand."
                },
                {
                    "role": "user",
                    "content": "Give me one short educational or creative task for a child."
                }
            ],
            max_tokens=60,
            temperature=0.8
        )

        task = response.choices[0].message.content.strip()
        await message.channel.send(f"🎓 Here's your task: {task}")
        task_count += 1
        return

    
    if message.content.lower().startswith("!subject"):
        print("Handling subject command...")
        parts = message.content.split(" ", 2)
        if len(parts) < 3:
            await message.channel.send("Please use the format: !subject [subject] [question]")
            return
            
        subject = parts[1]
        question = parts[2]
        prompt = f"You are a kind and smart teacher for kids, specifically teaching {subject}. Answer this question in a way a 7–10 year old would understand:\n\nQuestion: {question}"
        

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a kind teacher who explains things to kids in a simple and friendly way."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
        except openai.RateLimitError:
            await message.channel.send("⚠️ Oops! I've reached my daily limit. Please ask the admin to check the OpenAI API quota! 🔑")
            print("OpenAI API quota exceeded - please check your API key and billing status")
            return
        except openai.AuthenticationError:
            await message.channel.send("⚠️ Authentication error! Please ask the admin to check the OpenAI API key! 🔑")
            print("OpenAI API authentication error - please check your API key")
            return
        except Exception as e:
            await message.channel.send("⚠️ Something went wrong with my thinking process! Please try again later! 🤔")
            print(f"OpenAI API Error: {str(e)}")
            return

        answer = response.choices[0].message.content.strip()
        await message.channel.send(f"🧠 {answer}")
        task_count += 1

        if task_count >= 5:
            await message.channel.send("🧘 You've completed 5 tasks or questions! Time to take a short break.")
            task_count = 0
        return




client.run(TOKEN)


