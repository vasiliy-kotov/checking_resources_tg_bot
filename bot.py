"""Главный файл приложения бота."""

import datetime
import logging
import os
import sys
import time
import pytz
import requests

from dotenv import load_dotenv
from http import HTTPStatus
from logging.handlers import RotatingFileHandler
from mycustomerror import MyCustomError
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_SUBSCRIBER_IDS = (os.getenv('TELEGRAM_SUBSCRIBER_IDS'))
TELEGRAM_ADMIN_ID = (os.getenv('TELEGRAM_ADMIN_ID'))
RETRY_TIME = 14400  # В секундах
ENDPOINT = [
    'https://общее-дело.рф/',
    'https://общее-дело.рф/123',
    'https://vk.com/obsheedelorf',
    'https://ok.ru/obsheedelo',
    'https://www.youtube.com/user/proektobsheedelo?sub_confirmation=1',
    'https://rutube.ru/channel/479524/',
    'https://общеедело-про.конкурсы.рф/',
    'https://metodic.obshee-delo.ru/',
    'https://obshee-delo.club/',
    # 'https://12312werwe3.ru/'  # для теста не доступного сайта
]
RESULTS = []
TZ_MOSCOW = pytz.timezone('Europe/Moscow')
DT_MOSCOW = datetime.datetime.now(TZ_MOSCOW)


logger = logging.getLogger(__name__)


def get_telegram_id():
    """Достаёт из секретного файла перечень id учётных запписей телеграм."""
    logger.info('***Работает get_telegram_id.')
    logger.info('Читаем файл list_tg_ids.txt.')
    with open('list_tg_ids.txt', 'r') as f:
        for line in f:
            logger.info(f'Линия в файле - {line}')
            if line.find('=') != -1:
                ids = line[line.find('=') + 1:]
                telegram_subscriber_ids = [int(t) for t in ids.split(',')]
        f.close()
    logger.info(
        'Список ИД учёток Телеграм подписчиков из get_telegram_id - '
        + f'{telegram_subscriber_ids}.')
    return telegram_subscriber_ids


def send_message_admin(bot, message):
    """Отправляет сообщение в Telegram чат админа."""
    logger.info('***Работает send_message_admin.')
    if not bot:
        message = f'Ошибка инициализации объекта bot - {bot}.'
        logger.error(message, exc_info=True)
        raise MyCustomError(message)


def send_message(bot, message, telegram_subscriber_ids_list):
    """Отправляет сообщение в Telegram-чаты участников процесса."""
    logger.info('***Работает send_message.')
    if not bot:
        message = f'Ошибка инициализации объекта bot - {bot}.'
        logger.error(message, exc_info=True)
        raise MyCustomError(message)
    else:
        for t in telegram_subscriber_ids_list:
            bot.send_message(chat_id=t, text=message,)
            logger.info(f'В чат {t} отправлено сообщение - "{message}".')


def check_status_resource(bot, endpoint, telegram_subscriber_ids_list):
    """Делает запрос к эндпоинту.

    В качестве параметра функция получает временную метку и ендпоинт. Делает
    запрос и, если статус ответа на 200, то посылает сообщение пользоватлю из
    списка.
    """
    logger.info('***Работает check_status_resource.')
    response = requests.get(endpoint)
    status_code = response.status_code
    if response.status_code != HTTPStatus.OK:
        message_status_code_not_200 = (
            f'Ошибка запроса к ресурсу {endpoint}. Код - {status_code}.')
        logger.error(message_status_code_not_200)
        send_message(
            bot, message_status_code_not_200, telegram_subscriber_ids_list)
    else:
        logger.info(f'Ресурс - "{endpoint}", status_code - "{status_code}".')
    return status_code


