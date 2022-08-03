# Kipu Grapher

Telegram bot to graph friday bottle raffle progress.

## Getting Started

### Basic

Using [pipenv](https://pipenv.pypa.io/en/latest/):

1. Set `BOT_TOKEN` in .env
2. pipenv install --dev
3. pipenv run setup
4. pipenv run dev

### Docker

1. docker build -t [image_name] .
2. docker run -e "BOT_TOKEN=???" [image_name]
