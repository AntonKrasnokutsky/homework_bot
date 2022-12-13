class EnvironmentNotFound(Exception):
    """Исключение возникающее при нехватки переменных окружения."""

    pass


class AnswerAPIError(Exception):
    """Исключение возникающее при ошибочных ответах от API."""

    pass


class MessageSend(Exception):
    """Ошибка отправки сообщения."""

    pass
