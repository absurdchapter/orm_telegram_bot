import asyncio
import logging.handlers
import os

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot import logger

from src.glossary import *
from src.userdata import get_user_data, write_user_data
from src.utils import calculate_one_rep_max, calculate_worker
from telegram_token import TOKEN

bot = AsyncTeleBot(TOKEN)

logger.setLevel(logging.DEBUG)
os.makedirs('logs', exist_ok=True)
fh = logging.handlers.TimedRotatingFileHandler('logs/log', when='midnight')
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'))
logger.addHandler(fh)


@bot.message_handler(func=lambda _: True)
async def handler(message):
    logger.info("Message from %s: %s", message.chat.id, message.text)
    user_data = get_user_data(message.chat.id)
    if user_data is None or message.text.strip() == '/start' or message.text.strip() in restart_words:
        user_data = {'conversation_state': 'init'}
    await reply(message, user_data)


async def reply(message, user_data):
    logger.debug("User data:"+str(user_data))

    conversation_state = user_data['conversation_state']

    if conversation_state == 'init':
        await reply_start(message, user_data)
    elif conversation_state == 'option_select':
        await reply_option_select(message, user_data)

    elif conversation_state == 'orm_init':
        await reply_orm_init(message, user_data)
    elif conversation_state == 'orm_weight':
        await reply_orm_weight(message, user_data)
    elif conversation_state == 'orm_reps':
        await reply_orm_reps(message, user_data)
    elif conversation_state == 'orm_sets':
        await reply_orm_sets(message, user_data)
    elif conversation_state == 'orm_type':
        await reply_orm_type(message, user_data)

    elif conversation_state == 'worker_init':
        await reply_worker_init(message, user_data)
    elif conversation_state == 'worker_weight':
        await reply_worker_weight(message, user_data)
    elif conversation_state == 'worker_reps':
        await reply_worker_reps(message, user_data)
    elif conversation_state == 'worker_sets':
        await reply_worker_sets(message, user_data)
    elif conversation_state == 'worker_type':
        await reply_worker_type(message, user_data)

    else:
        assert False

    write_user_data(message.chat.id, user_data)


def reply_markup(buttons):
    markup = types.ReplyKeyboardMarkup()
    markup.row(*buttons)
    markup.one_time_keyboard = True
    return markup


async def reply_start(message, user_data):
    text = "Hi, I can help you calculate your *one-rep max* or *rep weight*.\n" \
           "Please select an option."
    markup = reply_markup(OPTION_LIST)
    await bot.reply_to(message, text, reply_markup=markup, parse_mode="markdown")
    user_data['conversation_state'] = 'option_select'


async def reply_option_select(message, user_data):
    if message.text.strip() in OPTION_LIST:
        # BIFURCATION
        option = OPTION_DICT[message.text.strip()]
        user_data['conversation_state'] = option + '_init'
        await reply(message, user_data)
    else:
        text = "I did not understand. Please select an option."
        markup = reply_markup(OPTION_LIST)
        await bot.reply_to(message, text, reply_markup=markup)


async def reply_orm_init(message, user_data):
    text = "Enter the lifted weight"
    user_data['conversation_state'] = 'orm_weight'
    await bot.reply_to(message, text)


async def reply_orm_weight(message, user_data):
    try:
        user_data['weight'] = float(message.text.strip())
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the lifted weight (a float number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of reps'
    user_data['conversation_state'] = 'orm_reps'
    await bot.reply_to(message, text)


async def reply_orm_reps(message, user_data):
    try:
        user_data['reps'] = int(message.text.strip())
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of reps (a whole number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of sets'
    user_data['conversation_state'] = 'orm_sets'
    await bot.reply_to(message, text)


async def reply_orm_sets(message, user_data):
    try:
        user_data['sets'] = int(message.text.strip())
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of sets (a whole number)"
        await bot.reply_to(message, text)
        return

    text = 'Select the exercise'
    user_data['conversation_state'] = 'orm_type'
    markup = reply_markup(EXERCISE_LIST)
    await bot.reply_to(message, text, reply_markup=markup)


async def reply_orm_type(message, user_data):
    if message.text.strip() in EXERCISE_LIST:
        user_data['exercise'] = EXERCISE_DICT[message.text.strip()]

        orm = calculate_one_rep_max(user_data['weight'],
                                    user_data['reps'],
                                    user_data['sets'],
                                    user_data['exercise']
                                    )

        text = '_Weight lifted: %lg_\n' % user_data['weight']
        text += '_Reps: %d_\n' % user_data['reps']
        text += '_Sets: %d_\n' % user_data['sets']
        text += '_Exercise: %s_\n\n' % message.text.strip()

        if orm > 0:
            text += '*Your one-rep max: %d*' % int(orm)
        else:
            text += '*Your one-rep max: ambulance*'

        markup = reply_markup(RESTART_WORDS)
        user_data['conversation_state'] = 'init'
        del user_data['weight']
        del user_data['reps']
        del user_data['sets']

        await bot.reply_to(message, text, reply_markup=markup, parse_mode="markdown")

    else:
        text = 'I did not understand.\n'
        text += 'Please select the exercise.'
        markup = reply_markup(OPTION_LIST)
        await bot.reply_to(message, text, reply_markup=markup)


async def reply_worker_init(message, user_data):
    text = 'Enter your one-rep max'
    user_data['conversation_state'] = 'worker_weight'
    await bot.reply_to(message, text)


async def reply_worker_weight(message, user_data):
    try:
        user_data['orm'] = float(message.text.strip())
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the one-rep max (a float number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of reps'
    user_data['conversation_state'] = 'worker_reps'
    await bot.reply_to(message, text)


async def reply_worker_reps(message, user_data):
    try:
        user_data['reps'] = int(message.text.strip())
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of reps (a whole number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of sets'
    user_data['conversation_state'] = 'worker_sets'
    await bot.reply_to(message, text)


async def reply_worker_sets(message, user_data):
    try:
        user_data['sets'] = int(message.text.strip())
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of sets (a whole number)"
        await bot.reply_to(message, text)
        return

    text = 'Select the exercise'
    user_data['conversation_state'] = 'worker_type'
    markup = reply_markup(EXERCISE_LIST)
    await bot.reply_to(message, text, reply_markup=markup)


async def reply_worker_type(message, user_data):
    if message.text.strip() in EXERCISE_LIST:
        user_data['exercise'] = EXERCISE_DICT[message.text.strip()]

        worker = calculate_worker(user_data['orm'],
                                  user_data['reps'],
                                  user_data['sets'],
                                  user_data['exercise'])

        text = '_One rep max: %lg_\n' % user_data['orm']
        text += '_Reps: %d_\n' % user_data['reps']
        text += '_Sets: %d_\n' % user_data['sets']
        text += '_Exercise: %s_\n\n' % message.text.strip()

        if worker > 0:
            text += '*Your rep weight: %d*' % int(worker)
        else:
            text += '*Your rep weight: ambulance*'

        markup = reply_markup(RESTART_WORDS)
        user_data['conversation_state'] = 'init'
        del user_data['orm']
        del user_data['reps']
        del user_data['sets']

        await bot.reply_to(message, text, reply_markup=markup, parse_mode="markdown")

    else:
        text = 'I did not understand.\n'
        text += 'Please select the exercise.'
        markup = reply_markup(EXERCISE_LIST)
        await bot.reply_to(message, text, reply_markup=markup)

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.infinity_polling(logger_level=logging.DEBUG))
loop.close()