def check_tokens(telegram_subscriber_ids_list):
    """Проверяет доступность переменных окружения для работы программы."""
    logger.info('***Работает check_tokens.')
    logger.info(f'TELEGRAM_TOKEN - {TELEGRAM_TOKEN}.')
    logger.info(
        f'telegram_subscriber_ids_list - {telegram_subscriber_ids_list}.')
    logger.info(f'TELEGRAM_ADMIN_ID - {TELEGRAM_ADMIN_ID}.')
    return all(
        [TELEGRAM_TOKEN, telegram_subscriber_ids_list, TELEGRAM_ADMIN_ID])


def last_check_message(results):
    """Возвращает результаты послденей проверки из константы RESULTS."""
    logger.info('***Работает last_check_message.')
    results_str = ''
    for r in results:
        results_str += (r + ' ')
    logger.info(f'Результат last_check_message - {results_str}.')
    return results_str


def last_check(update, context):
    """Возвращает результаты последней проверки."""
    logger.info('***Работает last_check.')
    chat = update.effective_chat
    name = update.message.chat.username
    button = ReplyKeyboardMarkup(
        [['/bot_settings', '/last_check', '/subscribe']],
        resize_keyboard=True
    )
    message = last_check_message(RESULTS)
    context.bot.send_message(
        chat_id=chat.id,
        text=message,
        reply_markup=button
    )
    logger.info(
        f'Запрошены результаты последней проверки. Пользователь {name}.')


def bot_settings(update, context):
    """Возвращает список проверяемых сайтов и периодичность проверки."""
    logger.info('***Работает bot_settings.')

    def min_or_hour(amount_time):
        """Анализ размера времени.

        Берёт время в секундах и возвращает строки со значением времени и 
        признака минут или часов.
        """
        logger.info('***Работает min_or_hour.')
        time_str = ''
        if (amount_time / 60) > 60:
            time_str += (str(amount_time / 3600) + ' ч')
        elif amount_time < 60:
            time_str += (str(amount_time / 60) + ' м')
        logger.info(f'Результат min_or_hour - {time_str}.')
        return time_str

    chat = update.effective_chat
    name = update.message.chat.username
    button = ReplyKeyboardMarkup(
        [['/bot_settings', '/last_check', '/subscribe']],
        resize_keyboard=True
    )
    endpoints_str = ''
    for e in ENDPOINT:
        endpoints_str += e + '\n'
    time = min_or_hour(RETRY_TIME)
    message = (
        f'Список проверямых сайтов:\n{endpoints_str}'
        + f'Периодичность проверки - 1 р. в {time}.')
    context.bot.send_message(
        chat_id=chat.id,
        text=message,
        reply_markup=button
    )
    logger.info(f'Запрошены настройки бота. Пользователь {name}.')


def subscribe(update, context):
    """Подписка на рассылку сообщений от бота."""
    logger.info('***Работает subscribe.')
    chat = update.effective_chat
    name = update.message.chat.username
    tg_id = update.message.chat.id
    logger.info(f'tg_id - {tg_id}')
    button = ReplyKeyboardMarkup(
        [['/bot_settings', '/last_check', '/subscribe']],
        resize_keyboard=True
    )
    TELEGRAM_SUBSCRIBER_IDS_LIST = get_telegram_id()
    logger.info(
        f'TELEGRAM_SUBSCRIBER_IDS_LIST - {TELEGRAM_SUBSCRIBER_IDS_LIST}.')
    NEW_TELEGRAM_SUBSCRIBER_IDS = 'TELEGRAM_SUBSCRIBER_IDS='
    if tg_id in TELEGRAM_SUBSCRIBER_IDS_LIST:
        for i in range(0, len(TELEGRAM_SUBSCRIBER_IDS_LIST)):
            if TELEGRAM_SUBSCRIBER_IDS_LIST[i] == tg_id:
                del TELEGRAM_SUBSCRIBER_IDS_LIST[i]
                logger.info(
                    'TELEGRAM_SUBSCRIBER_IDS_LIST после удаления id - '
                    + f'{TELEGRAM_SUBSCRIBER_IDS_LIST}.')
                NEW_TELEGRAM_SUBSCRIBER_IDS += ', '.join(
                    str(x) for x in TELEGRAM_SUBSCRIBER_IDS_LIST)
                logger.info(
                    'NEW_TELEGRAM_SUBSCRIBER_IDS id после удаления - '
                    + f'{NEW_TELEGRAM_SUBSCRIBER_IDS}.')
                with open('list_tg_ids.txt', 'w') as f:
                    f.write(NEW_TELEGRAM_SUBSCRIBER_IDS)
                    f.close()
                message = ('Вы отписались от рассылки сообщений от бота.')
                logger.info(f'Пользователь {name} отписалися от рассылки.')
    else:
        NEW_TELEGRAM_SUBSCRIBER_IDS = 'TELEGRAM_SUBSCRIBER_IDS='
        NEW_TELEGRAM_SUBSCRIBER_IDS += ', '.join(
            str(x) for x in TELEGRAM_SUBSCRIBER_IDS_LIST)
        NEW_TELEGRAM_SUBSCRIBER_IDS += f',{tg_id}\n'
        with open('list_tg_ids.txt', 'w') as f:
            f.write(NEW_TELEGRAM_SUBSCRIBER_IDS)
            f.close()
        message = ('Вы подписались на рассылку сообщений от бота.')
        logger.info(f'Пользователь {name} подписался на рассылку.')
    context.bot.send_message(
        chat_id=chat.id,
        text=message,
        reply_markup=button
    )


