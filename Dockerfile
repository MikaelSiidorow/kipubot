FROM python:3.8-slim-buster as base

WORKDIR /bot

RUN pip3 install pipenv

FROM base as install-stage

COPY Pipfile .
COPY Pipfile.lock .

#install dependencies
RUN pipenv install
# Setup the database
COPY setup.py .
RUN python3 setup.py

FROM install-stage as run-stage
COPY . .
# Run the app
CMD [ "pipenv","run","python3", "./bot.py" ]