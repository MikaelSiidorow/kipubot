# syntax=docker/dockerfile:1
FROM python:3.10 as base

# Setup ENV variables here (if needed in the future)


FROM base as python-deps

# Install pipx and poetry
RUN pip3 install --user pipx
ENV PATH=/root/.local/bin:$PATH
RUN pipx install poetry==1.4.2
ENV PATH=/root/.local/pipx/venvs/poetry/bin:$PATH

# Install python dependencies in /.venv
WORKDIR /bot
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install

COPY . .
# Run the app
CMD [ "poetry", "run", "poe", "dev" ]
