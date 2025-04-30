
# 🤖 ChatBuddy – AI-Powered Discord Bot

ChatBuddy is an AI-powered Discord bot that uses the Hugging Face inference API to answer questions, tell jokes, generate tasks, and help with studies in a fun, conversational style.

## 🌟 Features

"`!ai <your question>` – Ask me anything, I'll try to help!\n"
"`!style <style> <question>` – Get answers in different styles (kid, teacher, poet, historian, scientist, chef, detective)\n"
"`!cite <topic>` – Find academic citations for any topic\n"
"`!joke` – Want a laugh? I got you.\n"
"`!task` – Get an AI-generated task!\n"
"`!homework` – Get an AI-generated study question!\n"
"`!subject <subject>` – Get AI-powered questions about a specific subject!\n"
"`!game` – Show available games and how to play them!\n"
"`!help` – Show this help message.\n\n"
            "**Examples:**\n"
"`!style kid What is gravity?` – Get a kid-friendly explanation\n"
"`!cite quantum physics` – Find citations about quantum physics\n"
"`!book` – Get link to e-derslik portal\n"
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
