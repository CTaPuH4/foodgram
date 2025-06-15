# Фудграм

**Фудграм** — это API для социальной сети рецептов. Пользователи могут публиковать рецепты, добавлять их в избранное, подписываться на авторов и формировать список покупок по выбранным блюдам. Фронтенд реализован в виде одностраничного приложения (React), взаимодействующего с этим REST API.

---

## 🚀 Возможности

- Регистрация и авторизация пользователей
- Публикация, редактирование и удаление рецептов
- Добавление рецептов в избранное
- Подписка на других авторов
- Формирование списка покупок на основе рецептов
- Фильтрация рецептов по тегам, автору и избранному
- Эндпоинты доступны по JWT-токену
- Документация API (автоматическая или Swagger/OpenAPI)
- CI/CD через GitHub Actions
- Развёртывание через Docker Compose (nginx + PostgreSQL + backend)

---

## 🛠️ Стек технологий

- Python 3.9
- Django 3.2
- Django REST Framework
- PyJWT
- PostgreSQL
- Docker + Docker Compose
- Gunicorn + Nginx
- GitHub Actions (CI/CD)

---

### ⚙️ Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке.

Запустить Docker Engine и собрать проект:

```
docker compose -f docker-compose.production.yml up
```

---

### Примеры запросов.
Запросы отправляются на эндпойнты c префиксом ```/api/```  например:
```http://127.0.0.1:8080```**/api/v1**```/users/me```

## Получение JWT-токена

*POST/auth/token/login/*

Request sample:

    {
    "email": "^w\\Z",
    "password": "string"
    }

Response sample (200_OK):

    {
    "token": "string"
    }

## Получение списка пользователей

*GET/users/*

Response sample (200_OK):

    {
      "count": 0,
      "next": "string",
      "previous": "string",
      "results": [
        {
            "email": "string",
            "id": 0,
            "username": "string",
            "first_name": "string",
            "last_name": "string",
            "is_subscribed": false,
            "avatar": "string"
        },
        {
            "email": "string",
            "id": 1,
            "username": "string",
            "first_name": "string",
            "last_name": "string",
            "is_subscribed": false,
            "avatar": "string"
        }
      ]
    }

## Получение списка тегов

*GET/tags/*

Respose sample (200_OK):
[
    {
        "id": 0,
        "name": "string",
        "slug": "string"
    },
    {
        "id": 1,
        "name": "string",
        "slug": "string"
    }
]

---

### Авторы:

* Ilya Nizhelskiy (CTaPuH4)  - https://github.com/CTaPuH4
