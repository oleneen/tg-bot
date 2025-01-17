import telebot
import logging
from telebot import types
import sqlite3
import requests
import os
import requests
from mega import Mega
from dotenv import load_dotenv

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# Словарь для хранения данных пользователейа
user_data = {}

# Сообщения для бота
GREETING_MESSAGE = 'Я бот для принятия вашей оплаты и записи на проекты <b><em>модельного агенства "Happy Kids" города Екатеринбург</em></b>. Если вы неправильно выберете ответ, вы всегда можете начать заново, прописав команду /start. Если у вас возникнет вопрос или какая-то проблема, пропишете /help. Ответьте на пару вопросов, чтобы получить нужную ссылку на оплату. В каком запуске учится ваш ребенок?'
LAUNCH_QUESTION = 'Подскажите, в каком запуске учится ваш ребенок?'
PAYMENT_PERIOD_QUESTION = 'Какой период обучения вы хотите оплатить?'
NUMBER_OF_CHILDREN_QUESTION = 'Сколько ваших детей обучается в нашей школе на данный момент?'
RECEIPT_REQUEST = 'Прошу вас отправить фото-скриншот чека об оплате.'
PAYMENT_CONFIRMATION = 'Оплата принята и отправлена директору. Теперь запишитесь на проект:'
ERROR = 'Похоже, вы выбрали ответ не из списка. Давайте начнем беседу заново!'
MANY_ERRORS = 'Упс! Давайте я дам вам подробную инструкцию по пользованию нашим ботом! Прописав команду /start, вы запустите бота. Чтобы ответить на вопрос бота, нужно выбрать вариант из кнопок, которые находятся под строкой ввода сообщения. Если данного списка у вас нет, нужно нажать на кнопку, обведенную красным кружком на фото выше.'
PRINT_PAY_LINK = 'Ссылка на оплату:'
PRINT_PAY = 'Вот ваша ссылка на оплату. Введите Имя и Фамилию ребенка, за которго вносится оплата, вида: Иванов_Иван (без пробелов, только нижнее подчеркивание).'
PHOTO_REQUEST = 'Теперь пришлите мне чек об оплате в виде скриншота, я направлю его директору Марии.'
LINK_NOT_FOUND_ERROR = 'Ошибка: ссылка не найдена.'
CONNECT_WITH_CREATOR = 'Напишите моему создателю @oleneen, чтобы получить ответ на ваш вопрос. Как будете готовы начать, я буду тут, только напишите /start'
LET_PRACTICE = 'Теперь попрактикуемся, вы готовы продолжить?'

# Информация по периодам и группам
blocks = {1: '1 блок (3 месяца)', 2: '2 блока (6 месяцев)', 3: '3 блока (9 месяцев)', 4: '4 блока (12 месяцев'}
months = {1: '1 месяц', 3: '3 месяца', 6: '6 месяцeв', 9: '9 месяцев'}
groups = ['12 запуск', '13 запуск', '14 запуск', 'Проф-курс']

