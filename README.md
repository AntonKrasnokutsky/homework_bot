# homework_bot
python telegram bot

## Авторы
Разработка курса и заданий Яндекс.Практикум
Иполнитель: Антон Краснокутский

## Описание
Проект разрабатывался на курсе Python-разработчик Яндекс.Практикум. Является учебным проектом по изучению API.
Проект предоставляет возможности:
- Отслеживание статуса проверки заданий
- Отправка сообчещений в Telegram об изменении статуса

## Технология
- Python telegram bot 13.7

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/AntonKrasnokutsky/homework_bot.git
```

```
cd homework_bot/
```

Создать виртуальное окружение

```
python3.7 -m venv venv
```

Активировать виртуальное окружение и установить зависимости

```
. venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Создать файл `.env` с переменными окружения и внести данные:
```
PRACTICUM_TOKEN - токен студента практикума
TELEGRAM_TOKEN - токен telegram бота
TELEGRAM_CHAT_ID - ID telegram чата
```
Запустить проект
```
python homework.py
```
