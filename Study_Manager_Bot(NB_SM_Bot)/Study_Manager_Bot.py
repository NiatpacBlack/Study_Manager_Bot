import config
import db
import answers
import telebot
import flask
import time

from telebot import types
from flask import Flask, request, Response
from datetime import datetime

app = Flask(__name__)
bot = telebot.TeleBot(config.token)

id_session = 0
last_message = ''

db.create_all_table()


def create_start_keyboard():
    start_keyboard = types.InlineKeyboardMarkup()
    begin_btn = types.InlineKeyboardButton(text="Начать учебу", callback_data='begin')
    report_btn = types.InlineKeyboardButton(text="Посмотреть отчет по учебе", callback_data='reports')
    start_keyboard.add(begin_btn)
    start_keyboard.add(report_btn)
    return start_keyboard


def create_mid_keyboard():
    start_mid_keyboard = types.InlineKeyboardMarkup()
    pause_btn = types.InlineKeyboardButton(text="Приостановить учебу", callback_data='pause')
    end_btn = types.InlineKeyboardButton(text="Закончить учебу", callback_data='end')
    start_mid_keyboard.add(pause_btn)
    start_mid_keyboard.add(end_btn)
    return start_mid_keyboard


def create_pause_keyboard():
    start_pause_keyboard = types.InlineKeyboardMarkup()
    unpause_btn = types.InlineKeyboardButton(text="Возобновить учебу", callback_data='unpause')
    end_btn = types.InlineKeyboardButton(text="Закончить учебу", callback_data='end')
    start_pause_keyboard.add(unpause_btn)
    start_pause_keyboard.add(end_btn)
    return start_pause_keyboard


def create_reports_keyboard():
    reports_keyboard = types.InlineKeyboardMarkup()
    report_1_btn = types.InlineKeyboardButton(text="Отчет за текущий день", callback_data='report_1')
    report_2_btn = types.InlineKeyboardButton(text="Отчет за текущую неделю", callback_data='report_2')
    report_3_btn = types.InlineKeyboardButton(text="Отчет за текущий месяц", callback_data='report_3')
    report_4_btn = types.InlineKeyboardButton(text="Отчет за все время", callback_data='report_4')
    reports_keyboard.add(report_1_btn)
    reports_keyboard.add(report_2_btn)
    reports_keyboard.add(report_3_btn)
    reports_keyboard.add(report_4_btn)
    return reports_keyboard


def date_translation(unix_date: int):
    return datetime.fromtimestamp(unix_date).strftime("%H:%M:%S %Y-%m-%d")


def time_translation(unix_date: int):
    return datetime.utcfromtimestamp(unix_date).strftime("%H:%M:%S")


def unix_translation(normal_date: str):
    unix_date = int((datetime.strptime(f'{normal_date}', '%H:%M:%S %Y-%m-%d')).timestamp())
    return unix_date


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
    if request.method == 'POST':
        return Response('ok', status=200)
    else:
        return ''


@bot.message_handler(commands=['start'])
def start_bot(message):
    global last_message
    start_keyboard = create_start_keyboard()
    last_message = bot.send_message(
        chat_id=message.chat.id,
        text=answers.start_answer(),
        parse_mode='HTML',
        reply_markup=start_keyboard
    )


@bot.message_handler(commands=['add_time'])
def add_time_bot(message):
    list_message_words = message.text.split()
    try:
        if list_message_words.index('start:') == 1 and list_message_words.index('stop:') == 4:
            start_time_unix = unix_translation(' '.join(list_message_words[2:4]))
            end_time_unix = unix_translation(' '.join(list_message_words[5:]))
            db.insert('start_end_table',
                      chat_id=str(message.chat.id),
                      start_time=str(start_time_unix),
                      end_time=str(end_time_unix))
            id_session = db.get_session_id(message.chat.id, start_time_unix)
            db.delete_table('union_table')
            db.reinsert_union_table()
            total_work_time = db.get_total_work_time(id_session)
            db.insert('total_time_table',
                      session_id=str(id_session),
                      chat_id=str(message.chat.id),
                      total_work_time=str(total_work_time))
            bot.send_message(
                message.chat.id,
                answers.success_answer(),
                parse_mode='HTML'
            )
    except ValueError:
        bot.send_message(
            message.chat.id,
            answers.add_time_answer(),
            parse_mode='HTML'
        )
        answers.print_error()