# Инициализация пользователя
def initialize_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "count_of_errors": 0,
            "number_of_group": "",
            "period": "",
            "ch_count": "",
            "name_of_pupil": "",
        }

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('links.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            children_count INTEGER,
            period INTEGER,
            url TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Загрузка данных в базу данных
def load_data():
    data = [
        ("12 запуск", 1, 1, "https://happykidspay.ru/pay_1/4340"),
        ("12 запуск", 2, 1, "https://happykidspay.ru/pay_1/4339"),
        ("12 запуск", 3, 1, "https://happykidspay.ru/pay_1/4346"),
        ("13 запуск", 1, 1, "https://happykidspay.ru/pay_1/5434"),
        ("13 запуск", 2, 1, "https://happykidspay.ru/pay_1/5433"),
        ("13 запуск", 3, 1, "https://happykidspay.ru/pay_1/5530"),
        ("14 запуск", 1, 1, "https://happykidspay.ru/pay_1/7530"),
        ("14 запуск", 2, 1, "https://happykidspay.ru/pay_1/7529"),
        ("14 запуск", 3, 1, "https://happykidspay.ru/pay_1/7943"),
        ("Проф-курс", 1, 1, "https://happykidspay.ru/pay_1/4351"),
        ("Проф-курс", 2, 1, "https://happykidspay.ru/pay_1/5640"),
        ("Проф-курс", 3, 1, "https://happykidspay.ru/pay_1/4357"),
        ("12 запуск", 1, 3, "https://happykidspay.ru/pay_1/4341"),
        ("12 запуск", 1, 6, "https://happykidspay.ru/pay_1/4342"),
        ("12 запуск", 1, 9, "https://happykidspay.ru/pay_1/4343"),
        ("13 запуск", 1, 3, "https://happykidspay.ru/pay_1/5525"),
        ("13 запуск", 1, 6, "https://happykidspay.ru/pay_1/5526"),
        ("13 запуск", 1, 9, "https://happykidspay.ru/pay_1/5527"),
        ("14 запуск", 1, 3, "https://happykidspay.ru/pay_1/7938"),
        ("14 запуск", 1, 6, "https://happykidspay.ru/pay_1/7939"),
        ("14 запуск", 1, 9, "https://happykidspay.ru/pay_1/7940"),
        ("Проф-курс", 1, 2, "https://happykidspay.ru/pay_1/6236"),
        ("Проф-курс", 1, 3, "https://happykidspay.ru/pay_1/7619"),
        ("Проф-курс", 1, 4, "https://happykidspay.ru/pay_1/5641"),
    ]
    conn = sqlite3.connect('links.db')
    cursor = conn.cursor()
    cursor.executemany('INSERT INTO links (group_name, children_count, period, url) VALUES (?, ?, ?, ?)', data)
    conn.commit()
    conn.close()


# Получение ссылки из базы данных
def get_link(group_name, children_count=None, period=None):
    conn = sqlite3.connect('links.db')
    cursor = conn.cursor()
    if children_count:
        cursor.execute('SELECT url FROM links WHERE group_name = ? AND children_count = ?',
                       (group_name, children_count))
    else:
        cursor.execute('SELECT url FROM links WHERE group_name = ? AND period = ?', (group_name, period))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


# Авторизация в MEGA
load_dotenv()

def connect_to_mega():
    email = os.getenv("MEGA_EMAIL")
    password = os.getenv("MEGA_PASSWORD")
    mega = Mega()
    return mega.login(email, password)


# Загрузка файла на MEGA
def upload_file_to_mega(file_path, folder_name="Receipts"):
    mega = connect_to_mega()

    # Проверяем, существует ли папка
    folder = mega.find(folder_name)
    if not folder:
        folder = mega.create_folder(folder_name)

    # Загружаем файл
    mega.upload(file_path, folder[0])
    return f"Файл '{file_path}' успешно отправлен директору! Спасибо!"



# Проверка ошибок
def check_errors(message):
    user_id = message.chat.id
    user_data[user_id]["count_of_errors"] += 1
    if user_data[user_id]["count_of_errors"] % 2 == 0:
        error(message)
    else:
        bot.send_message(message.chat.id, ERROR)
        main(message)

@bot.message_handler(commands=['help'])
def error(message):
    with open('./instruct.jpg', 'rb') as file:
        data = file.read()
    bot.send_photo(message.chat.id, data, caption=MANY_ERRORS)
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Я готов!')
    btn2 = types.KeyboardButton('У меня есть вопрос/Я кое-что не понял:(')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id, LET_PRACTICE, reply_markup=markup)
    bot.register_next_step_handler(message, error_start)


def error_start(message):
    user_answer = message.text
    if user_answer == 'Я готов!':
        main(message)
    else:
        bot.send_message(message.chat.id, CONNECT_WITH_CREATOR)

