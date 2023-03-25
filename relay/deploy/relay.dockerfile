FROM python:3.11-slim-bullseye

ARG RELAY_HOST
ARG RELAY_PORT
ARG RELAY_LOG_LEVEL

ENV RELAY_HOST=${RELAY_HOST:-0.0.0.0}
ENV RELAY_PORT=${RELAY_PORT:-2700}
ENV RELAY_LOG_LEVEL=${RELAY_LOG_LEVEL:-INFO}

WORKDIR /app
COPY ../.. python-ndk

RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install -e ./python-ndk[relay]

EXPOSE 2700
ENTRYPOINT ["/opt/venv/bin/python", "/app/python-ndk/relay/server.py"]