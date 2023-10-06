import telebot
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta, date
import sqlite3
import schedule
import time
import threading
import os
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("STARTHELPERBOT_TOKEN"))

def meteo(chat_id):
    data = {}
    city_id = "33464"
    try:
        url = "https://www.meteo.gov.ua/_/m/prognoz.js"
        headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        data.update(response.json())

        current_datetime = datetime.now().date()
        tomorrow = current_datetime + timedelta(days=1)
        after_tomorrow = current_datetime + timedelta(days=2)
        current_datetime = str(current_datetime)
        tomorrow = str(tomorrow)
        after_tomorrow = str(after_tomorrow)

        bot.send_message(chat_id,
                         f"<b><u>{convert_date(current_datetime)}</u></b>\n\n&#127774;Вдень температура від "
                         f"{data[city_id][current_datetime]['T_ID_F']} до {data[city_id][current_datetime]['T_ID_T']}, "
                         f"{data[city_id][current_datetime]['HM']}, {data[city_id][current_datetime]['O_D']}. Вітер "
                         f"{data[city_id][current_datetime]['WD_S']} м/с.\n\n&#127770;Вночі температура від "
                         f"{data[city_id][tomorrow]['T_IN_F']} до {data[city_id][tomorrow]['T_IN_T']}, "
                         f"{data[city_id][tomorrow]['HM']}, {data[city_id][tomorrow]['O_N']}. Вітер "
                         f"{data[city_id][tomorrow]['WN_S']} м/с.\n\n&#127749;Схід сонця в {data[city_id][current_datetime]['SR']}, "
                         f"захід в {data[city_id][current_datetime]['SS']}.\n\n<b><u>{convert_date(tomorrow)}"
                         f"</u></b>\n\n&#127774;Вдень температура від "
                         f"{data[city_id][tomorrow]['T_ID_F']} до {data[city_id][tomorrow]['T_ID_T']}, "
                         f"{data[city_id][tomorrow]['HM']}, {data[city_id][tomorrow]['O_D']}. Вітер "
                         f"{data[city_id][tomorrow]['WD_S']} м/с.\n\n&#127770;Вночі температура від "
                         f"{data[city_id][after_tomorrow]['T_IN_F']} до {data[city_id][after_tomorrow]['T_IN_T']}, "
                         f"{data[city_id][after_tomorrow]['HM']}, {data[city_id][after_tomorrow]['O_N']}. Вітер "
                         f"{data[city_id][after_tomorrow]['WN_S']} м/с.", parse_mode="HTML")
    except Exception as e:
        print("Ошибка URL: {e}")

#Функция получает дату со временем и возвращает только дату
def date_formated(date_note):
    date_note = date_note[:10]
    date_format = datetime.strptime(date_note, '%Y-%m-%d')
    new_date = date_format.strftime('%d.%m.%Y')
    return new_date

#Функция получает дату заметки и выполняет проверку, не просрочена ли заметка
def print_notes(date_note):
    date_note = date_note[:10]
    date_format = datetime.strptime(date_note, '%Y-%m-%d')
    today = datetime.today()
    date_format = date_format.date()
    today = today.date()
    tomorrow = today + timedelta(days=1)
    return (date_format == today or date_format == tomorrow)

#Функция возвращает список текущих дел на два дня
def note(chat_id):
    table_name = f"id_{chat_id}"
    try:
        conn = sqlite3.connect("mydatabase.db")
        cursor = conn.cursor()

        cursor.execute(f"SELECT date, note FROM {table_name}")

        rows = cursor.fetchall()
    except Exception as e:
        print(f"Ошибка SQL: {e}")

    message_send = True
    notes = ""
    for row in rows:
        date, note = row
        if print_notes(date):
            date = date_formated(date)
            notes += date + " " + note + "\n\n"
            message_send = False

    if message_send:
        bot.send_message(chat_id, "Поточні справи відсутні.")

    else:
        bot.send_message(chat_id, notes)

    conn.close()

#Функция получает номер месяца и возвращает текстовое название
def convert_date(data):
    new_data = data.split("-")
    month = {"01": "січня",
             "02": "лютого",
             "03": "березня",
             "04": "квітня",
             "05": "травня",
             "06": "червня",
             "07": "липня",
             "08": "серпня",
             "09": "вересня",
             "10": "жовтня",
             "11": "листопада",
             "12": "грудня"}

    return (new_data[2] + " " + month[new_data[1]])

