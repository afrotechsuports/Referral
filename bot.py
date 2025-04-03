import sqlite3
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Your bot token
TOKEN = "7612955995:AAEQ5dHvhKrnFICYTxfP875IKmok3tbthgI"

# List of emojis for users
USER_EMOJIS = ["😀", "😎", "🤓", "😺", "🐶", "🦁", "🐻", "🦊", "🐼", "🐨"]

# Set up the database with a column for user emoji
def setup_database():
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()
    # Table for users with points, emoji, link views, and link sends
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 0, emoji TEXT, link_views INTEGER DEFAULT 0, link_sends INTEGER DEFAULT 0)''')
    # Table for tracking who invited whom
    c.execute('''CREATE TABLE IF NOT EXISTS referrals 
                 (invited_user_id INTEGER PRIMARY KEY, invited_username TEXT, inviter_id INTEGER)''')
    conn.commit()
    conn.close()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id
    # Add user to the database if not already present
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()
    # Assign a random emoji to the user
    user_emoji = random.choice(USER_EMOJIS)
    c.execute("INSERT OR IGNORE INTO users (user_id, username, points, emoji, link_views, link_sends) VALUES (?, ?, 0, ?, 0, 0)",
              (user.id, user.username, user_emoji))
    conn.commit()
    conn.close()
    # Check if the user joined via a referral link
    if context.args and context.args[0].isdigit():
        inviter_id = int(context.args[0])
        # Increment link views for the inviter
        conn = sqlite3.connect("referrals.db")
        c = conn.cursor()
        c.execute("UPDATE users SET link_views = link_views + 1 WHERE user_id = ?", (inviter_id,))
        # Store the referral
        c.execute("INSERT OR IGNORE INTO referrals (invited_user_id, invited_username, inviter_id) VALUES (?, ?, ?)",
                  (user.id, user.username, inviter_id))
        # Award 30 points per referral
        c.execute("UPDATE users SET points = points + 30 WHERE user_id = ?", (inviter_id,))
        conn.commit()
        conn.close()
        await context.bot.send_message(chat_id=chat_id, text=f"🎉 Welcome! You were invited by user ID {inviter_id}. They earned 30 points! 🌟")
    # Show the referral button
    keyboard = [[InlineKeyboardButton("Get Referral Link 📩", callback_data='get_referral')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_msg = "👋 Welcome to the Referral Bot! Invite friends to earn points. Click below to get your referral link:"
    await context.bot.send_message(chat_id=chat_id, text=welcome_msg, reply_markup=reply_markup)

# Handle button clicks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    chat_id = query.message.chat_id
    if query.data == 'get_referral':
        # Increment link sends for the user
        conn = sqlite3.connect("referrals.db")
        c = conn.cursor()
        c.execute("UPDATE users SET link_sends = link_sends + 1 WHERE user_id = ?", (user.id,))
        # Get user's referral stats
        c.execute("SELECT points, emoji FROM users WHERE user_id = ?", (user.id,))
        user_data = c.fetchone()
        points, user_emoji = user_data
        c.execute("SELECT COUNT(*) FROM referrals WHERE inviter_id = ?", (user.id,))
        total_referrals = c.fetchone()[0]
        conn.commit()
        conn.close()
        # Generate referral link
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user.id}"
        # Create a "Copy Link" button
        keyboard = [[InlineKeyboardButton("Copy Referral Link 📋", callback_data=f'copy_{referral_link}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Show referral stats
        stats_msg = (
            f"📊 *Your Referral Stats* 📊\n"
            f"{user_emoji} *{user.username}*\n"
            f"👥 Users Referred: *{total_referrals}*\n"
            f"⭐ Points: *{points}*\n\n"
            f"🔗 *Your Referral Link:* {referral_link}"
        )
        await context.bot.send_message(chat_id=chat_id, text=stats_msg, reply_markup=reply_markup, parse_mode='Markdown')
    elif query.data.startswith('copy_'):
        referral_link = query.data.replace('copy_', '')
        await query.message.reply_text(f"✅ Link copied to clipboard:\n{referral_link}")

# Referral link generator (for direct command)
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id
    # Increment link sends for the user
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()
    c.execute("UPDATE users SET link_sends = link_sends + 1 WHERE user_id = ?", (user.id,))
    # Get user's referral stats
    c.execute("SELECT points, emoji FROM users WHERE user_id = ?", (user.id,))
    user_data = c.fetchone()
    points, user_emoji = user_data
    c.execute("SELECT COUNT(*) FROM referrals WHERE inviter_id = ?", (user.id,))
    total_referrals = c.fetchone()[0]
    conn.commit()
    conn.close()
    # Generate referral link
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user.id}"
    # Create a "Copy Link" button
    keyboard = [[InlineKeyboardButton("Copy Referral Link 📋", callback_data=f'copy_{referral_link}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Show referral stats
    stats_msg = (
        f"📊 *Your Referral Stats* 📊\n"
        f"{user_emoji} *{user.username}*\n"
        f"👥 Users Referred: *{total_referrals}*\n"
        f"⭐ Points: *{points}*\n\n"
        f"🔗 *Your Referral Link:* {referral_link}"
    )
    await context.bot.send_message(chat_id=chat_id, text=stats_msg, reply_markup=reply_markup, parse_mode='Markdown')

# Track new members in the group
async def track_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    chat_id = update.message.chat_id
    # Add the new member to the users table
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()
    user_emoji = random.choice(USER_EMOJIS)
    c.execute("INSERT OR IGNORE INTO users (user_id, username, points, emoji, link_views, link_sends) VALUES (?, ?, 0, ?, 0, 0)",
              (new_member.id, new_member.username, user_emoji))
    conn.commit()
    conn.close()
    await context.bot.send_message(chat_id=chat_id, text=f"🎉 Welcome to the group, {new_member.username}!")

# Main function
def main():
    setup_database()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_referral))
    application.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()