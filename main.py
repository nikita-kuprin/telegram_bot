# coding=utf-8
# Импортируем необходимые классы.
from flask_login import LoginManager
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import requests
import pyowm
from werkzeug.security import generate_password_hash, check_password_hash
from data import db_session
from data.users import User

db_session.global_init("db/blogs.sqlite")
login_manager = LoginManager()
user = User()


def set_password(self, password):
    self.hashed_password = generate_password_hash(password)


def age_verification(age):
    try:
        int(age)
        return False
    except ValueError:
        return True


def registration(update, context):
    update.message.reply_text("Какое у Вас имя?")
    return 1


reply_keyboard = [['/registration']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def start(update, context):
    update.message.reply_text("Привет! Я бот. Давайте познакомимся поближе. Для этого пройдите анкету",
                              reply_keyboard=markup)


def help(update, context):
    update.message.reply_text(
        "Мои команды:")
    update.message.reply_text(
        "1) /bop - случайное фото собачки всегда поднимет настроение :3")
    update.message.reply_text(
        "2) /set <время> - поставить таймер на любое количество секунд,"
        " чтобы удалить таймер - напиши мне /unset")
    update.message.reply_text(
        "3) /geocoder <название города> - показать карту местности города")
    update.message.reply_text(
        "4) /weather <название города транслитом> - показать погоду")


def stop(update, context):
    update.message.reply_text(
        "Анкетирование приостановлено. Для возобновления напиши мне /continue")


def first_answer(update, context):
    name = update.message.text
    user.name = name
    update.message.reply_text("Какое красивое имя!")
    update.message.reply_text("А где Вы живёте?🏙")
    return 2


def second_answer(update, context):
    city = update.message.text
    user.city = city
    update.message.reply_text("Сколько Вам лет?")
    return 3


def third_answer(update, context):
    age = update.message.text
    flag = age_verification(age)
    if flag:
        return 3
    user.age = age
    update.message.reply_text("Придумайте пароль")
    return 4


def fourth_answer(update, context):
    password = update.message.text
    user.password = generate_password_hash(password)
    user.status = "normal"
    update.message.reply_text("Ваши данные сохранены!")
    session = db_session.create_session()
    session.add(user)
    session.commit()
    return ConversationHandler.END


def get_url():
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']
    return url


def bop(update, context):
    url = get_url()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


def close_keyboard(update, context):
    update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove()
    )

    # Обычный обработчик, как и те, которыми мы пользовались раньше.


def set_timer(update, context):
    """Добавляем задачу в очередь"""
    chat_id = update.message.chat_id
    try:
        # args[0] должен содержать значение аргумента (секунды таймера)
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text(
                'Извините, не умеем возвращаться в прошлое')
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
        update.message.reply_text('Вернусь через {} секунд'.format(due))

    except (IndexError, ValueError):
        update.message.reply_text('Использование: /set <секунд>')


def task(context):
    job = context.job
    context.bot.send_message(job.context, text='Вернулся!')


def unset_timer(update, context):
    # Проверяем, что задача ставилась
    if 'job' not in context.chat_data:
        update.message.reply_text('Нет активного таймера')
        return
    job = context.chat_data['job']
    # планируем удаление задачи (выполнится, когда будет возможность)
    job.schedule_removal()
    # и очищаем пользовательские данные
    del context.chat_data['job']
    update.message.reply_text('Хорошо, вернулся сейчас!')


def get_ll(city):
    geocoder_uri = "http://geocode-maps.yandex.ru/1.x/"
    response = requests.get(geocoder_uri, params={
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": city
    })
    toponym = response.json()["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
    return toponym["Point"]["pos"].split()


def geocoder(update, context):
    city = update.message.text[9:]
    ll = get_ll(city)
    # Можно воспользоваться готовой функцией,
    # которую предлагалось сделать на уроках, посвящённых HTTP-геокодеру.

    static_api_request = f"http://static-maps.yandex.ru/1.x/?ll={ll[0]},{ll[1]}&spn=0.5,0.5&l=map"
    context.bot.send_photo(
        update.message.chat_id,  # Идентификатор чата. Куда посылать картинку.
        # Ссылка на static API, по сути, ссылка на картинку.
        # Телеграму можно передать прямо её, не скачивая предварительно карту.
        static_api_request,
        caption=f"Нашёл: {city}"
    )


def weather(update, context):
    try:
        city = update.message.text[8:]
        update.message.reply_text(f'Ищу погоду в городе {city}')
        params = {
            'q': city,
            'units': 'metric',
            'lang': 'ru',
            'APPID': 'dc3fe5fca29d8fd2decc5bc2118aeab4'
        }
        res = requests.get("http://api.openweathermap.org/data/2.5/find", params)
        data = res.json()
        city_id = data['list'][0]['id']
        new_params = {
            'id': city_id,
            'units': 'metric',
            'lang': 'ru',
            'APPID': 'dc3fe5fca29d8fd2decc5bc2118aeab4'
        }
        response = requests.get("http://api.openweathermap.org/data/2.5/weather", new_params)
        toponym = response.json()
        print(toponym)
        update.message.reply_text(f"Погода в городе {city}:")
        update.message.reply_text('Описание: {}'.format(toponym['weather'][0]['description']))
        update.message.reply_text('Температура: {}'.format(toponym['main']['temp']))
        update.message.reply_text('Максимальная температура: {}'.format(toponym['main']['temp_max']))
        update.message.reply_text('Минимальная температура: {}'.format(toponym['main']['temp_min']))
    except BaseException as e:
        print(e)
        update.message.reply_text("Неизвестная ошибка! Проверьте написание города!")


def weather_5(update, context):
    city = update.message.text[9:]
    update.message.reply_text(f'Ищу погоду в городе {city}')
    params = {
        'q': city,
        'units': 'metric',
        'lang': 'ru',
        'APPID': 'dc3fe5fca29d8fd2decc5bc2118aeab4'
    }
    res = requests.get("http://api.openweathermap.org/data/2.5/find", params)
    data = res.json()
    city_id = data['list'][0]['id']
    new_params = {
        'id': city_id,
        'units': 'metric',
        'lang': 'ru',
        'APPID': 'dc3fe5fca29d8fd2decc5bc2118aeab4'
    }
    response = requests.get("http://api.openweathermap.org/data/2.5/forecast", new_params)
    toponym = response.json()
    for i in toponym['list']:
        update.message.reply_text(i['dt_txt'], '{0:+3.0f}'.format(i['main']['temp']), i['weather'][0]['description'])


def main():
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
    # Вместо слова "TOKEN" надо разместить полученный от @BotFather токен
    updater = Updater('1243221890:AAHsgSwnGVBr5WwVEuWdT6wsPcVuW32xI3A', use_context=True,
                      request_kwargs=REQUEST_KWARGS)

    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()
    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],

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

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('bop', bop))
    dp.add_handler(CommandHandler('registration', registration))
    dp.add_handler(CommandHandler("close", close_keyboard))
    dp.add_handler(CommandHandler("geocoder", geocoder))
    dp.add_handler(CommandHandler("weather", weather))
    dp.add_handler(CommandHandler("weather2", weather_5))
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
