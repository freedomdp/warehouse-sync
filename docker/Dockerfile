FROM python:3.9

# Устанавливаем tzdata и настраиваем часовой пояс
RUN apt-get update && apt-get install -y tzdata
ENV TZ=Europe/Kiev
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

# Устанавливаем дополнительные зависимости
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy mysqlclient pytz

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
