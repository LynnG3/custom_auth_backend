# Custom Authentication Backend

Проект на Django с Django REST Framework и PostgreSQL для аутентификации пользователей.

## Архитектура 

### Принципы:

- Разделение ответственности: аутентификация, авторизация и бизнес-логика разделены
- Централизованное управление правами: все правила в одном месте
- Гибкость: легко добавлять новые ресурсы без изменения кода
- Производительность: кэширование прав и ролей

### Компоненты:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Аутентификация │    │    Авторизация   │    │  Бизнес-логика  │
│                 │    │                  │    │                 │
│ - JWT токены    │───▶│ - Проверка прав  │───▶│ - Mock Views    │
│ - bcrypt        │    │ - Middleware     │    │ - Ресурсы       │
│ - Middleware    │    │ - Декораторы     │    │ - Валидация     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Схема базы данных

A. users - Пользователи (приложение users)

- id (PK)
- email (unique)
- password_hash (bcrypt)
- first_name, last_name
- is_active, is_verified
- deleted_at

B. roles - Роли (приложение permissions)

- id (PK)
- name (admin, manager, user, guest)
- description


C. user_roles - Связь пользователей с ролями (приложение permissions)

- id (PK)
- user_id (FK -> users.id)
- role_id (FK -> roles.id)
- assigned_by, assigned_at

D. resource_permissions - Права ролей на ресурсы (приложение permissions)

- id (PK)
- role_id (FK -> roles.id)
- resource_name (string - 'users', 'products', 'orders')
- resource_type (string - 'module', 'object')
- read_permission (boolean)
- read_all_permission (boolean)
- create_permission (boolean)
- update_permission (boolean)
- update_all_permission (boolean)
- delete_permission (boolean)
- delete_all_permission (boolean)


## Технологии

- **Backend**: Django 5.2.5
- **API**: Django REST Framework 3.16.1
- **База данных**: PostgreSQL 15
- **Аутентификация**: 
- **Контейнеризация**: Docker & Docker Compose

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd custom_auth_backend
```

### 2. Создание виртуального окружения
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей
```bash
cd backend
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
Создайте файл `.env` в папке `backend/`:
```env
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DB_NAME=postgres_db
DB_USER=postgres_user
DB_PASSWORD=postgres_password
DB_HOST=localhost
DB_PORT=5432

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 5. Запуск PostgreSQL
```bash
docker-compose up -d
```

### 6. Применение миграций
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 8. Запуск сервера
```bash
python manage.py runserver
```

## API Endpoints

...

## Структура проекта

```
...
```



## Тестирование

```bash
# Запуск тестов
python manage.py test

# Запуск тестов с покрытием
coverage run --source='.' manage.py test
coverage report
```

## Развертывание

### Production настройки
1. Установите `DEBUG=False` в `.env`
2. Настройте `ALLOWED_HOSTS`
3. Используйте переменные окружения для секретных ключей
4. Настройте статические файлы
5. Используйте HTTPS

### Docker
```bash
# Сборка образа
docker build -t custom-auth-backend .

# Запуск контейнера
docker run -p 8000:8000 custom-auth-backend
```

## Лицензия

MIT License - см. файл [LICENSE](LICENSE) для деталей.

## Поддержка

При возникновении проблем создайте issue в репозитории или обратитесь к разработчикам.
