
# 🤖 ChatBuddy – AI-Powered Discord Bot

ChatBuddy is an AI-powered Discord bot that uses the Hugging Face inference API to answer questions, tell jokes, generate tasks, and help with studies in a fun, conversational style.

## 🌟 Features

- `!ai <your question>` – Ask anything, get an AI-powered answer
- `!joke` – Get a random tech-themed joke
- `!task` – Receive a simple AI-generated task
- `!homework <topic>` – Get study help from the AI
- `!subject <subject>` – Generate a question related to a specific subject
- `!help` – Show command list

## 🚀 Getting Started

### 1. Clone the Repository


### 2. Set Up Environment Variables

Create a `.env` file or set environment variables manually. You'll need:

```
Discord_token=YOUR_DISCORD_BOT_TOKEN
HuggingFace=YOUR_HUGGINGFACE_API_TOKEN
```

Alternatively, set them directly in your terminal or hosting environment.

### 3. Install Dependencies

Make sure you have Python 3.8 or higher installed, then:

### 4. Run the Bot

If everything is set up correctly, ChatBuddy will go online and start responding to commands!


## 🧠 AI Model Info

- Default model: `google/flan-t5-large`
- You can switch to another Hugging Face model (like `mistralai/Mistral-7B-Instruct`) by editing the `MODEL` variable in the code.


## 🛠️ File Overview

- `bot.py` – Main bot script
- `.env` – Environment variable file (should be in `.gitignore`)
- `README.md` – You're reading it!



This bot is created by Murad Mirzeyev for ADA SCHOOL AI Challenge 2025
