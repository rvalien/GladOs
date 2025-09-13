# Dockerfile
FROM alpine:3.19

# Принимаем версию как build argument
ARG RELEASE_VERSION=latest
ENV VERSION=${RELEASE_VERSION}

# Добавляем базовые утилиты
RUN apk add --no-cache curl

# Создаем простой скрипт для демонстрации
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'echo "🚀 Backend service starting..."' >> /app/start.sh && \
    echo 'echo "📦 Version: $VERSION"' >> /app/start.sh && \
    echo 'echo "🕐 Started at: $(date)"' >> /app/start.sh && \
    echo 'echo "🔧 Environment: $ENVIRONMENT"' >> /app/start.sh && \
    echo 'echo "✅ Backend service ready!"' >> /app/start.sh && \
    echo 'while true; do sleep 30; echo "💓 Backend heartbeat - Version: $VERSION"; done' >> /app/start.sh && \
    chmod +x /app/start.sh

WORKDIR /app

# Добавляем health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD echo "Health check - Version: $VERSION" || exit 1

CMD ["/app/start.sh"]