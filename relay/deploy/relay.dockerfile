FROM python:3.11-slim-bullseye

RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip
COPY ../../relay_requirements.txt /tmp/relay_requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/relay_requirements.txt

WORKDIR /app
COPY ../.. python-ndk

RUN /opt/venv/bin/pip install -e ./python-ndk[relay]

EXPOSE 2700
ENTRYPOINT ["/opt/venv/bin/python", "/app/python-ndk/relay/server.py"]