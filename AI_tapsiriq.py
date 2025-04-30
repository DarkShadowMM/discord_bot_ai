import discord
import requests
import os
import random
import sqlite3


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

# Game states
chess_games = {}
draughts_games = {}

# Draughts pieces and board
DRAUGHTS_PIECES = {
    'w': '⚪', 'W': '⬜',  # white pieces (normal and king)
    'b': '⚫', 'B': '⬛',  # black pieces (normal and king)
    ' ': '  '  # empty square
}

INITIAL_DRAUGHTS_BOARD = [
    [' ', 'b', ' ', 'b', ' ', 'b', ' ', 'b'],
    ['b', ' ', 'b', ' ', 'b', ' ', 'b', ' '],
    [' ', 'b', ' ', 'b', ' ', 'b', ' ', 'b'],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    ['w', ' ', 'w', ' ', 'w', ' ', 'w', ' '],
    [' ', 'w', ' ', 'w', ' ', 'w', ' ', 'w'],
    ['w', ' ', 'w', ' ', 'w', ' ', 'w', ' ']
]

def new_draughts_game():
    return {
        'board': [row[:] for row in INITIAL_DRAUGHTS_BOARD],
        'turn': 'w',  # w for white, b for black
        'status': "White's turn to play",
        'selected': None,
        'must_jump': False
    }

def render_draughts_board(board):
    board_display = "⚫ **Draughts Game:**\n```\n  1 2 3 4 5 6 7 8\n"
    for i, row in enumerate(board):
        board_display += f"{chr(65+i)} "
        board_display += "".join(DRAUGHTS_PIECES[cell] for cell in row) + f" {chr(65+i)}\n"
    board_display += "  1 2 3 4 5 6 7 8\n```"
    return board_display

def parse_draughts_position(position):
    """Convert draughts notation (e.g., 'A3') to board indices (row, col)"""
    if not position or len(position) != 2:
        return None

    row = ord(position[0].upper()) - ord('A')
    col = int(position[1]) - 1

    if 0 <= row < 8 and 0 <= col < 8:
        return (row, col)
    return None

def get_valid_jumps(game, row, col):
    """Get all valid jump moves for a piece"""
    jumps = []
    piece = game['board'][row][col]
    if not piece or piece == ' ':
        return jumps

    directions = []
    if piece.lower() == 'w':
        directions.extend([(-2, -2), (-2, 2)])  # upward jumps
    if piece.lower() == 'b':
        directions.extend([(2, -2), (2, 2)])    # downward jumps
    if piece.isupper():  # king can move both directions
        directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]

    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        jump_row, jump_col = row + dr//2, col + dc//2

        if (0 <= new_row < 8 and 0 <= new_col < 8 and
            game['board'][new_row][new_col] == ' ' and
            game['board'][jump_row][jump_col] != ' ' and
            game['board'][jump_row][jump_col].lower() != piece.lower()):
            jumps.append((new_row, new_col))

    return jumps