def main():
    """Основная логика работы бота."""
    logger.info('***Работает main.')
    logger.info(f'Список Интернет-ресурсов - {[endp for endp in ENDPOINT]}.')
    global RESULTS
    TELEGRAM_SUBSCRIBER_IDS_LIST = get_telegram_id()
    if not check_tokens(TELEGRAM_SUBSCRIBER_IDS_LIST):
        message = (
            f'Проверка токенов завершилась с ошибкой - {check_tokens()}.')
        logger.critical(message, exc_info=True)
        sys.exit(message)
    logger.info('Проверка токенов завершилась успешно.')
    while True:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            updater = Updater(token=TELEGRAM_TOKEN)
            RESULTS.append(f'Дата и время последней проверки - {DT_MOSCOW}.\n')
            for endp in ENDPOINT:
                logger.info(f'Проверяем статус сайта "{endp}".')
                check = check_status_resource(
                    bot, endp, TELEGRAM_SUBSCRIBER_IDS_LIST)
                RESULTS.append(f'Сайт {endp}. Результат - {check}.\n')
        except requests.exceptions.ConnectionError as conerror:
            message = ('ConnectionError при запуске функции main: \n'
                       + f'"{conerror}".\nНе удаётся установить соединение '
                       + f'с сайтом. -\n{endp}.')
            logger.error(message)
            send_message(bot, message, TELEGRAM_SUBSCRIBER_IDS_LIST)
            send_message_admin(bot, message)
            logger.exception(message, exc_info=True)
            raise MyCustomError(message)
        except TypeError as typerror:
            message = (f'TypeError при запуске функции main: {typerror}')
            logger.error(message)
            send_message_admin(bot, message)
            logger.exception(message, exc_info=True)
            raise MyCustomError(message)
        except Exception as error:
            message = (f'Exception при запуске функции main: {error}.')
            logger.error(message)
            send_message_admin(bot, message)
            logger.exception(message, exc_info=True)
            raise MyCustomError(message)
        finally:
            updater.dispatcher.add_handler(
                CommandHandler('subscribe', subscribe))
            updater.dispatcher.add_handler(
                CommandHandler('last_check', last_check))
            updater.dispatcher.add_handler(
                CommandHandler('bot_settings', bot_settings))
            updater.start_polling()
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s -'
        + ' %(funcName)s - %(lineno)d'
    )

    # Хэндлер для управления лог-файлами
    handler = RotatingFileHandler(
        'bot.log',
        maxBytes=50000000,
        backupCount=2,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.info('********************\nНачало журнала.')
    logger.info('Формат записей:\n%(asctime)s - %(levelname)s - %(message)s -'
                + ' %(funcName)s - %(lineno)d')

    main()
