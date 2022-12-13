import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import AnswerAPIError, EnvironmentNotFound, MessageSend
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
TIME_SLEEP = 600

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    message = (
        'Отсутствует обязательная переменная окружения: '
        '"{}" Программа принудительно остановлена.'
    )
    if not PRACTICUM_TOKEN:
        raise EnvironmentNotFound(message.format('PRACTICUM_TOKEN'))
    if not TELEGRAM_TOKEN:
        raise EnvironmentNotFound(message.format('TELEGRAM_TOKEN'))
    if not TELEGRAM_CHAT_ID:
        raise EnvironmentNotFound(message.format('TELEGRAM_CHAT_ID'))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено в чат Telegram')
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения: {error}')
        raise MessageSend('Сообщение не отправлено')


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
        raise AnswerAPIError(
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {error}'
        )

    if (homework_statuses.status_code == HTTPStatus.BAD_REQUEST
       or homework_statuses.status_code == HTTPStatus.UNAUTHORIZED
       or homework_statuses.status_code != HTTPStatus.OK):
        error = homework_statuses.json()['error']['error']
        raise AnswerAPIError(
            f'Сбой в работе программы: '
            f'Эндпоинт {ENDPOINT} сообщил об ошибке: {error}.'
        )

    try:
        return homework_statuses.json()
    except Exception as error:
        raise AnswerAPIError(
            f'Сбой в работе программы: '
            f'Эндпоинт {ENDPOINT} вернул некорректный json: {error}.'
        )


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Неверный формат ответа API.')

    if 'homeworks' not in response:
        raise AnswerAPIError('Ответ не содержит информации о домашней работе.')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Неверный формат ответа для "homeworks".')


def parse_status(homework):
    """Извлекает статус этой домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе API домашки нет ключа "homework_name".')
    if 'status' not in homework:
        raise KeyError('В ответе API домашки нет ключа "status".')
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError(
            f'В ответе API домашки указан незвестный статус проверки. '
            f'{homework["status"]}'
        )
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except Exception as error:
        logging.critical(error)
        raise EnvironmentNotFound(error)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            answer = get_api_answer(timestamp)
            check_response(answer)
            print(answer)
            message = parse_status(answer['homeworks'][0])
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    main()
