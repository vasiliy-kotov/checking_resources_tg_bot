"""Главный файл приложения бота."""
import logging
import os
import requests
import sys
import time

from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from http import HTTPStatus
from mycustomerror import MyCustomError
from telegram import Bot

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = (os.getenv('TELEGRAM_CHAT_ID'))
TELEGRAM_CHAT_ADMIN_ID = (os.getenv('TELEGRAM_CHAT_ADMIN_ID'))
TELEGRAM_CHAT_ID_LIST = []
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
    'https://obshee-delo.club/'
]

logger = logging.getLogger(__name__)


def get_telegram_id():
    """Достаёт из секретного файла перечень id учётных запписей телеграм."""
    telegram_chat_id = []
    buffer = ''
    for t in range(len(TELEGRAM_CHAT_ID)):
        if TELEGRAM_CHAT_ID[t] != ',':
            if t != (len(TELEGRAM_CHAT_ID) - 1):
                buffer += TELEGRAM_CHAT_ID[t]
            else:
                buffer += TELEGRAM_CHAT_ID[t]
                telegram_chat_id.append(int(buffer))
                buffer = ''
        elif TELEGRAM_CHAT_ID[t] == ',':
            telegram_chat_id.append(int(buffer))
            buffer = ''
    logger.info(
        f'telegram_chat_id из get_telegram_id - {telegram_chat_id}.')
    return telegram_chat_id


def send_message_admin(bot, message):
    """Отправляет сообщение в Telegram чат админа."""
    if not bot:
        message = f'Ошибка инициализации объекта bot - {bot}.'
        logger.error(message, exc_info=True)
        raise MyCustomError(message)
    else:
        logger.info(
            f'TELEGRAM_CHAT_ADMIN_ID send_message_admin - {TELEGRAM_CHAT_ADMIN_ID}.')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ADMIN_ID, text=message,)
        logger.info(f'В чат отправлено сообщение - "{message}".')


def send_message(bot, message):
    """Отправляет сообщение в Telegram чаты участников процесса."""
    if not bot:
        message = f'Ошибка инициализации объекта bot - {bot}.'
        logger.error(message, exc_info=True)
        raise MyCustomError(message)
    else:
        logger.info(
            f'TELEGRAM_CHAT_ID_LIST send_message - {TELEGRAM_CHAT_ID_LIST}.')
        for t in TELEGRAM_CHAT_ID_LIST:
            bot.send_message(chat_id=t, text=message,)
            logger.info(f'В чат отправлено сообщение - "{message}".')


def get_resource_answer(endpoint):
    """Делает запрос к эндпоинту.

    В качестве параметра функция получает временную метку и ендпоинт.
    """
    bot = Bot(token=TELEGRAM_TOKEN)
    response = requests.get(endpoint)
    status_code = response.status_code
    if response.status_code != HTTPStatus.OK:
        message_status_code_not_200 = (
            f'Ошибка запроса к ресурсу {endpoint}. Код - {status_code}.'
        )
        logger.error(message_status_code_not_200)
        send_message(bot, message_status_code_not_200)
    else:
        logger.info(f'Ресурс - "{endpoint}", status_code - "{status_code}".')


def check_tokens():
    """Проверяет доступность переменных окружения для работы программы."""
    return all(
        [TELEGRAM_TOKEN, TELEGRAM_CHAT_ID_LIST, TELEGRAM_CHAT_ADMIN_ID])


def main():
    """Основная логика работы бота."""
    logger.info(f'Список Интернет-ресурсов - {[endp for endp in ENDPOINT]}.')
    logger.info('Проверяем токены.')
    global TELEGRAM_CHAT_ID_LIST
    TELEGRAM_CHAT_ID_LIST = get_telegram_id()
    logger.info(f'id учёток Телеграм для рассылки - {TELEGRAM_CHAT_ID_LIST}.')
    logger.info(f'id учётки Телеграм админа - {TELEGRAM_CHAT_ADMIN_ID}.')
    if not check_tokens():
        message = (
            f'Проверка токенов завершилась с ошибкой - {check_tokens()}.')
        logger.critical(message, exc_info=True)
        sys.exit(message)
    else:
        logger.info('Проверка токенов завершилась успешно.')
        while True:
            try:
                bot = Bot(token=TELEGRAM_TOKEN)
                for endp in ENDPOINT:
                    logger.info(f'Проверяем статус сайта "{endp}".')
                    get_resource_answer(endp)
            except ConnectionError as conerror:
                message = ('ConnectionError при запуске функции main: '
                           + f'{conerror}.')
                logger.error(message)
                send_message(bot, message)
                logger.exception(message, exc_info=True)
                raise ConnectionError(message)
            except TypeError as typerror:
                message = (
                    'TypeError при запуске функции main: '
                    + f'{typerror}'
                )
                logger.error(message)
                send_message_admin(bot, message)
                logger.exception(message, exc_info=True)
                raise TypeError(message)
            except Exception as error:
                message = (
                    'Exception при запуске функции '
                    + f'main: {error}.'
                )
                logger.error(message)
                send_message_admin(bot, message)
                logger.exception(message, exc_info=True)
                raise MyCustomError(message)
            finally:
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
