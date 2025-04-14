FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    --no-install-recommends

# Установка Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование зависимостей
COPY ../requirements_for_consumers.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements_for_consumers.txt

# Копирование исходного кода
COPY product.py wb_consumer/wb_consumer.py ./

# Команда запуска
CMD ["python3", "wb_consumer.py"]
