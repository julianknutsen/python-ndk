FROM python:3.11-slim-bullseye

RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip

WORKDIR /app
COPY ../.. python-ndk

RUN /opt/venv/bin/pip install -e ./python-ndk[relay]

EXPOSE 2700
ENTRYPOINT ["/opt/venv/bin/python", "/app/python-ndk/relay/server.py"]