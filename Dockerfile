# Этап сборки
FROM python:3.13-slim AS builder

ARG RELEASE_VERSION=latest
ENV VERSION=${RELEASE_VERSION}

LABEL version=$VERSION
LABEL description="image with GladOs $VERSION"

WORKDIR /app

# Устанавливаем Poetry
RUN pip install poetry

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости в виртуальное окружение
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

# Финальный этап
FROM python:3.13-slim

WORKDIR /app

# Копируем установленные пакеты и код
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Создаем пользователя для безопасности
RUN adduser --disabled-password --gecos '' appuser

# Создаем директории для coverage и даем права appuser
RUN mkdir -p /app/coverage && \
    mkdir -p /tmp && \
    chmod 777 /tmp && \
    chown -R appuser:appuser /app

USER appuser

# Запускаем бота
CMD ["python", "main.py"]
