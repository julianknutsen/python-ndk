FROM python:3.11-slim-bullseye

ARG RELAY_HOST
ARG RELAY_PORT
ARG RELAY_LOG_LEVEL
ARG RELAY_EVENT_REPO
ARG RELAY_URL

ENV RELAY_HOST=${RELAY_HOST:-0.0.0.0}
ENV RELAY_PORT=${RELAY_PORT:-2700}
ENV RELAY_LOG_LEVEL=${RELAY_LOG_LEVEL:-INFO}
ENV RELAY_EVENT_REPO=${RELAY_EVENT_REPO:-MEMORY}
ENV RELAY_URL=${RELAY_URL:-wss://localhost}

WORKDIR /app
COPY ../.. python-ndk

RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install -e ./python-ndk[relay]

EXPOSE 2700
ENTRYPOINT ["/opt/venv/bin/python", "/app/python-ndk/relay/server.py"]