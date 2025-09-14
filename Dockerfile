FROM alpine:3.19

ARG RELEASE_VERSION=latest
ENV VERSION=${RELEASE_VERSION}

LABEL version=$VERSION
LABEL description="image with backend $VERSION"

CMD echo "Hello from version $VERSION"
