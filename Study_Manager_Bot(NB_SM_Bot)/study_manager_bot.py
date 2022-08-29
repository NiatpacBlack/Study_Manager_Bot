import config
import db
import answers

from time import time
from telebot import types, TeleBot
from flask import Flask, abort, request, Response
from datetime import datetime

app = Flask(__name__)
bot = TeleBot(config.token)

""" В эту переменную будет заноситься номер текущей session_id из базы данных """
id_session = 0

""" В эту переменную будет заноситься последнее отправленное сообщение с кнопками """
last_message = ''

db.create_all_table()


def create_start_keyboard():
    """ Создает кнопки выпадающие при старте бота """

    start_keyboard = types.InlineKeyboardMarkup()
    begin_btn = types.InlineKeyboardButton(text="Начать учебу", callback_data='begin')
    report_btn = types.InlineKeyboardButton(text="Посмотреть отчет по учебе", callback_data='reports')
    start_keyboard.add(begin_btn)
    start_keyboard.add(report_btn)
    return start_keyboard


def create_mid_keyboard():
    """ Создает кнопки выпадающие при начале учебы """

    start_mid_keyboard = types.InlineKeyboardMarkup()
    pause_btn = types.InlineKeyboardButton(text="Приостановить учебу", callback_data='pause')
    end_btn = types.InlineKeyboardButton(text="Закончить учебу", callback_data='end')
    start_mid_keyboard.add(pause_btn)
    start_mid_keyboard.add(end_btn)
    return start_mid_keyboard


def create_pause_keyboard():
    """ Создает кнопки выпадающие при постановке на паузу """

    start_pause_keyboard = types.InlineKeyboardMarkup()
    unpause_btn = types.InlineKeyboardButton(text="Возобновить учебу", callback_data='unpause')
    end_btn = types.InlineKeyboardButton(text="Закончить учебу", callback_data='end')
    start_pause_keyboard.add(unpause_btn)
    start_pause_keyboard.add(end_btn)
    return start_pause_keyboard


def create_reports_keyboard():
    """ Создает кнопки выпадающие при переходе к отчетам """

    reports_keyboard = types.InlineKeyboardMarkup()
    report_1_btn = types.InlineKeyboardButton(text="Отчет за текущий день", callback_data='report_1')
    report_2_btn = types.InlineKeyboardButton(text="Отчет за текущую неделю", callback_data='report_2')
    report_3_btn = types.InlineKeyboardButton(text="Отчет за текущий месяц", callback_data='report_3')
    report_4_btn = types.InlineKeyboardButton(text="Отчет за все время", callback_data='report_4')
    report_5_btn = types.InlineKeyboardButton(text="Отчет за прошлую неделю", callback_data='report_5')
    reports_keyboard.add(report_1_btn)
    reports_keyboard.add(report_2_btn)
    reports_keyboard.add(report_3_btn)
    reports_keyboard.add(report_4_btn)
    reports_keyboard.add(report_5_btn)
    return reports_keyboard


def unix_to_date_conv(unix_date: int):
    """ Конвертирует unix формат в читаемую дату """

    normal_date = datetime.fromtimestamp(unix_date).strftime("%H:%M:%S %Y-%m-%d")
    return normal_date


def date_to_unix_conv(normal_date: str):
    """ Конвертирует строку с читаемой датой в unix формат """

    unix_date = int((datetime.strptime(f'{normal_date}', '%H:%M:%S %Y-%m-%d')).timestamp())
    return unix_date


