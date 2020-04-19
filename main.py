# coding=utf-8
# Импортируем необходимые классы.
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import requests
import time
import re

reply_keyboard = [['/address', '/phone'],
                  ['/site', '/bop']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)


# начало диалога с пользователем
def start(update, context):
    update.message.reply_text(
        "Привет! Я бот. Давайте познакомимся поближе. Для этого пройдите следующую анкету:")
    return 1


# когда для описания функций бота
def help(update, context):
    update.message.reply_text(
        "Мои команды:")
    update.message.reply_text(
        "1) /bop - случайное фото собачки всегда поднимет настроение :3")
    time.sleep(1000)
    update.message.reply_text("2) /set <время> - поставить таймер на любое количество секунд,"
                              " чтобы удалить таймер - напиши мне /unset")
    time.sleep(1000)


def stop(update, context):
    update.message.reply_text(
        "Анкетирование приостановлено. Для возобновления напиши мне /continue")


# Анкета представляет собой серию вопросов;
# каждый ответ пользователя сохраняется в базе и может использоваться в других функциях
def first_answer(update, context):
    update.message.reply_text("Какое у Вас имя?")
    name = update.message.text
    print(name)
    update.message.reply_text("Какое красивое имя!")
    return 2


def second_answer(update, context):
    update.message.reply_text("А где Вы живёте?🏙")
    city = update.message.text
    print city
    return 3


def third_answer(update, context):
    pass


# поправить потом
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
            3: [MessageHandler(Filters.text, third_answer)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('bop', bop))
    dp.add_handler(CommandHandler("close", close_keyboard))
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
