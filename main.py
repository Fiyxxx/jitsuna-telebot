from typing import Final
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from database import Database

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.info("Starting bot...")

TELEGRAM_API_KEY: Final = os.getenv("TELEGRAM_API_KEY")
BOT_USERNAME: Final = "@jitsuna_bot"
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username)
    
    welcome_text = (
        f"Hello {user.first_name}! 👋\n\n"
        "I'm Jitsuna, your habit tracking assistant. I'll help you build and maintain good habits.\n\n"
        "Here's what I can do:\n"
        "• Track up to 8 habits (for focus and effectiveness)\n"
        "• Award XP for completed habits\n"
        "• Track your streaks\n"
        "• Set daily reminders\n\n"
        "Use /help to see all available commands!"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Available commands:\n\n"
        "/start - Start the bot\n"
        "/addhabit <name> - Add a new habit\n"
        "/tracker - View and manage your habits\n"
        "/removehabit <name> - Remove a habit\n"
        "/setreminder <hour> - Set daily reminder (0-23)\n"
        "/help - Show this help message\n\n"
        "Features:\n"
        "• 5 XP base reward per completed habit\n"
        "• Streak bonus XP (equals streak days)\n"
        "• Level up every 50 XP\n"
        "• Daily reset at midnight (your timezone)"
    )
    await update.message.reply_text(help_text)

async def add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a habit name: /addhabit <name>")
        return
    
    habit_name = " ".join(context.args)
    user_id = update.effective_user.id
    
    if db.add_habit(user_id, habit_name):
        await update.message.reply_text(f"✅ Added habit: {habit_name}")
    else:
        await update.message.reply_text(
            "❌ You've reached the maximum of 8 habits. "
            "This limit helps maintain focus and effectiveness. "
            "Remove some habits first using /removehabit"
        )

async def remove_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a habit name: /removehabit <name>")
        return
    
    habit_name = " ".join(context.args)
    user_id = update.effective_user.id
    
    if db.remove_habit(user_id, habit_name):
        await update.message.reply_text(f"✅ Removed habit: {habit_name}")
    else:
        await update.message.reply_text("❌ Habit not found. Check your habits with /tracker")

async def tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    habits = db.get_user_habits(user_id)
    xp, level = db.get_user_xp(user_id)
    
    if not habits:
        await update.message.reply_text(
            "You don't have any habits yet. Add one with /addhabit <name>"
        )
        return
    
    text = f"🎯 Your Habits (Level {level}, {xp} XP)\n\n"
    keyboard = []
    
    for habit_id, name, streak, last_completed in habits:
        status = "✅" if last_completed else "❌"
        text += f"{name} - Streak: {streak} days {status}\n"
        keyboard.append([
            InlineKeyboardButton(
                f"{name} {status}",
                callback_data=f"toggle_{habit_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("toggle_"):
        habit_id = int(query.data.split("_")[1])
        user_id = query.from_user.id
        
        if db.toggle_habit(user_id, habit_id):
            await query.message.edit_text(
                "✅ Habit status updated! Use /tracker to see your habits."
            )
        else:
            await query.message.edit_text(
                "❌ Failed to update habit status. Please try again."
            )

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide an hour (0-23): /setreminder <hour>")
        return
    
    try:
        hour = int(context.args[0])
        if not 0 <= hour <= 23:
            raise ValueError
        
        user_id = update.effective_user.id
        db.set_reminder(user_id, hour)
        await update.message.reply_text(f"✅ Daily reminder set for {hour:02d}:00")
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid hour (0-23)")

async def log_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    logging.info(f"User ({user.id}, @{user.username}) sent: {message_text}")  # Log all messages

def main():
    application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addhabit", add_habit))
    application.add_handler(CommandHandler("removehabit", remove_habit))
    application.add_handler(CommandHandler("tracker", tracker))
    application.add_handler(CommandHandler("setreminder", set_reminder))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_user_input))
    # Start the bot
    application.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()
    