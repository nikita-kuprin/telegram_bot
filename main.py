# coding=utf-8
# Импортируем необходимые классы.
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Импортируем необходимую библиотеку для работы с API
import requests

# Импортируем необходимую библиотеку для создания хешированного пароля
from werkzeug.security import generate_password_hash

# Импортируем все необходимое для работы с базой данной
from data import db_session
from data.users import User

# Импортируем random для генерации случайных чисел
from random import randint

# Инициализация базы данных
db_session.global_init("db/blogs.sqlite")

# Создаем пользователя для регистрации и дальнейшего отправления его в базу данных
user = User()


# Функция для установки хешированного пароля при регистрации
def set_password(self, password):
    self.hashed_password = generate_password_hash(password)


# Функция для проверки возраста, введенного пользователем
# если все проверки завершены - функция отправит  False
# если не все - функция отправит сообщение о ошибке и True,
# тем самым заставляю вводить пользователя свой возраст ещё раз
def age_verification(update, age):
    try:
        # первая проверка направлена на то, чтобы проверить
        # ввел ли пользователь число или нет
        # не число вызовет ошибку
        int(age)
        # вторая проверка на отрицательный возраст
        if age < 0:
            update.message.reply_text("Введите неотрицательное число!")
            return True
        return False

    except ValueError:
        update.message.reply_text("Введите целое число!")
        return True


# начало регистрации пользователя
def registration(update, context):
    update.message.reply_text("Какое у Вас имя?")
    return 1
    # Следующее текстовое сообщение будет обработано
    # обработчиком states[1]


