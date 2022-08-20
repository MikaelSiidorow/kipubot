# syntax=docker/dockerfile:1
FROM python:3.8 as base

# Setup ENV variables here (if needed in the future)


FROM base as python-deps

# Install pipenv
RUN pip3 install pipenv

# Install python dependencies in /.venv
WORKDIR /bot
COPY Pipfile .
COPY Pipfile.lock .
RUN  pipenv install --dev

COPY . .
# Run the app
CMD [ "pipenv", "run", "test_hot" ]
