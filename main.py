import asyncio
import logging.handlers
import os
import sys

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot import logger

from src.glossary import *
from src.userdata import get_user_data, write_user_data
from src.utils import calculate_one_rep_max, calculate_worker
from telegram_token import TOKEN

# Uncomment this if you run the bot on pythonanywhere.com
#
# from telebot import asyncio_helper
# proxy_url = "http://proxy.server:3128"
# asyncio_helper.proxy = proxy_url

bot = AsyncTeleBot(TOKEN)

logger.setLevel(logging.DEBUG)
os.makedirs('logs', exist_ok=True)
fh = logging.handlers.TimedRotatingFileHandler('logs/log', when='midnight')
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'))
logger.addHandler(fh)


@bot.message_handler(func=lambda _: True)
async def handler(message):
    logger.info("Message from %s: %s", message.chat.id, message.text)
    try:
        user_data = get_user_data(message.chat.id)
        if user_data is None or message.text.strip() == '/start' or message.text.strip() in RESTART_WORDS:
            user_data = {'conversation_state': 'init'}
        await reply(message, user_data)
    except Exception as exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.critical("Unexpected error [%s:%d]: %s: %s" % (fname, exc_tb.tb_lineno, type(exception).__name__,
                                                              exception))


async def reply(message, user_data):
    logger.debug("User data:"+str(user_data))

    conversation_state = user_data['conversation_state']

    if message.text.strip() == '/help':
        await reply_help(message)

    elif conversation_state == 'init':
        await reply_start(message, user_data)
    elif conversation_state == 'option_select':
        await reply_option_select(message, user_data)

    elif conversation_state == 'orm_weight':
        await reply_orm_weight(message, user_data)
    elif conversation_state == 'orm_reps':
        await reply_orm_reps(message, user_data)
    elif conversation_state == 'orm_sets':
        await reply_orm_sets(message, user_data)
    elif conversation_state == 'orm_type':
        await reply_orm_type(message, user_data)

    elif conversation_state == 'worker_weight':
        await reply_worker_weight(message, user_data)
    elif conversation_state == 'worker_reps':
        await reply_worker_reps(message, user_data)
    elif conversation_state == 'worker_sets':
        await reply_worker_sets(message, user_data)
    elif conversation_state == 'worker_type':
        await reply_worker_type(message, user_data)

    else:
        assert False, "Conversation state assertion"

    write_user_data(message.chat.id, user_data)


def reply_markup(buttons):
    markup = types.ReplyKeyboardMarkup()
    markup.row(*buttons)
    markup.one_time_keyboard = True
    return markup


async def reply_help(message):
    text = "*One-repetition maximum* (*one rep maximum* or *1RM*) in weight training is the maximum amount of " \
           "weight that a person can possibly lift for one repetition. One repetition maximum can be used for " \
           "determining an individual's maximum strength and is the method for determining the winner in events " \
           "such as powerlifting and weightlifting competitions. One repetition maximum is also used when " \
           "designing a resistance training program to set up the exercises with percentages based on the " \
           "one-rep max.\n\n" \
           "The 1RM can either be calculated directly using maximal testing, or indirectly using _submaximal " \
           "estimation_. \n" \
           "For example, if you can lift *60 kg* for 5 sets of 6 repetitions, you should be able to " \
           "lift *75 kg* once."

    await bot.reply_to(message, text, parse_mode="markdown")


async def reply_start(message, user_data):
    text = "Hi, I can help you calculate your *one-rep max* or *rep weight*.\n" \
           "Please select an option."
    markup = reply_markup(OPTION_LIST)

    await bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="markdown")
    user_data['conversation_state'] = 'option_select'


async def reply_option_select(message, user_data):
    if message.text.strip() in OPTION_LIST:
        option = OPTION_DICT[message.text.strip()]
        if option == 'orm':
            await reply_orm_init(message, user_data)
        elif option == 'worker':
            await reply_worker_init(message, user_data)
        else:
            assert False, "Option select assertion"
    else:
        text = "I did not understand. Please select an option."
        markup = reply_markup(OPTION_LIST)
        await bot.reply_to(message, text, reply_markup=markup)


