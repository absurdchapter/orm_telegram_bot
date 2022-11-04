import os
from telebot import asyncio_helper

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

class TelegramTokenNotSpecified(Exception):
    pass

if not TELEGRAM_TOKEN:
    raise TelegramTokenNotSpecified("Please specify TELEGRAM_TOKEN environmental variable or edit src/config.py")

if os.environ.get('PYTHONANYWHERE'):
    asyncio_helper.proxy = "http://proxy.server:3128"