def validate_draughts_move(game, from_pos, to_pos):
    """Validate draughts move"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Basic validation
    piece = game['board'][from_row][from_col]
    if not piece or piece == ' ':
        return False, "No piece at source position."
    if piece.lower() != game['turn']:
        return False, f"It's {'White' if game['turn'] == 'w' else 'Black'}'s turn."
    if game['board'][to_row][to_col] != ' ':
        return False, "Destination square is not empty."

    # Check for mandatory jumps
    has_jumps = False
    for r in range(8):
        for c in range(8):
            if (game['board'][r][c].lower() == game['turn'] and
                get_valid_jumps(game, r, c)):
                has_jumps = True
                break
        if has_jumps:
            break

    # If there are jumps available, only allow jump moves
    if has_jumps:
        valid_jumps = get_valid_jumps(game, from_row, from_col)
        if (to_row, to_col) in valid_jumps:
            return True, ""
        return False, "Must make a jump move when available."

    # Regular move validation
    row_diff = to_row - from_row
    col_diff = abs(to_col - from_col)

    if piece.isupper():  # King piece
        if abs(row_diff) == 1 and col_diff == 1:
            return True, ""
    else:  # Regular piece
        if piece == 'w' and row_diff == -1 and col_diff == 1:
            return True, ""
        if piece == 'b' and row_diff == 1 and col_diff == 1:
            return True, ""

    return False, "Invalid move for this piece."

def get_ai_draughts_move(game):
    """Generate a simple AI move for draughts"""
    valid_moves = []

    # Collect all valid moves for AI pieces
    for row in range(8):
        for col in range(8):
            piece = game['board'][row][col]
            if piece.lower() == game['turn']:
                # Check all possible jumps first
                jumps = get_valid_jumps(game, row, col)
                if jumps:
                    for jump in jumps:
                        valid_moves.append(((row, col), jump))
                else:
                    # Check regular moves
                    for dr, dc in [(1, -1), (1, 1)] if piece == 'b' else [(-1, -1), (-1, 1)]:
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if game['board'][new_row][new_col] == ' ':
                                valid_moves.append(((row, col), (new_row, new_col)))

    # Return random valid move
    return random.choice(valid_moves) if valid_moves else None

def make_draughts_move(game, from_pos, to_pos):
    """Execute a draughts move"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    piece = game['board'][from_row][from_col]

    # Move the piece
    game['board'][to_row][to_col] = piece
    game['board'][from_row][from_col] = ' '

    # Handle jumps
    if abs(to_row - from_row) == 2:
        jumped_row = (from_row + to_row) // 2
        jumped_col = (from_col + to_col) // 2
        game['board'][jumped_row][jumped_col] = ' '

    # King promotion
    if piece == 'w' and to_row == 0:
        game['board'][to_row][to_col] = 'W'
    elif piece == 'b' and to_row == 7:
        game['board'][to_row][to_col] = 'B'

    # Check for additional jumps
    if abs(to_row - from_row) == 2 and get_valid_jumps(game, to_row, to_col):
        game['selected'] = (to_row, to_col)
        game['must_jump'] = True
        game['status'] = f"{'White' if game['turn'] == 'w' else 'Black'} must continue jumping"
    else:
        # Switch turns
        game['turn'] = 'b' if game['turn'] == 'w' else 'w'
        game['status'] = f"{'White' if game['turn'] == 'w' else 'Black'}'s turn to play"
        game['selected'] = None
        game['must_jump'] = False

# Chess pieces
PIECES = {
    'wr': '♖', 'wn': '♘', 'wb': '♗', 'wq': '♕', 'wk': '♔', 'wp': '♙',
    'br': '♜', 'bn': '♞', 'bb': '♝', 'bq': '♛', 'bk': '♚', 'bp': '♟'
}

# Initial board setup
INITIAL_BOARD = [
    ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
    ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
    ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']
]

def new_chess_game():
    return {
        'board': [row[:] for row in INITIAL_BOARD],
        'turn': 'w',  # w for white, b for black
        'selected': None,
        'status': "White's turn to play"
    }

def get_piece_symbol(piece_code):
    return PIECES.get(piece_code, ' ')

def render_board(board):
    board_display = "♟️ **Chess Game:**\n```\n  a b c d e f g h\n"
    for i, row in enumerate(board):
        board_display += f"{8-i} "
        board_display += " ".join(get_piece_symbol(cell) for cell in row) + f" {8-i}\n"
    board_display += "  a b c d e f g h\n```"
    return board_display

def parse_position(position):
    """Convert chess notation (e.g., 'e2') to board indices (row, col)"""
    if not position or len(position) != 2:
        return None

    col = ord(position[0].lower()) - ord('a')
    row = 8 - int(position[1])

    if 0 <= row < 8 and 0 <= col < 8:
        return (row, col)
    return None

