from os import getenv
from pathlib import Path

''' Uncomment this if you're using .env file '''
from dotenv import load_dotenv

load_dotenv()

# DIRS
BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'

# APP
DEBUG: bool | None = getenv('DEBUG', '0').lower() in ['1', 'true', 'yes']

# TELEGRAM
TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_SUPERUSER_ID = int(getenv('TELEGRAM_BOT_SUPERUSER_ID'))

# DATABASE
DB_SERVER_PREFIX = getenv('DB_SERVER_PREFIX')
DB_SERVER_HOST = getenv('DB_SERVER_HOST')
DB_SERVER_PORT = getenv('DB_SERVER_PORT')
DB_AUTH_LOGIN = getenv('DB_AUTH_LOGIN')
DB_AUTH_PASSWORD = getenv('DB_AUTH_PASSWORD')
DB_NAME = getenv('DB_NAME')

DB_CONNECTION_STRING = (
    f'{DB_SERVER_PREFIX}://'
    f'{DB_AUTH_LOGIN}'
    f':{DB_AUTH_PASSWORD}@'
    f'{DB_SERVER_HOST}'
    f':{DB_SERVER_PORT}/'
    f'{DB_NAME}'
)
