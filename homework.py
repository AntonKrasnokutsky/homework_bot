import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    filename='main.log',
    filemode='w',
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class EnvironmentNotFound(Exception):
    """Исключение возникающее при нехватки переменных окружения."""

    pass


class AnswerAPIError(Exception):
    """Исключение возникающее при ошибочных ответах от API."""

    pass


def check_tokens():
    """Проверяет доступность переменных окружения."""
    message = ("Отсутствует обязательная переменная окружения: "
               "'{}' Программа принудительно остановлена.")
    if not PRACTICUM_TOKEN:
        logging.critical(message.format("PRACTICUM_TOKEN"))
        raise EnvironmentNotFound(message.format("PRACTICUM_TOKEN"))
    elif not TELEGRAM_TOKEN:
        logging.critical(message.format("TELEGRAM_TOKEN"))
        raise EnvironmentNotFound(message.format("TELEGRAM_TOKEN"))
    elif not TELEGRAM_CHAT_ID:
        logging.critical(message.format("TELEGRAM_CHAT_ID"))
        raise EnvironmentNotFound(message.format("TELEGRAM_CHAT_ID"))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug("Сообщение отправлено в чат Telegram")
    except Exception as error:
        message = f"Сбой при отправке сообщения: {error}"
        logging.error(message)


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
    except Exception as error:
        logging.error(
            f"Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. "
            f"Код ответа API: {error}"
        )
        homework_statuses = None
    if homework_statuses.status_code == HTTPStatus.BAD_REQUEST:
        error = homework_statuses.json()['error']['error']
        logging.error(
            f"Сбой в работе программы: "
            f"Эндпоинт {ENDPOINT} сообщил об ошибке: {error}."
        )
        homework_statuses = None
    elif homework_statuses.status_code == HTTPStatus.UNAUTHORIZED:
        message = homework_statuses.json()['message']
        logging.error(
            f"Сбой в работе программы: "
            f"Эндпоинт {ENDPOINT} сообщил об ошибке: {message}."
        )
        homework_statuses = None
    elif homework_statuses.status_code != HTTPStatus.OK:
        error = homework_statuses.status_code()
        logging.error(
            f"Сбой в работе программы: "
            f"Эндпоинт {ENDPOINT} сообщил об ошибке: Код ответа API: {error}."
        )
        homework_statuses = None

    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    keys = ['homeworks', 'current_date']
    if not isinstance(response, dict):
        message = "Неверный формат ответа API."
        raise TypeError(message)
    for key in response.keys():
        if key not in keys:
            message = (f"Неожиданный ключ в ответе: "
                       f"Эндпоинт {ENDPOINT}. Ключ в ответе: {key}")
            raise AnswerAPIError(message)
    if 'homeworks' not in response.keys():
        message = "Ответ не содержит информации о домашней работе."
        raise AnswerAPIError(message)
    if not isinstance(response['homeworks'], list):
        message = "Неверный формат ответа для 'homeworks'."
        raise TypeError(message)


def parse_status(homework):
    """Извлекает статус этой домашней работы."""
    if "homework_name" not in homework.keys():
        raise KeyError("В ответе API домашки нет ключа 'homework_name'.")
    if "status" not in homework.keys():
        raise KeyError("В ответе API домашки нет ключа 'status'.")
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError(
            f"В ответе API домашки указан незвестный статус проверки. "
            f"{homework['status']}"
        )
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        answer = get_api_answer(timestamp)
        try:
            check_response(answer)
            message = parse_status(answer['homeworks'][0])
            send_message(bot, message)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            send_message(bot, message)
        time.sleep(600)


if __name__ == '__main__':
    main()