def validate_move(game, from_pos, to_pos):
    """Basic move validation"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Check if source has a piece
    piece = game['board'][from_row][from_col]
    if not piece:
        return False, "No piece at source position."

    # Check if it's the right player's turn
    if piece[0] != game['turn']:
        return False, f"It's {'White' if game['turn'] == 'w' else 'Black'}'s turn."

    # Check if destination has friendly piece
    dest_piece = game['board'][to_row][to_col]
    if dest_piece and dest_piece[0] == game['turn']:
        return False, "Cannot capture your own piece."

    # Implement basic movement rules for each piece
    piece_type = piece[1]

    # Pawn movement
    if piece_type == 'p':
        # Direction depends on color
        direction = -1 if piece[0] == 'w' else 1

        # Forward move
        if from_col == to_col and not dest_piece:
            # Single square forward
            if to_row == from_row + direction:
                return True, ""

            # Double square forward from starting position
            if ((piece[0] == 'w' and from_row == 6 and to_row == 4) or 
                (piece[0] == 'b' and from_row == 1 and to_row == 3)):
                # Check if the path is clear
                if not game['board'][from_row + direction][from_col]:
                    return True, ""

        # Capture move (diagonal)
        elif abs(from_col - to_col) == 1 and to_row == from_row + direction:
            if dest_piece and dest_piece[0] != piece[0]:
                return True, ""

    # Knight movement
    elif piece_type == 'n':
        row_diff = abs(from_row - to_row)
        col_diff = abs(from_col - to_col)
        if (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2):
            return True, ""

    # Bishop movement
    elif piece_type == 'b':
        row_diff = abs(from_row - to_row)
        col_diff = abs(from_col - to_col)
        if row_diff == col_diff:
            # Check if path is clear
            row_step = 1 if to_row > from_row else -1
            col_step = 1 if to_col > from_col else -1

            r, c = from_row + row_step, from_col + col_step
            while r != to_row:
                if game['board'][r][c]:
                    return False, "Path is not clear."
                r += row_step
                c += col_step

            return True, ""

    # Rook movement
    elif piece_type == 'r':
        if from_row == to_row or from_col == to_col:
            # Check if path is clear
            if from_row == to_row:  # Horizontal movement
                start, end = min(from_col, to_col), max(from_col, to_col)
                for c in range(start + 1, end):
                    if game['board'][from_row][c]:
                        return False, "Path is not clear."
            else:  # Vertical movement
                start, end = min(from_row, to_row), max(from_row, to_row)
                for r in range(start + 1, end):
                    if game['board'][r][from_col]:
                        return False, "Path is not clear."

            return True, ""

    # Queen movement (combination of bishop and rook)
    elif piece_type == 'q':
        row_diff = abs(from_row - to_row)
        col_diff = abs(from_col - to_col)

        # Diagonal movement
        if row_diff == col_diff:
            row_step = 1 if to_row > from_row else -1
            col_step = 1 if to_col > from_col else -1

            r, c = from_row + row_step, from_col + col_step
            while r != to_row:
                if game['board'][r][c]:
                    return False, "Path is not clear."
                r += row_step
                c += col_step

            return True, ""

        # Straight movement
        elif from_row == to_row or from_col == to_col:
            if from_row == to_row:  # Horizontal movement
                start, end = min(from_col, to_col), max(from_col, to_col)
                for c in range(start + 1, end):
                    if game['board'][from_row][c]:
                        return False, "Path is not clear."
            else:  # Vertical movement
                start, end = min(from_row, to_row), max(from_row, to_row)
                for r in range(start + 1, end):
                    if game['board'][r][from_col]:
                        return False, "Path is not clear."

            return True, ""

    # King movement
    elif piece_type == 'k':
        row_diff = abs(from_row - to_row)
        col_diff = abs(from_col - to_col)

        # Kings move one square in any direction
        if row_diff <= 1 and col_diff <= 1:
            return True, ""

    return False, "Invalid move for this piece."

def get_ai_chess_move(game):
    """Generate a simple AI move for chess"""
    valid_moves = []

    # Collect all valid moves for AI pieces
    for from_row in range(8):
        for from_col in range(8):
            piece = game['board'][from_row][from_col]
            if piece and piece[0] == game['turn']:
                for to_row in range(8):
                    for to_col in range(8):
                        if validate_move(game, (from_row, from_col), (to_row, to_col))[0]:
                            valid_moves.append(((from_row, from_col), (to_row, to_col)))

    # Return random valid move
    return random.choice(valid_moves) if valid_moves else None

def make_move(game, from_pos, to_pos):
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Move the piece
    game['board'][to_row][to_col] = game['board'][from_row][from_col]
    game['board'][from_row][from_col] = ''

    # Switch turns
    game['turn'] = 'b' if game['turn'] == 'w' else 'w'
    game['status'] = f"{'White' if game['turn'] == 'w' else 'Black'}'s turn to play"
    game['selected'] = None

# Function to query Hugging Face API
def query_huggingface(message):
    try:
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
            json=payload,
            timeout=30
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

from database import Database
from ai_personas import get_persona_prompt
import re

# Initialize database
db = Database()

# Bot startup message
@client.event
async def on_ready():
    print(f"🤖 ChatBuddy is online as {client.user} and ready to assist!")

async def find_citation(topic):
    prompt = f"Find and provide an academic citation related to: {topic}"
    response = query_huggingface(prompt)
    return response

async def get_styled_response(message, style):
    persona_prompt = get_persona_prompt(style)
    full_prompt = f"{persona_prompt}\nUser question: {message}"
    return query_huggingface(full_prompt)

# Handle incoming messages
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Track user
    db.add_user(str(message.author.id), str(message.author))
    db.update_user_activity(str(message.author.id))

    user_message = message.content.lower()

    # Handle empty messages
    if not user_message.strip():
        await message.channel.send("❌ Please provide a message with your command!")
        return
        
    # Handle citation requests
    elif user_message.startswith("!cite"):
        topic = message.content[6:].strip()
        if not topic:
            await message.channel.send("❌ Please provide a topic to find citations for!")
            return
        try:
            response = await find_citation(topic)
            await message.channel.send(f"📚 **Citation for '{topic}':**\n{response}")
        except Exception as e:
            await message.channel.send("❌ Sorry, I couldn't fetch a citation right now. Please try again later.")
            
    # Handle style-specific responses
    elif user_message.startswith("!style"):
        parts = message.content.split(maxsplit=2)
        if len(parts) < 3:
            styles = ", ".join(PERSONAS.keys())
            await message.channel.send(f"❌ Please use format: !style <style> <question>\nAvailable styles: {styles}")
            return
            
        style = parts[1].lower()
        question = parts[2]
        
        if style not in PERSONAS:
            styles = ", ".join(PERSONAS.keys())
            await message.channel.send(f"❌ Invalid style. Available styles: {styles}")
            return
            
        try:
            response = await get_styled_response(question, style)
            await message.channel.send(f"🎭 **{style.title()} style answer:**\n{response}")
        except Exception as e:
            await message.channel.send("❌ Sorry, I couldn't process your request right now. Please try again later.")
    channel_id = str(message.channel.id)

    if user_message.startswith("!help"):
        help_text = (
            "📚 **ChatBuddy Commands:**\n"
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

    elif user_message.startswith("!game"):
        game_command = user_message[6:].strip().lower()
        is_ai_mode = "ai" in game_command

        if is_ai_mode:
            game_command = game_command.replace("ai", "").strip()

        if not game_command:
            game_help = (
                "🎮 **Available Games:**\n\n"
                "**AI Mode:**\n"
                "- Add 'ai' to game command to play against AI (e.g., `!game ai chess`)\n\n"
                "1. **Chess** ♟️\n"
                "- Type `!game chess` to start a chess game\n"
                "- Move pieces with `!move e2 e4` format\n"
                "- Type `!select e2` to highlight a piece\n"
                "- Type `!move e4` to move selected piece\n"
                "- Type `!chess` to view the current board\n"
                "- Type `!reset chess` to reset the game\n\n"
                "2. **Draughts** 🔵\n"
                "- Type `!game draughts` to start a draughts game\n"
                "- Get tips and game scenarios\n"
            )
            await message.channel.send(game_help)
            return

        if game_command == "chess":
            # Create a new chess game for this channel
            chess_games[channel_id] = new_chess_game()
            game = chess_games[channel_id]
            if is_ai_mode:
                game["mode"] = "ai"

            # Display the board
            board_display = render_board(game['board'])

            instructions = (
                "**How to play:**\n"
                "1. White pieces: ♔♕♖♗♘♙\n"
                "2. Black pieces: ♚♛♜♝♞♟\n"
                "3. Move with `!move e2 e4` or select with `!select e2` then `!move e4`\n"
                "4. Type `!chess` to see the current board\n"
                "5. Type `!reset chess` to reset the game\n"
            )

            await message.channel.send(board_display + "\n" + instructions)

        elif game_command == "draughts":
            # Create a new draughts game for this channel
            draughts_games[channel_id] = new_draughts_game()
            game = draughts_games[channel_id]
            if is_ai_mode:
                game["mode"] = "ai"

            # Display the board
            board_display = render_draughts_board(game['board'])

            instructions = (
                "**How to play Draughts:**\n"
                "1. White pieces: ⚪(normal) ⬜(king)\n"
                "2. Black pieces: ⚫(normal) ⬛(king)\n"
                "3. Move with `!dmove A3 B4` or select with `!dselect A3` then `!dmove B4`\n"
                "4. Type `!draughts` to see the current board\n"
                "5. Type `!reset draughts` to reset the game\n"
            )

            await message.channel.send(board_display + "\n" + instructions)


    # Chess game commands
    elif user_message.startswith("!chess"):
        if channel_id not in chess_games:
            await message.channel.send("❌ No chess game in progress. Type `!game chess` to start.")
            return

        # Display the current board
        game = chess_games[channel_id]
        board_display = render_board(game['board'])
        status_message = f"\n**Status:** {game['status']}"

        await message.channel.send(board_display + status_message)

    elif user_message.startswith("!select"):
        if channel_id not in chess_games:
            await message.channel.send("❌ No chess game in progress. Type `!game chess` to start.")
            return

        game = chess_games[channel_id]
        position = user_message[8:].strip().lower()
        pos = parse_position(position)

        if not pos:
            await message.channel.send("❌ Invalid position. Use format like 'e2'.")
            return

        row, col = pos
        piece = game['board'][row][col]

        if not piece:
            await message.channel.send("❌ No piece at that position.")
            return

        if piece[0] != game['turn']:
            await message.channel.send(f"❌ It's {'White' if game['turn'] == 'w' else 'Black'}'s turn.")
            return

        game['selected'] = pos
        game['status'] = f"Selected {get_piece_symbol(piece)} at {position}. Use `!move <position>` to move."

        # Display the board with selection
        board_display = render_board(game['board'])
        status_message = f"\n**Status:** {game['status']}"

        await message.channel.send(board_display + status_message)

    elif user_message.startswith("!move"):
        if channel_id not in chess_games:
            await message.channel.send("❌ No chess game in progress. Type `!game chess` to start.")
            return

        game = chess_games[channel_id]
        parts = user_message[6:].strip().lower().split()

        # Format can be "!move e2 e4" or "!move e4" (if a piece is selected)
        if len(parts) == 2:
            from_pos = parse_position(parts[0])
            to_pos = parse_position(parts[1])

            if not from_pos or not to_pos:
                await message.channel.send("❌ Invalid position(s). Use format like 'e2 e4'.")
                return

        elif len(parts) == 1 and game['selected']:
            from_pos = game['selected']
            to_pos = parse_position(parts[0])

            if not to_pos:
                await message.channel.send("❌ Invalid position. Use format like 'e4'.")
                return
        else:
            await message.channel.send("❌ Invalid move format. Use `!move e2 e4` or select a piece first with `!select e2`.")
            return

        # Validate and make the move
        valid, error_msg = validate_move(game, from_pos, to_pos)

        if valid:
            make_move(game, from_pos, to_pos)
            board_display = render_board(game['board'])
            status_message = f"\n**Status:** {game['status']}"

            await message.channel.send(board_display + status_message)

            # AI's turn
            if "ai" in chess_games[channel_id].get("mode", ""):
                ai_move = get_ai_chess_move(game)
                if ai_move:
                    make_move(game, ai_move[0], ai_move[1])
                    board_display = render_board(game['board'])
                    status_message = f"\n**Status:** {game['status']}"
                    await message.channel.send("🤖 AI move:" + board_display + status_message)
        else:
            await message.channel.send(f"❌ Invalid move: {error_msg}")

    elif user_message.startswith("!reset chess"):
        if channel_id in chess_games:
            chess_games[channel_id] = new_chess_game()
            game = chess_games[channel_id]
            board_display = render_board(game['board'])

            await message.channel.send("♟️ **Chess game reset!**\n" + board_display)
        else:
            await message.channel.send("❌ No chess game to reset. Type `!game chess` to start.")

    elif user_message.startswith("!draughts"):
        if channel_id not in draughts_games:
            await message.channel.send("❌ No draughts game in progress. Type `!game draughts` to start.")
            return

        # Display the current board
        game = draughts_games[channel_id]
        board_display = render_draughts_board(game['board'])
        status_message = f"\n**Status:** {game['status']}"

        await message.channel.send(board_display + status_message)

    elif user_message.startswith("!dselect"):
        if channel_id not in draughts_games:
            await message.channel.send("❌ No draughts game in progress. Type `!game draughts` to start.")
            return

        game = draughts_games[channel_id]
        position = user_message[9:].strip().upper()
        pos = parse_draughts_position(position)

        if not pos:
            await message.channel.send("❌ Invalid position. Use format like 'A3'.")
            return

        row, col = pos
        piece = game['board'][row][col]

        if not piece or piece == ' ':
            await message.channel.send("❌ No piece at that position.")
            return

        if piece.lower() != game['turn']:
            await message.channel.send(f"❌ It's {'White' if game['turn'] == 'w' else 'Black'}'s turn.")
            return

        game['selected'] = pos
        game['status'] = f"Selected piece at {position}. Use `!dmove <position>` to move."

        # Display the board with selection
        board_display = render_draughts_board(game['board'])
        status_message = f"\n**Status:** {game['status']}"

        await message.channel.send(board_display + status_message)

    elif user_message.startswith("!dmove"):
        if channel_id not in draughts_games:
            await message.channel.send("❌ No draughts game in progress. Type `!game draughts` to start.")
            return

        game = draughts_games[channel_id]
        parts = user_message[7:].strip().upper().split()

        # Format can be "!dmove A3 B4" or "!dmove B4" (if a piece is selected)
        if len(parts) == 2:
            from_pos = parse_draughts_position(parts[0])
            to_pos = parse_draughts_position(parts[1])

            if not from_pos or not to_pos:
                await message.channel.send("❌ Invalid position(s). Use format like 'A3 B4'.")
                return

        elif len(parts) == 1 and game['selected']:
            from_pos = game['selected']
            to_pos = parse_draughts_position(parts[0])

            if not to_pos:
                await message.channel.send("❌ Invalid position. Use format like 'B4'.")
                return
        else:
            await message.channel.send("❌ Invalid move format. Use `!dmove A3 B4` or select a piece first with `!dselect A3`.")
            return

        # Validate and make the move
        valid, error_msg = validate_draughts_move(game, from_pos, to_pos)

        if valid:
            make_draughts_move(game, from_pos, to_pos)
            board_display = render_draughts_board(game['board'])
            status_message = f"\n**Status:** {game['status']}"

            await message.channel.send(board_display + status_message)

            # AI's turn
            if "ai" in draughts_games[channel_id].get("mode", ""):
                ai_move = get_ai_draughts_move(game)
                if ai_move:
                    make_draughts_move(game, ai_move[0], ai_move[1])
                    board_display = render_draughts_board(game['board'])
                    status_message = f"\n**Status:** {game['status']}"
                    await message.channel.send("🤖 AI move:" + board_display + status_message)
        else:
            await message.channel.send(f"❌ Invalid move: {error_msg}")

    elif user_message.startswith("!reset draughts"):
        if channel_id in draughts_games:
            draughts_games[channel_id] = new_draughts_game()
            game = draughts_games[channel_id]
            board_display = render_draughts_board(game['board'])

            await message.channel.send("⚫ **Draughts game reset!**\n" + board_display)
        else:
            await message.channel.send("❌ No draughts game to reset. Type `!game draughts` to start.")

    if user_message.startswith("!book"):
        ederslik_text = (
            "📚 **E-dərslik:**\n"
            "E-dərslik portalına keçid: https://e-derslik.edu.az/portal/\n"
            "Bütün fənlər üzrə elektron dərsliklər burada!"
        )
        await message.channel.send(ederslik_text)
        
            


# Run the bot
client.run(DISCORD_BOT_TOKEN)
