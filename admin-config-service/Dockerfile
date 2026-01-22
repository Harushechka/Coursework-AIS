FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY shared/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код сервиса
COPY shared/ .

# Экспортируем порт
EXPOSE 8000

# Запускаем сервис
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]