# Старт
@bot.message_handler(commands=['start'])
def main(message):
    user_id = message.chat.id
    initialize_user(user_id)
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton(groups[0])
    btn2 = types.KeyboardButton(groups[1])
    btn3 = types.KeyboardButton(groups[2])
    btn4 = types.KeyboardButton(groups[3])
    markup.row(btn1, btn2, btn3)
    markup.row(btn4)
    bot.send_message(message.chat.id, f'Здравствуйте, {message.from_user.first_name}! ' + GREETING_MESSAGE,
                     parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(message, on_click)

# Выбрать период
def on_click(message):
    user_answer = message.text
    valid_answers = groups
    user_id = message.chat.id
    if user_answer in valid_answers:
        user_data[user_id]["number_of_group"] = message.text
        markup2 = types.ReplyKeyboardMarkup()
        if message.text == groups[3]:
            btn1 = types.KeyboardButton(blocks[1])
            btn2 = types.KeyboardButton(blocks[2])
            btn3 = types.KeyboardButton(blocks[3])
            btn4 = types.KeyboardButton(blocks[4])
        else:
            btn1 = types.KeyboardButton(months[1])
            btn2 = types.KeyboardButton(months[3])
            btn3 = types.KeyboardButton(months[6])
            btn4 = types.KeyboardButton(months[9])
        markup2.row(btn1, btn2, btn3)
        markup2.row(btn4)
        bot.send_message(message.chat.id, PAYMENT_PERIOD_QUESTION, reply_markup=markup2)
        bot.register_next_step_handler(message, on_click_count)
    else:
        check_errors(message)

# Выбрать период оплаты
def on_click_count(message):
    user_answer = message.text
    user_id = message.chat.id
    markup3 = types.ReplyKeyboardMarkup()
    if user_answer in blocks.values() or user_answer in months.values():
        user_data[user_id]["period"] = user_answer
        if user_data[user_id]["period"] == months[1] or user_data[user_id]["period"] == blocks[1]:
            btn1 = types.KeyboardButton('1')
            btn2 = types.KeyboardButton('2')
            btn3 = types.KeyboardButton('3')
            markup3.row(btn1, btn2)
            markup3.row(btn3)
            bot.send_message(message.chat.id, NUMBER_OF_CHILDREN_QUESTION, reply_markup=markup3)
            bot.register_next_step_handler(message, on_click_pay)
        else:
            on_click_pay(message)
    else:
        check_errors(message)

# Выбрать кол-во детей
def on_click_pay(message):
    user_answer = message.text
    user_id = message.chat.id
    if user_answer in ['1', '2', '3']:
        user_data[user_id]["ch_count"] = int(user_answer)
        url = get_link(user_data[user_id]["number_of_group"], user_data[user_id]["ch_count"], 1)
        if url:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(PRINT_PAY_LINK, url=url))
            bot.send_message(message.chat.id, PRINT_PAY, reply_markup=markup)
            bot.register_next_step_handler(message, get_name)
        else:
            bot.send_message(message.chat.id, LINK_NOT_FOUND_ERROR)
    else:
        period = user_data[user_id]['period']
        url = get_link(user_data[user_id]["number_of_group"], None, int(period.split()[0]))
        if url:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(PRINT_PAY_LINK, url=url))
            bot.send_message(message.chat.id, PRINT_PAY, reply_markup=markup)
            bot.register_next_step_handler(message, get_name)
        else:
            bot.send_message(message.chat.id, LINK_NOT_FOUND_ERROR)
# Получить имя ребенка
def get_name(message):
    user_id = message.chat.id
    if message.text != '/start':
        bot.send_message(message.chat.id,
                         PHOTO_REQUEST)
        user_data[user_id]["name_of_pupil"] = message.text
        bot.register_next_step_handler(message, get_recipe)
    else:
        main(message)

# Отправить фото в облако
@bot.message_handler(content_types=['photo'])
def get_recipe(message):
    if message.content_type == 'photo':
        user_id = message.chat.id
        # Получаем ID самого большого фото
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)

        # Получаем путь к файлу на сервере Telegram
        file_path = file_info.file_path
        file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'
        file_name = user_data[user_id]["name_of_pupil"]+'.jpg'

        # Скачиваем файл с Telegram
        response = requests.get(file_url)
        with open(file_name, 'wb') as f:
            f.write(response.content)

        # Загружаем файл в MEGA
        try:
            upload_status = upload_file_to_mega(file_name)
            bot.send_message(message.chat.id, f"Чек успешно загружен на MEGA: {upload_status}")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка загрузки на MEGA: {str(e)}")
        finally:
            # Удаляем локальный файл после загрузки
            os.remove(file_name)
    elif message.text != '/start':
        bot.send_message(message.chat.id, 'Отправьте, пожалуйста, скриншот чека.')
    else:
        main(message)

# Для вывода ссылок
def get_all_links():
    """Функция для получения всех записей из таблицы links."""
    conn = sqlite3.connect('links.db') 
    cursor = conn.cursor()  

    cursor.execute("SELECT * FROM links")

    records = cursor.fetchall()

    conn.close()

    return records

# Удалить все ссылки из БД
def delete_all_rows():
    conn = sqlite3.connect('links.db') 
    cursor = conn.cursor()  
    cursor.execute("DELETE FROM links") 
    conn.commit()  
    conn.close()  
    print("Все строки из таблицы links успешно удалены.")

# Запуск
if __name__ == "__main__":
    init_db()
    #delete_all_rows()
    #load_data()
    all_links = get_all_links()
    for record in all_links:
        print(record)
    bot.infinity_polling()