@bot.message_handler(commands=['help'])
def help_bot(message):
    bot.send_message(
        message.chat.id,
        answers.help_answer(),
        parse_mode='HTML'
    )


@bot.callback_query_handler(func=lambda callback: True)
def callback_inline(callback):
    global id_session, last_message
    try:
        try:
            if callback.data == 'reports':
                bot.delete_message(callback.message.chat.id, last_message.id)
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text='Выберите действие',
                    reply_markup=create_reports_keyboard()
                )

            if callback.data == 'report_1':
                total_time_today = db.report_today(str(callback.message.chat.id))
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За сегодня вы занимались {time_translation(total_time_today)}'
                )
            if callback.data == 'report_2':
                total_time_week = db.report_week(str(callback.message.chat.id))
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За эту неделю вы занимались {time_translation(total_time_week)}'
                )
            if callback.data == 'report_3':
                total_time_month = db.report_month(str(callback.message.chat.id))
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За этот месяц вы занимались {time_translation(total_time_month)}'
                )
            if callback.data == 'report_4':
                total_time = db.report_all_time(str(callback.message.chat.id))
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За все время вы занимались {time_translation(total_time)}'
                )
        except TypeError:
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=answers.report_error(),
                parse_mode='HTML'
            )
            answers.print_error()

        if callback.data == 'begin':
            db.insert('start_end_table', chat_id=str(callback.message.chat.id), start_time=str(int(time.time())))

            id_session = db.get_session_id(callback.message.chat.id, int(time.time()))
            print(f' Id сессии равен: {id_session}')

            bot.delete_message(callback.message.chat.id, last_message.id)
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=f'Учеба начата в {date_translation(int(time.time()))}',
            )
            last_message = bot.send_message(
                chat_id=callback.message.chat.id,
                text='Выберите действие:',
                reply_markup=create_mid_keyboard()
            )
        if callback.data == 'pause':
            db.insert('pause_unpause_table', session_id=str(id_session), pause_time=str(int(time.time())))

            bot.delete_message(callback.message.chat.id, last_message.id)
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=f'Учеба приостановлена в {date_translation(int(time.time()))}',
            )
            last_message = bot.send_message(
                chat_id=callback.message.chat.id,
                text='Выберите действие:',
                reply_markup=create_pause_keyboard()
            )
        if callback.data == 'unpause':
            db.set_unpause_time(int(time.time()), id_session)

            bot.delete_message(callback.message.chat.id, last_message.id)
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=f'Учеба возобновлена в {date_translation(int(time.time()))}',
            )
            last_message = bot.send_message(
                chat_id=callback.message.chat.id,
                text='Выберите действие:',
                reply_markup=create_mid_keyboard()
            )
        if callback.data == 'end':
            db.set_end_time(int(time.time()), id_session)
            db.delete_table('union_table')
            db.reinsert_union_table()
            total_work_time = db.get_total_work_time(id_session)
            db.insert('total_time_table',
                      session_id=str(id_session),
                      chat_id=str(callback.message.chat.id),
                      total_work_time=str(total_work_time))

            bot.delete_message(callback.message.chat.id, last_message.id)
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=f'Учеба закончена в {date_translation(int(time.time()))}\n'
                     f'Время учебы {time_translation(total_work_time)}',
            )
    except:
        bot.send_message(
            chat_id=callback.message.chat.id,
            text=answers.callback_error(),
            parse_mode='HTML'
        )
        answers.print_error()


if __name__ == '__main__':
    app.run()
