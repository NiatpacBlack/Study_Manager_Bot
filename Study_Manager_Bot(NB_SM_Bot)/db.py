import sqlite3
from datetime import datetime


def create_all_table():
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    # создает все рабочие таблицы, если те еще не созданы или были удалены внезапно
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS start_end_table(
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INT,
        start_time INT,
        end_time INT    
        );'''
                   )
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pause_unpause_table(
        pause_unpause_table_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INT,
        pause_time INT,
        unpause_time INT,
        FOREIGN KEY (session_id) REFERENCES start_end_table (session_id) ON DELETE CASCADE
        );'''
                   )
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS union_table(
        session_id INT,
        chat_id INT,
        start_time INT,
        end_time INT,
        pause_unpause_id INT,
        pause_time INT, 
        unpause_time INT
        );'''
                   )
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS total_time_table(
        session_id INT,
        chat_id INT,
        total_work_time INT    
        );
        '''
                   )
    study_time_db.commit()


# добавление данных в таблицу
def insert(table: str, **kwargs):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()
    columns = ", ".join(kwargs.keys())
    values = ", ".join(kwargs.values())
    cursor.execute(f'''
            INSERT INTO {table} 
            ({columns}) 
            VALUES ({values});
            '''
                   )
    study_time_db.commit()


# удаление таблицы
def delete_table(table: str):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()
    cursor.execute(f'DELETE FROM {table}')
    study_time_db.commit()


# отчет об общем времени в текущем дне
def report_today(chat_id: str):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    day_now_unix = int((datetime.strptime(f'{datetime.now().date()}', '%Y-%m-%d')).timestamp())
    day_next_unix = day_now_unix + 86400

    cursor.execute(f'''
            SELECT SUM(total_work_time)
            FROM total_time_table
                INNER JOIN union_table USING(chat_id, session_id)
            WHERE chat_id = {chat_id} AND start_time > {day_now_unix} AND start_time < {day_next_unix};      
            ''')
    read_table = cursor.fetchall()
    return int(read_table[0][0])


# отчет об общем времени в текущей неделе
def report_week(chat_id: str):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    now_weekday = datetime.now().date().weekday()
    day_now_unix = int((datetime.strptime(f'{datetime.now().date()}', '%Y-%m-%d')).timestamp())

    for day in range(1, 8):
        if now_weekday == day:
            start_week_unix = day_now_unix - (86400 * day)
            end_week_unix = start_week_unix + (86400 * 7)

    cursor.execute(f'''
            SELECT SUM(total_work_time)
            FROM union_table
                LEFT JOIN total_time_table USING(chat_id, session_id)
            WHERE chat_id = {chat_id} AND start_time > {start_week_unix} AND start_time < {end_week_unix};      
            ''')
    read_table = cursor.fetchall()
    return int(read_table[0][0])


# отчет об общем времени в текущем месяце
def report_month(chat_id: str):
    import calendar
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    day_now = datetime.now().date().day
    day_now_unix = int((datetime.strptime(f'{datetime.now().date()}', '%Y-%m-%d')).timestamp())
    month_days = calendar.mdays[datetime.now().date().month]

    for day in range(1, month_days + 1):
        if day_now == day:
            start_month_unix = day_now_unix - (86400 * day)
            end_month_unix = start_month_unix + (86400 * month_days)

    cursor.execute(f'''
                SELECT SUM(total_work_time)
                FROM total_time_table
                    INNER JOIN union_table USING(chat_id, session_id)
                WHERE chat_id = {chat_id} AND start_time > {start_month_unix} AND start_time < {end_month_unix};      
                ''')
    read_table = cursor.fetchall()
    return int(read_table[0][0])


# отчет об общем времени за все время
def report_all_time(chat_id: str):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()
    cursor.execute(f'''
            SELECT SUM(total_work_time)
            FROM union_table
                LEFT JOIN total_time_table USING(chat_id, session_id)
            WHERE chat_id = {chat_id};      
            ''')
    read_table = cursor.fetchall()
    return int(read_table[0][0])


def get_session_id(chat_id: int, start_time: int):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    cursor.execute(f'''
                        SELECT session_id
                        FROM start_end_table
                        WHERE chat_id == {chat_id} AND start_time == {start_time}
                ''')
    read_start_end_table = cursor.fetchall()
    return int(read_start_end_table[0][0])


def set_unpause_time(unpause_time: int, session_id: int):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    cursor.execute(f'''
                        UPDATE pause_unpause_table
                        SET unpause_time = {unpause_time}
                        WHERE session_id == {session_id} AND unpause_time is Null;
                    ''')
    study_time_db.commit()


def set_end_time(end_time: int, session_id: int):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    cursor.execute(f'''
                        UPDATE start_end_table SET end_time = {end_time}
                        WHERE session_id == {session_id}
                        ''')
    study_time_db.commit()


# вставляет в таблицу union_table объединенные таблицы start_end и pause_unpause, и меняет null на end_time
def reinsert_union_table():
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()
    cursor.execute('''
                        INSERT INTO union_table
                        SELECT *
                        FROM start_end_table
                        LEFT JOIN pause_unpause_table USING(session_id);
                        ''')
    cursor.execute('''
                        UPDATE union_table
                        SET unpause_time = end_time
                        WHERE pause_time is not Null AND unpause_time is Null;
                        ''')
    study_time_db.commit()


# получаем количество секунд учебы за все время, для аккаунта к которому относится id сессии
def get_total_work_time(session_id: int):
    study_time_db = sqlite3.connect('study_time.db')
    cursor = study_time_db.cursor()

    cursor.execute(f'''
                        SELECT
                        CASE
                            WHEN SUM(unpause_time) - SUM(pause_time) is Null
                                THEN (end_time - start_time) - 0
                            ELSE (end_time - start_time) - (SUM(unpause_time) - SUM(pause_time))
                        END AS general_pause_time
                        FROM union_table
                        WHERE session_id = {session_id}
                        GROUP BY session_id, chat_id, start_time, end_time;
                        ''')
    read_text_table = cursor.fetchall()
    return read_text_table[0][0]
