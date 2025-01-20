## ctapuh4-foodgram.ddns.net

# Описание.

«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

### Стек использованных технологий:

* Python
* Django
* Django REST framework

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке.

Запустить Docker Engine и собрать проект:

```
docker compose -f docker-compose.production.yml up
```


### Примеры.
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

### Авторы:

* Ilya Nizhelskiy (CTaPuH4)  - https://github.com/CTaPuH4
