# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /bot

# Setup venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Setup the database
COPY setup.py setup.py
RUN python3 setup.py

# Run the app
COPY . .
CMD [ "python3", "./bot.py" ]