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
│ - JWT токены    │───▶│ - RBAC система   │───▶│ - Mock Views    │
│ - bcrypt        │    │ - Middleware     │    │ - Ресурсы       │
│ - Custom Auth   │    │ - Декораторы     │    │ - Валидация     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Схема базы данных

### A. users - Пользователи (приложение users)
- `id` (PK)
- `email` (unique)
- `password_hash` (bcrypt)
- `first_name`, `last_name`
- `is_active`, `is_verified`
- `deleted_at` (soft delete)

### B. roles - Роли (приложение permissions)
- `id` (PK)
- `name` (admin, manager, user, guest)
- `description`
- `is_default`
- `created_at`

### C. user_roles - Связь пользователей с ролями
- `id` (PK)
- `user_id` (FK -> users.id)
- `role_id` (FK -> roles.id)
- `assigned_by`, `assigned_at`
- `is_active`

### D. role_permissions - Права ролей на ресурсы
- `id` (PK)
- `role_id` (FK -> roles.id)
- `resource_type` (product, order, user)
- `can_create`, `can_read`, `can_update`, `can_delete`
- `can_manage_others` (управление чужими ресурсами)

### E. resources - Ресурсы системы (приложение mock_resources)
- `id` (PK)
- `name`, `resource_type`
- `owner` (FK -> users.id)
- `created_at`, `updated_at`

## Система ролей и разрешений

### Роли:
- **`admin`** - полный доступ ко всем функциям
- **`manager`** - чтение всех данных, управление своими ресурсами
- **`user`** - чтение продуктов, управление своими заказами
- **`guest`** - только чтение продуктов (неаутентифицированные)
- предполагается возможность добавлять роли

### Логика доступа:
- **Роли**: чтение - админы и менеджеры, создание/добавление/удаление - только админы
- **Роли пользователей**: чтение - все аутентифицированные, создание/добавление/удаление - только админы
- **Разрешения**: чтение - админы и менеджеры, создание/добавление/удаление - только админы
- **Ресурсы**: создание/изменение/удаление - по правам роли и владельца

## Технологии

- **Backend**: Django 5.2.5
- **API**: Django REST Framework 3.16.1
- **База данных**: PostgreSQL 15
- **Кэширование**: Redis 7
- **Аутентификация**: JWT (PyJWT), bcrypt
- **Документация API**: drf-spectacular
- **Тестирование**: pytest, pytest-django, faker
- **Контейнеризация**: Docker & Docker Compose

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd custom_auth_backend
```

### 2. Настройка переменных окружения
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

# Redis settings
REDIS_HOST=redis
REDIS_PORT=6379

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Запуск в Docker (рекомендуется)
```bash
# Запуск всех сервисов
docker compose up --buld -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs

# суперпользователь создается автоматически
# при запуске c помощью entrypoint.sh, если еще не создан
```


### 5. Проверка работы
- **API документация**: http://localhost:8000/api/v1/docs/
- **Админка Django**: http://localhost:8000/admin/
- **API endpoints**: http://localhost:8000/api/v1/

#### Загрузка тестовых данных

Для демонстрации работы системы создайте набор тестовых данных:

```bash
# Выполнить в контейнере
docker compose exec web python manage.py create_test_data
```

**Что создается:**
- **Пользователи**: admin@example.com, manager@example.com, user@example.com
- **Роли**: admin, manager, user, guest
- **Типы ресурсов**: product, order
- **Моковые ресурсы**: тестовый продукт и заказ
- **Разрешения**: настроены согласно бизнес-логике

**Логины для тестирования:**
- `admin@example.com` / `AdminPass123!` - полный доступ
- `manager@example.com` / `ManagerPass123!` - создание и редактирование
- `user@example.com` / `UserPass123!` - чтение и управление заказами

## Тестирование

### Запуск тестов в контейнере
```bash
# Все тесты
docker compose exec web python -m pytest
# С подробным выводом
docker-compose exec web python -m pytest -v
```

### Запуск тестов локально
```bash
cd backend
python -m pytest
```

## API Endpoints

```
### Аутентификация (`/api/v1/auth/`)
- `POST /auth/register/` - регистрация пользователя
- `POST /auth/login/` - вход в систему
- `POST /auth/logout/` - выход из системы

### Пользователи (`/api/v1/users/`)
- `GET /users/me/` - профиль текущего пользователя
- `PUT /users/update_profile/` - обновление профиля
- `POST /users/change_password/` - смена пароля
- `POST /users/delete_account/` - удаление аккаунта

### Роли (`/api/v1/roles/`)
- `GET /roles/` - список ролей (admin, manager)
- `POST /roles/` - создание роли (admin)
- `PUT /roles/{id}/` - обновление роли (admin)
- `DELETE /roles/{id}/` - удаление роли (admin)

### Роли пользователей (`/api/v1/user-roles/`)
- `GET /user-roles/` - список назначений ролей (все аутентифицированные)
- `POST /user-roles/` - назначение роли (admin)
- `PUT /user-roles/{id}/` - обновление роли (admin)
- `DELETE /user-roles/{id}/` - удаление роли (admin)

### Разрешения (`/api/v1/permissions/`)
- `GET /permissions/` - список разрешений (admin, manager)
- `POST /permissions/` - создание разрешения (admin)
- `PUT /permissions/{id}/` - обновление разрешения (admin)
- `DELETE /permissions/{id}/` - удаление разрешения (admin)

### Ресурсы (`/api/v1/resources/`)
- `GET /resources/` - список ресурсов (все)
- `POST /resources/` - создание ресурса (user+)
- `PUT /resources/{id}/` - обновление ресурса (user+, владелец)
- `DELETE /resources/{id}/` - удаление ресурса (user+, владелец)
```


## Лицензия

MIT License - см. файл [LICENSE](LICENSE) для деталей.

## Поддержка

При возникновении проблем создайте issue в репозитории или обратитесь к разработчикам.
