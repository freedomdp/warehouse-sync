FROM python:3.12

WORKDIR /app

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Изменяем команду запуска, убирая флаг --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
