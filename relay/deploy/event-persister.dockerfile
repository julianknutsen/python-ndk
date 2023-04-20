FROM python:3.11-slim-bullseye

ARG KAFKA_URL

ENV KAFKA_URL=${RELAY_URL:-wss://localhost}

WORKDIR /app
COPY ../.. python-ndk

RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install -e ./python-ndk[relay]

EXPOSE 2700
ENTRYPOINT ["/opt/venv/bin/python", "/app/python-ndk/relay/event_persister.py"]