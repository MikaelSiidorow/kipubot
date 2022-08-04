# Kipu Grapher

Telegram bot to graph friday bottle raffle progress.

## Getting Started

### Basic

Using [pipenv](https://pipenv.pypa.io/en/latest/):

1. Set `BOT_TOKEN` in .env
2. Set `DATABASE_URL` in .env
3. pipenv install --dev
4. pipenv run init
5. pipenv run dev

### Docker

(Requires that the database is initialized)

1. docker build -t [image_name] .
2. docker run -e "BOT_TOKEN=???" -e "DATABASE_URL=???" [image_name]