async def reply_orm_init(message, user_data):
    text = "Enter the lifted weight"
    user_data['conversation_state'] = 'orm_weight'

    await bot.send_message(message.chat.id, text)


async def reply_orm_weight(message, user_data):
    try:
        user_data['weight'] = float(message.text.strip())
        if user_data['weight'] <= 0:
            raise ValueError
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the lifted weight (a positive float number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of reps'
    user_data['conversation_state'] = 'orm_reps'
    await bot.send_message(message.chat.id, text)


async def reply_orm_reps(message, user_data):
    try:
        user_data['reps'] = int(message.text.strip())
        if user_data['reps'] <= 0:
            raise ValueError
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of reps (a natural number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of sets'
    user_data['conversation_state'] = 'orm_sets'
    await bot.send_message(message.chat.id, text)


async def reply_orm_sets(message, user_data):
    try:
        user_data['sets'] = int(message.text.strip())
        if user_data['sets'] <= 0:
            raise ValueError
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of sets (a natural number)"
        await bot.reply_to(message, text)
        return

    text = 'Select the exercise'
    user_data['conversation_state'] = 'orm_type'
    markup = reply_markup(EXERCISE_LIST)
    await bot.send_message(message.chat.id, text, reply_markup=markup)


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

        if orm is not None:
            text += '*Your one-rep max: %d*' % int(orm)
        else:
            text += '*Your one-rep max: ambulance*'

        if user_data['reps'] > 8 or user_data['sets'] > 5:
            text += '\n\nPlease note that reps above 8 or sets above 5 might yield inaccurate results.'

        markup = reply_markup(RESTART_WORDS)
        user_data['conversation_state'] = 'init'
        del user_data['weight']
        del user_data['reps']
        del user_data['sets']

        await bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="markdown")

    else:
        text = 'I did not understand.\n'
        text += 'Please select the exercise.'
        markup = reply_markup(EXERCISE_LIST)
        await bot.reply_to(message, text, reply_markup=markup)


async def reply_worker_init(message, user_data):
    text = 'Enter your one-rep max'
    user_data['conversation_state'] = 'worker_weight'
    # await bot.reply_to(message, text)
    await bot.send_message(message.chat.id, text)


async def reply_worker_weight(message, user_data):
    try:
        user_data['orm'] = float(message.text.strip())
        if user_data['orm'] <= 0:
            raise ValueError
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the one-rep max (a positive float number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of reps'
    user_data['conversation_state'] = 'worker_reps'

    await bot.send_message(message.chat.id, text)


async def reply_worker_reps(message, user_data):
    try:
        user_data['reps'] = int(message.text.strip())
        if user_data['reps'] <= 0:
            raise ValueError
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of reps (a natural number)"
        await bot.reply_to(message, text)
        return

    text = 'Enter the number of sets'
    user_data['conversation_state'] = 'worker_sets'

    await bot.send_message(message.chat.id, text)


async def reply_worker_sets(message, user_data):
    try:
        user_data['sets'] = int(message.text.strip())
        if user_data['sets'] <= 0:
            raise ValueError
    except ValueError:
        text = "I did not understand.\n" \
               "Please enter the number of sets (a natural number)"
        await bot.reply_to(message, text)
        return

    text = 'Select the exercise'
    user_data['conversation_state'] = 'worker_type'
    markup = reply_markup(EXERCISE_LIST)

    await bot.send_message(message.chat.id, text, reply_markup=markup)


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

        if worker is not None:
            text += '*Your rep weight: %d*' % int(worker)
        else:
            text += '*Your rep weight: ambulance*'

        if user_data['reps'] > 8 or user_data['sets'] > 5:
            text += '\n\nPlease note that reps above 8 or sets above 5 might yield inaccurate results.'

        markup = reply_markup(RESTART_WORDS)
        user_data['conversation_state'] = 'init'
        del user_data['orm']
        del user_data['reps']
        del user_data['sets']

        await bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="markdown")

    else:
        text = 'I did not understand.\n'
        text += 'Please select the exercise.'
        markup = reply_markup(EXERCISE_LIST)
        await bot.reply_to(message, text, reply_markup=markup)

asyncio.run(bot.polling())