# Команда для начала общения с ботом
def start(update, context):
    # создание клавиатуры
    reply_keyboard = [["/registration"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    # передаем клавиатуру в качестве параметра пользователю
    update.message.reply_text("Привет! Я бот. Давайте познакомимся поближе. Для этого пройдите анкету",
                              reply_markup=markup)


# Команда для получения команд бота
def help(update, context):
    update.message.reply_text(
        "Мои команды:"
    )
    update.message.reply_text(
        "1)🦮 /dog_photo - случайное фото собачки всегда поднимет настроение :3"
    )
    update.message.reply_text(
        "2)😸 /cat_photo - случайное фото кота. Тоже приятно"
    )
    update.message.reply_text(
        "3)⏰ /set <время> - поставить таймер на любое количество секунд,"
        " чтобы удалить таймер - напиши мне /unset"
    )
    update.message.reply_text(
        "4)🗺 /geocoder <название города> - показать карту местности города"
    )
    update.message.reply_text(
        "5)🌡 /weather <название города транслитом> - показать погоду в вашем городе"
    )
    update.message.reply_text(
        '6)🔢 /fact_random_number - получение факта о случайном числе'
    )
    update.message.reply_text(
        '7)🔢 /fact_my_number <целое число> - получение факта о вашем числе'
    )


def stop(update, context):
    update.message.reply_text(
        "Анкетирование приостановлено. Данные не сохранены."
    )
    update.message.reply_text(
        " Для новой регистрации отправьте мне /registration."
    )


# Первый вопрос для регистрации (имя)
def first_answer(update, context):
    # Это ответ на первый вопрос.
    name = update.message.text
    user.name = name
    update.message.reply_text("Какое красивое имя!")
    update.message.reply_text("А где Вы живёте?🏙")
    return 2
    # Следующее текстовое сообщение будет обработано
    # обработчиком states[2]


# Второй вопрос для регистрации (город)
def second_answer(update, context):
    # Это ответ на второй вопрос.
    city = update.message.text
    user.city = city
    update.message.reply_text("Сколько Вам лет?")
    return 3
    # Следующее текстовое сообщение будет обработано
    # обработчиком states[3]


# Третий вопрос для регистрации (возраст)
def third_answer(update, context):
    # Это ответ на третий вопрос.
    age = update.message.text
    flag = age_verification(update, age)
    if flag:
        return 3
    user.age = age
    update.message.reply_text("Придумайте пароль")
    return 4


# Четвертый вопрос для регистрации (пароль)
def fourth_answer(update, context):
    # Это ответ на четвертый вопрос.
    password = update.message.text
    # хэширование пароля
    user.password = generate_password_hash(password)
    # ставим статус пользователю
    user.status = "normal"
    update.message.reply_text("Ваши данные сохранены!")
    # подключаемся к базе данных
    session = db_session.create_session()
    # добавляем пользователя в базу данных
    session.add(user)
    # коммитим изменения
    session.commit()
    return ConversationHandler.END  # Константа, означающая конец диалога.
    # Все обработчики из states и fallbacks становятся неактивными.


# функция для получения случайного фото 🦮
def dog_photo(update, context):
    try:
        # формируем запрос
        responce = requests.get('https://random.dog/woof.json')
        # в формате json
        toponym = responce.json()
        # получаем ссылку на картинку
        photo = toponym["url"]
        # отсылаем пользователю фотографию
        chat_id = update.message.chat_id
        context.bot.send_photo(
            chat_id=chat_id,
            photo=photo
        )
    except BaseException as e:
        print(e)
        update.message.reply_text("Неизвестная ошибка! Пожалуйста, попробуйте заново!")


def cat_photo(update, context):
    try:
        # формируем запрос
        responce = requests.get('https://aws.random.cat/meow')
        # в формате json
        toponym = responce.json()
        # получаем ссылку на картинку
        photo = toponym["file"]
        # отсылаем пользователю фотографию
        chat_id = update.message.chat_id
        context.bot.send_photo(
            chat_id=chat_id,
            photo=photo
        )
    except BaseException as e:
        print(e)
        update.message.reply_text(
            "Неизвестная ошибка! Пожалуйста, попробуйте заново!"
        )


def close_keyboard(update, context):
    update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove()
    )


def set_timer(update, context):
    """Добавляем задачу в очередь"""
    chat_id = update.message.chat_id
    try:
        # args[0] должен содержать значение аргумента (секунды таймера)
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text(
                'Извините, не умеем возвращаться в прошлое'
            )
            return

        # Добавляем задачу в очередь
        # и останавливаем предыдущую (если она была)
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_once(task, due, context=chat_id)
        # Запоминаем созданную задачу в данных чата.
        context.chat_data['job'] = new_job
        # Присылаем сообщение о том, что всё получилось.
        update.message.reply_text(
            'Вернусь через {} секунд'.format(due)
        )

    except (IndexError, ValueError):
        update.message.reply_text(
            'Использование: /set <секунд>'
        )


def task(context):
    job = context.job
    context.bot.send_message(
        job.context, text='Вернулся!'
    )


def unset_timer(update, context):
    # Проверяем, что задача ставилась
    if 'job' not in context.chat_data:
        update.message.reply_text(
            'Нет активного таймера'
        )
        return
    job = context.chat_data['job']
    # планируем удаление задачи (выполнится, когда будет возможность)
    job.schedule_removal()
    # и очищаем пользовательские данные
    del context.chat_data['job']
    update.message.reply_text(
        'Хорошо, вернулся сейчас!'
    )


# функция для получения координат места(города)
def get_ll(city):
    geocoder_url = "http://geocode-maps.yandex.ru/1.x/"
    # формируем параметры для запроса
    params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": city
    }
    # формируем запрос
    response = requests.get(geocoder_url, params=params)
    # в формате json
    toponym = response.json()["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
    # возвращаем координаты места
    return toponym["Point"]["pos"].split()


# функция для получения места(города)
def geocoder(update, context):
    try:
        # выбираем слово из команды пользователя
        city = update.message.text[9:]
        # получаем координаты места
        # с помощью функции get_ll
        ll = get_ll(city)
        # формируем запрос
        static_api_request = f"http://static-maps.yandex.ru/1.x/?ll={ll[0]},{ll[1]}&spn=0.5,0.5&l=map"
        context.bot.send_photo(
            update.message.chat_id,  # Идентификатор чата. Куда посылать картинку.
            # Ссылка на static API, по сути, ссылка на картинку.
            # Телеграму можно передать прямо её, не скачивая предварительно карту.
            static_api_request,
            caption=f"Нашёл: {city}"
        )
    except BaseException as e:
        print(e)
        update.message.reply_text(
            "Неизвестная ошибка! Проверьте написание города!"
        )


def get_id_city(update, city):
    try:
        # выбираем слово из команды пользователя
        # получаем id города, который запросил пользователь
        # формируем параметры для запроса
        params = {
            'q': city,
            'units': 'metric',
            'lang': 'ru',
            'APPID': 'dc3fe5fca29d8fd2decc5bc2118aeab4'
        }
        # формируем запрос
        res = requests.get("http://api.openweathermap.org/data/2.5/find", params)
        # в запросе json
        data = res.json()
        # в city_id -  id города
        city_id = data['list'][0]['id']
        return city_id
    except BaseException as e:
        print(e)
        update.message.reply_text(
            "Неизвестная ошибка! Проверьте написание города!"
        )


# функция для получения погоды в городе
def weather(update, context):
    try:
        # выбираем слово из команды пользователя
        city = update.message.text[8:]
        update.message.reply_text(f'Ищу погоду в городе {city}')
        city_id = get_id_city(update, city)
        # формируем параметры для нового запроса
        new_params = {
            'id': city_id,
            'units': 'metric',
            'lang': 'ru',
            'APPID': 'dc3fe5fca29d8fd2decc5bc2118aeab4'
        }
        # формируем запрос
        response = requests.get("http://api.openweathermap.org/data/2.5/weather", new_params)
        # в формате json
        toponym = response.json()
        # присылаем пользователю результаты
        update.message.reply_text(f"Погода в городе {city}:")
        update.message.reply_text('Описание: {}'.format(toponym['weather'][0]['description']))
        update.message.reply_text('Температура: {}'.format(toponym['main']['temp']))
        update.message.reply_text('Максимальная температура: {}'.format(toponym['main']['temp_max']))
        update.message.reply_text('Минимальная температура: {}'.format(toponym['main']['temp_min']))
    except BaseException as e:
        print(e)
        update.message.reply_text(
            "Неизвестная ошибка! Проверьте написание города!"
        )


def fact_random_number(update, context):
    try:
        number = randint(1, 1000)
        print(number)
        response = requests.get('http://numbersapi.com/{}?json'.format(str(number)))
        print(response)
        toponym = response.json()
        update.message.reply_text(toponym['text'])
    except BaseException as e:
        print(e)
        update.message.reply_text(
            "Неизвестная ошибка! Повторите попытку ещё раз!"
        )


def fact_my_number(update, context):
    try:
        number = update.message.text[16:]
        response = requests.get('http://numbersapi.com/{}?json'.format(str(number)))
        toponym = response.json()
        update.message.reply_text(toponym['text'])
    except BaseException as e:
        print(e)
        update.message.reply_text(
            "Неизвестная ошибка! Повторите попытку ещё раз!"
        )


def main():
    # параметры для подключения к PROXY серверу
    REQUEST_KWARGS = {
        'proxy_url': 'socks5://96.96.33.133:1080',  # Адрес прокси сервера
        # Опционально, если требуется аутентификация:
        'urllib3_proxy_kwargs': {
            'assert_hostname': 'False',
            'cert_reqs': 'CERT_NONE',
            'username': 'user',
            'password': 'password'
        }
    }

    # Создаём объект updater
    # Вместо слова "TOKEN" надо разместить полученный от @BotFather токен
    updater = Updater('1243221890:AAHsgSwnGVBr5WwVEuWdT6wsPcVuW32xI3A', use_context=True,
                      request_kwargs=REQUEST_KWARGS)

    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # сценарий для регистрации пользователя
    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /registration. Она задаёт первый вопрос.
        entry_points=[CommandHandler('registration', registration)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.text, first_answer)],
            # Функция читает ответ на второй вопрос и продолжает беседу.
            2: [MessageHandler(Filters.text, second_answer)],
            3: [MessageHandler(Filters.text, third_answer)],
            4: [MessageHandler(Filters.text, fourth_answer)]
        },
        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    # зарегистрируем сценарий в диспетчере
    dp.add_handler(conv_handler)

    # зарегистрируем команды в диспетчере
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('dog_photo', dog_photo))
    dp.add_handler(CommandHandler("cat_photo", cat_photo))
    dp.add_handler(CommandHandler('registration', registration))
    dp.add_handler(CommandHandler("close", close_keyboard))
    dp.add_handler(CommandHandler("geocoder", geocoder))
    dp.add_handler(CommandHandler("weather", weather))
    dp.add_handler(CommandHandler("fact_random_number", fact_random_number))
    dp.add_handler(CommandHandler("fact_my_number", fact_my_number))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset_timer,
                                  pass_chat_data=True))

    # Ждём завершения приложения.
    # (например, получения сигнала SIG_TERM при нажатии клавиш Ctrl+C)
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
