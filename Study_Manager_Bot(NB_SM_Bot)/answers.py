def callback_error():
    text = '<i>Сожалею, произошла ошибка, мы работаем над этим. Попробуйте прописать /start и попробовать еще раз</i>'
    return text


def add_time_answer():
    text = '<i>Сожалею, произошла ошибка. Проверьте корректность введенной информации</i>'
    return text


def start_answer():
    text = ('<b>Этот бот создан, чтобы контролировать время учебы и формировать отчеты по пройденным занятиям\n'
            'Для получение подробной информации о командах бота введите /help</b>')
    return text


def help_answer():
    text = ('<i>'
            '/start - запускает бота и выводит начальное меню действий\n'
            '\n'
            '/add_time - позволяет добавить время вашего обучения в статистику.\n'
            'Для этого введите время в формате:\n'
            '<b>/add_time start: HH:MM:SS YYYY-MM-DD stop: HH:MM:SS YYYY-MM-DD</b>'
            '</i>')
    return text


def success_answer():
    text = '<i>Действие успешно выполнено</i>'
    return text


def report_error():
    text = '<i>Данных нет</i>'
    return text


def print_error():
    import traceback
    print('Ошибка:\n', traceback.format_exc())
