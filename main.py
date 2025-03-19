from typing import Final
from dotenv import load_dotenv
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_API_KEY: Final = os.getenv("TELEGRAM_API_KEY")
BOT_USERNAME: Final = "@jitsuna_bot"

