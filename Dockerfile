FROM alpine:3.19

ARG COMPOSE_TAG=latest
ENV VERSION=${COMPOSE_TAG}

CMD echo "Hello from version $VERSION"