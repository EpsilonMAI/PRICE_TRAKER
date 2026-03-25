# Price Tracker 

Веб-приложение для отслеживания цен товаров в различных интернет-магазинах с возможностью получения уведомлений об изменениях цен.

## Технологический стек

### Backend
- **Django 6.0.3** - веб-фреймворк
- **Django REST Framework** - API
- **Simple JWT** - JWT аутентификация
- **PostgreSQL** - база данных
- **django-cors-headers** - обработка CORS
- **Pillow** - работа с изображениями

### Frontend
- **Vite** - сборщик модулей
- **Alpine.js** - реактивный фреймворк
- **Tailwind CSS** - стилизация
- **Flowbite** - UI компоненты

## Требования

- Python 3.10+
- PostgreSQL 14+
- Node.js 18+
- npm или yarn

## 🚀 Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd PRICE_TRAKER
```

### 2. Настройка Backend

#### 2.1 Создание виртуального окружения

```bash
python -m venv .venv
source .venv/bin/activate  # для macOS/Linux
# или
.venv\Scripts\activate     # для Windows
```

#### 2.2 Установка зависимостей

```bash
pip install -r backend/requirements.txt
```

#### 2.3 Настройка базы данных

Создайте базу данных PostgreSQL:

```bash
# Запустите PostgreSQL и создайте базу данных
psql postgres
CREATE DATABASE price_tracker;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE price_tracker TO your_user;
\q
```

#### 2.4 Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Database
DB_NAME=price_tracker
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### 2.5 Применение миграций

```bash
cd backend/price_tracker
python manage.py migrate
```

#### 2.6 Создание суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

#### 2.7 Запуск сервера разработки

```bash
python manage.py runserver
```

Backend будет доступен по адресу: http://127.0.0.1:8000

### 3. Настройка Frontend

#### 3.1 Установка зависимостей

```bash
cd frontend/tracker-ui
npm install
```

#### 3.2 Запуск сервера разработки

```bash
npm run dev
```

Frontend будет доступен по адресу: http://localhost:5173

## Структура проекта

```
PRICE_TRAKER/
├── backend/
│   ├── requirements.txt
│   └── price_tracker/
│       ├── manage.py
│       ├── items/          # Модели товаров и категорий
│       ├── stores/         # Модели магазинов
│       ├── tracking/       # Отслеживание товаров и история цен
│       ├── users/          # Пользователи и профили
│       └── price_tracker/  # Настройки проекта
├── frontend/
│   └── tracker-ui/
│       ├── index.html      # Каталог товаров
│       ├── login.html      # Авторизация
│       ├── register.html   # Регистрация
│       ├── profile.html    # Профиль пользователя
│       └── src/
│           ├── main.js     # Alpine.js компоненты
│           ├── api.js      # API клиент
│           └── style.css   # Стили
├── .env                    # Переменные окружения (не в git)
├── .gitignore
└── README.md
```

## API Endpoints

### Аутентификация
- `POST /api/register/` - Регистрация нового пользователя
- `POST /api/token/` - Получение JWT токенов
- `POST /api/token/refresh/` - Обновление access токена
- `GET /api/profile/` - Получение профиля пользователя

### Отслеживание товаров
- `GET /api/detailedprod/` - Список отслеживаемых товаров
- `POST /api/additem/` - Добавить товар в отслеживание
- `PATCH /api/tracking/<id>/` - Обновить параметры отслеживания

### Товары и магазины
- `GET /api/products/` - Список товаров
- `GET /api/products/<id>/` - Детали товара

## 📱 Использование

1. **Регистрация**: Перейдите на `/register.html` и создайте аккаунт
2. **Вход**: Авторизуйтесь на `/login.html`
3. **Добавление товара**: На главной странице нажмите "Добавить товар"
4. **Отслеживание**: Включайте/выключайте отслеживание через чекбокс на карточке товара
5. **Профиль**: Просматривайте статистику в `/profile.html`

## Разработка

### Запуск в режиме разработки

Откройте два терминала:

**Терминал 1 (Backend):**
```bash
cd backend/price_tracker
source ../../.venv/bin/activate  # активируйте venv
python manage.py runserver
```

**Терминал 2 (Frontend):**
```bash
cd frontend/tracker-ui
npm run dev
```

### Административная панель

Доступна по адресу: http://127.0.0.1:8000/admin

## Основные функции

- ✅ JWT аутентификация
- ✅ Регистрация и авторизация пользователей
- ✅ Добавление товаров в отслеживание
- ✅ Управление активностью отслеживания
- ✅ История изменения цен
- ✅ Профиль пользователя со статистикой
- ✅ Пользовательские названия товаров
- 🚧 Автоматический парсинг цен
- 🚧 Email уведомления
- 🚧 Графики изменения цен

## Лицензия

Этот проект создан в учебных целях для T1 case.

---

⭐ Если проект понравился, поставьте звездочку!