def sec_to_hours_conv(seconds: int):
    """ Конвертирует секунды в часы, минуты, секунды """

    hours = str(seconds // 3600)
    if len(hours) == 1:
        hours = '0' + hours
    minutes = str((seconds % 3600) // 60)
    if len(minutes) == 1:
        minutes = '0' + minutes
    seconds = str((seconds % 3600) % 60)
    if len(seconds) == 1:
        seconds = '0' + seconds
    return f"{hours}:{minutes}:{seconds}"


@app.route('/', methods=['POST', 'GET'])
def index():
    """ Обработка полученных веб-хуков """

    if request.headers.get('content-type') == 'application/json':
        update = types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)
    if request.method == 'POST':
        return Response('ok', status=200)
    else:
        return ''


@bot.message_handler(commands=['start'])
def start_bot(message):
    """ Отрисовка стартовой клавиатуры и стартового сообщения """

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
    """ Добавление введенных даты и времени в таблицу start_end_table и общего времени в таблицу total_time_table """

    list_message_words = message.text.split()
    try:
        """ Проверка на соответствие шаблону ввода даты """
        if list_message_words.index('start:') == 1 and list_message_words.index('stop:') == 4:
            start_time_unix = date_to_unix_conv(' '.join(list_message_words[2:4]))
            end_time_unix = date_to_unix_conv(' '.join(list_message_words[5:]))

            """ Добавление времени начала и конца учебы в таблицу """
            db.insert(
                'start_end_table',
                chat_id=str(message.chat.id),
                start_time=str(start_time_unix),
                end_time=str(end_time_unix)
            )

            """ Перезагрузка таблицы union_table, для вычисления общего времени """
            session_id = db.get_session_id(message.chat.id, start_time_unix)
            db.delete_table('union_table')
            db.reinsert_union_table()
            total_work_time = db.get_total_work_time(session_id)

            """ Добавление общего времени учебы в таблицу """
            db.insert(
                'total_time_table',
                session_id=str(session_id),
                chat_id=str(message.chat.id),
                total_work_time=str(total_work_time)
            )

            """ Ответ пользователю об успехе """
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
    """ Отправка сообщения с информацией о командах бота пользователю """

    bot.send_message(
        message.chat.id,
        answers.help_answer(),
        parse_mode='HTML'
    )


@bot.callback_query_handler(func=lambda callback: True)
def callback_inline(callback):
    """ Обработка всех полученных callback команд """

    global id_session, last_message
    try:

        """ Обработка нажатия отчетных кнопок """
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
                    text=f'За сегодня вы занимались {sec_to_hours_conv(total_time_today)}'
                )

            if callback.data == 'report_2':
                total_time_week = db.report_week(str(callback.message.chat.id))
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За эту неделю вы занимались {sec_to_hours_conv(total_time_week)}'
                )

            if callback.data == 'report_3':
                total_time_month = db.report_month(str(callback.message.chat.id))
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За этот месяц вы занимались {sec_to_hours_conv(total_time_month)}'
                )

            if callback.data == 'report_4':
                total_time = db.report_all_time(str(callback.message.chat.id))
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За все время вы занимались {sec_to_hours_conv(total_time)}'
                )

            if callback.data == 'report_5':
                total_time_last_week = db.report_week(str(callback.message.chat.id), week='last')
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f'За прошлую неделю вы занимались {sec_to_hours_conv(total_time_last_week)}'
                )
        except TypeError:
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=answers.report_error(),
                parse_mode='HTML'
            )
            answers.print_error()

        """ Обработка нажатий основных кнопок """
        if callback.data == 'begin':
            db.insert('start_end_table', chat_id=str(callback.message.chat.id), start_time=str(int(time())))

            id_session = db.get_session_id(callback.message.chat.id, int(time()))
            print(f' Id сессии равен: {id_session}')

            bot.delete_message(callback.message.chat.id, last_message.id)
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=f'Учеба начата в {unix_to_date_conv(int(time()))}',
            )
            last_message = bot.send_message(
                chat_id=callback.message.chat.id,
                text='Выберите действие:',
                reply_markup=create_mid_keyboard()
            )
        if callback.data == 'pause':
            db.insert(
                'pause_unpause_table',
                session_id=str(id_session),
                pause_time=str(int(time()))
            )

            bot.delete_message(callback.message.chat.id, last_message.id)
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=f'Учеба приостановлена в {unix_to_date_conv(int(time()))}',
            )
            last_message = bot.send_message(
                chat_id=callback.message.chat.id,
                text='Выберите действие:',
                reply_markup=create_pause_keyboard()
            )
        if callback.data == 'unpause':
            db.set_unpause_time(int(time()), id_session)

            bot.delete_message(callback.message.chat.id, last_message.id)
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=f'Учеба возобновлена в {unix_to_date_conv(int(time()))}',
            )
            last_message = bot.send_message(
                chat_id=callback.message.chat.id,
                text='Выберите действие:',
                reply_markup=create_mid_keyboard()
            )
        if callback.data == 'end':
            db.set_end_time(int(time()), id_session)
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
                text=f'Учеба закончена в {unix_to_date_conv(int(time()))}\n'
                     f'Время учебы {sec_to_hours_conv(total_work_time)}',
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
