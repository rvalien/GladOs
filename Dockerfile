FROM alpine:3.19

LABEL version=${COMPOSE_TAG}

CMD echo "Hello from version ${COMPOSE_TAG}"