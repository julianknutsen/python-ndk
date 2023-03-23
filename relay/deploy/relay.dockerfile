FROM python:3.9-slim-bullseye

ARG RELAY_HOST
ARG RELAY_PORT
ARG RELAY_LOG_LEVEL

ENV RELAY_HOST=${RELAY_HOST:-0.0.0.0}
ENV RELAY_PORT=${RELAY_PORT:-2700}
ENV RELAY_LOG_LEVEL=${RELAY_LOG_LEVEL:-INFO}

WORKDIR /app
COPY ../.. python-ndk

RUN pip install -e ./python-ndk[relay]

EXPOSE 2700
ENTRYPOINT ["python /app/python-ndk/relay/server.py"]