#Новый запуск бота и первое сообщение
@bot.message_handler(commands=['start'])
def start(message):
    table_name = f"id_{message.chat.id}"
    try:
        conn = sqlite3.connect("mydatabase.db")
        cursor = conn.cursor()

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table_name}
                                      (date DATE, note TEXT)
                                   """)
        conn.close()
    except Exception as e:
        print(f"Ошибка SQL: {e}")

    bot.send_message(message.chat.id, "Цей бот кожного ранку сповіщає про поточні справи, які були додані "
                                      "в бота, а також про погоду на два дні. \n\nЩоб додати нову справу, "
                                      "виберіть команду /add_note із меню. \nКоманда /meteo надасть актуальний "
                                      "прогноз погоди на 2 дні. \nЩоб отримати список поточних справ на 2 дні, "
                                      "введіть команду /note")

#Команда для получения текущей погоды на два дня
@bot.message_handler(commands=["meteo"])
def check_meteo(message):
    data = {}
    city_id = "33464"

    try:
        url = "https://www.meteo.gov.ua/_/m/prognoz.js"
        headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        data.update(response.json())

        current_datetime = datetime.now().date()
        tomorrow = current_datetime + timedelta(days=1)
        after_tomorrow = current_datetime + timedelta(days=2)
        current_datetime = str(current_datetime)
        tomorrow = str(tomorrow)
        after_tomorrow = str(after_tomorrow)


        bot.send_message(message.chat.id,
                     f"<b><u>{convert_date(current_datetime)}</u></b>\n\n&#127774;Вдень температура від "
                     f"{data[city_id][current_datetime]['T_ID_F']} до {data[city_id][current_datetime]['T_ID_T']}, "
                     f"{data[city_id][current_datetime]['HM']}, {data[city_id][current_datetime]['O_D']}. Вітер "
                     f"{data[city_id][current_datetime]['WD_S']} м/с.\n\n&#127770;Вночі температура від "
                     f"{data[city_id][tomorrow]['T_IN_F']} до {data[city_id][tomorrow]['T_IN_T']}, "
                     f"{data[city_id][tomorrow]['HM']}, {data[city_id][tomorrow]['O_N']}. Вітер "
                     f"{data[city_id][tomorrow]['WN_S']} м/с.\n\n&#127749;Схід сонця в {data[city_id][current_datetime]['SR']}, "
                     f"захід в {data[city_id][current_datetime]['SS']}.\n\n<b><u>{convert_date(tomorrow)}"
                     f"</u></b>\n\n&#127774;Вдень температура від "
                     f"{data[city_id][tomorrow]['T_ID_F']} до {data[city_id][tomorrow]['T_ID_T']}, "
                     f"{data[city_id][tomorrow]['HM']}, {data[city_id][tomorrow]['O_D']}. Вітер "
                     f"{data[city_id][tomorrow]['WD_S']} м/с.\n\n&#127770;Вночі температура від "
                     f"{data[city_id][after_tomorrow]['T_IN_F']} до {data[city_id][after_tomorrow]['T_IN_T']}, "
                     f"{data[city_id][after_tomorrow]['HM']}, {data[city_id][after_tomorrow]['O_N']}. Вітер "
                     f"{data[city_id][after_tomorrow]['WN_S']} м/с.", parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка URL: {e}")

#Команда для добавления новой заметки в локальную базу данных
@bot.message_handler(commands=["add_note"])
def add_note(message):
    bot.send_message(message.chat.id, "Додайте нову справу в форматі [01.01.2023 Опис справи]")

    #Получение новой заметки и проверка ее на корректность
    @bot.message_handler(content_types=["text"])
    def check_data(message):
        note = message.text
        try:
            note_parts = note.split(" ", 1)
            if len(note_parts) >=2:
                date = datetime.strptime(note_parts[0], '%d.%m.%Y')
                text = note_parts[1]

            table_name = f"id_{message.chat.id}"
            conn = sqlite3.connect("mydatabase.db")
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {table_name} (date, note) VALUES (?, ?)", (date, text))

            # Сохраняем изменения в базе данных
            conn.commit()
            conn.close()

            bot.send_message(message.chat.id, "Справа додана")

        except:
            bot.send_message(message.chat.id, "Помилка вводу. Вірний формат (без квадратних дужок) [01.01.2023 Опис справи]")

#Команда для получения текущего списка задач из локальной базы
@bot.message_handler(commands=["note"])
def print_note(message):
    table_name = f"id_{message.chat.id}"
    try:
        conn = sqlite3.connect("mydatabase.db")
        cursor = conn.cursor()

        cursor.execute(f"SELECT date, note FROM {table_name}")

        rows = cursor.fetchall()
    except Exception as e:
        print(f"Ошибка SQL: {e}")

    message_send = True
    notes = ""
    for row in rows:
        date, note = row
        if print_notes(date):
            date = date_formated(date)
            notes += date + " " + note + "\n\n"
            message_send = False

    if message_send:
        bot.send_message(message.chat.id, "Поточні справи відсутні.")

    else:
        bot.send_message(message.chat.id, notes)

    conn.close()

#Функция отправляет пользователям текущую погоду и список задач на два ближайших дня.
def check_everyday():
    try:
        conn = sqlite3.connect("mydatabase.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Ошибка SQL: {e}")

    for table in tables:
        table_name = int(table[0][3:])
        meteo(table_name)
        note(table_name)

#Ежедневное выполнение задачи
schedule.every().day.at("05:00").do(check_everyday)

#Запуск задачи
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

#Запуск бота
def run_polling():
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")

#Создание двух потоков
schedule_thread = threading.Thread(target=run_schedule)
polling_thread = threading.Thread(target=run_polling)

#Запуск двух потоков
schedule_thread.start()
polling_thread.start()