![workflow status badge][workflow-status-badge]

# Foodgram

Foodgram - это онлайн-сервис, на котором пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Технологии:

[![Python][Python-badge]][Python-url]
[![Django][Django-badge]][Django-url]
[![DRF][DRF-badge]][DRF-url]
[![Docker][Docker-badge]][Docker-url]

## Установка

Для развёртывания проетка вам потребуется установить Docker и docker compose на вашей виртуальной машине. Инструкции по установке для вашей операционной системы можно найти на официальном сайте [Docker][Docker-url].

1. Скопируйте папки frontend и infra этого репозитория на вашу виртуальную машину.
2. В папке infra создайте файл переменных окружения по данному образцу:
```
SECRET_KEY=<ваш секретный ключ для settings.py Django проекта>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=<имя вашей базы postgres>
POSTGRES_USER=<имя пользователя для допуска к базе>
POSTGRES_PASSWORD=<пароль для допуска к базе>
DB_HOST=db
DB_PORT=5432
```
3. Запустите команду `docker-compose up`
4. Далее выполнить последовательно следующие команды для применения миграций, создания суперпользователя и сбора статических файлов проекта:
```
sudo docker-compose exec backend python migrate
sudo docker-compose exec backend python manage.py createsuperuser
sudo docker-compose exec backend python manage.py collectstatic --no-input
```
В качестве примера для базы данных создано несколько записей и заполнен список ингредиентов, хранящихся в файле `datadump.json`. Их можно внести в базу данных развернутого проекта следующей командой:
```
sudo docker-compose exec backend python manage.py loaddata datadump.json
```

## Использование

Foodgram предлагает следующие функции:

- **Публикация рецептов**: пользователи могут публиковать свои рецепты, указывая ингридиенты и их количество, прикрепляя картинку, помечая рецепт тэгами (например, "завтрак") для удобства их поиска.
- **Подписка на пользователей**: пользователи могут подписываться на публикации других пользователей.
- **Добавление рецептов в избранное**: пользователи могут добавлять понравившиеся рецепты в список "Избранное".
- **Скачивание списка продуктов**: пользователи могут скачивать список продуктов, необходимых для приготовления выбранных блюд.

## Авторство

- **FRONTEND**: команда **Яндекс.Практикум**
- **BACKEND**: Дмитрий Смолов

<!-- MARKDOWN LINKS & BADGES -->

[workflow-status-badge]: https://github.com/DmitrySmolov/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg

[Python-url]: https://www.python.org/
[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white

[Django-url]: https://www.djangoproject.com/
[Django-badge]: https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white

[DRF-url]: https://www.django-rest-framework.org/
[DRF-badge]: https://img.shields.io/badge/DRF-80DAEB?style=for-the-badge&logo=django&logoColor=white

[Docker-url]: https://www.docker.com/
[Docker-badge]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
