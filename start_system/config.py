from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv('TOKEN')
URL_DATABASE = getenv('URL_DATABASE')
REFERRAL_REWARD = 2
INITIAL_TASK_REWARD = 2
REQUIRED_UC_FOR_WITHDRAWAL = 60
REQUIRED_CHANNELS = [
    {'name': 'Магаз Дядюшки - КУПИТЬ UC', 'link': 'https://t.me/magaz_dyad'},
    {'name': 'МЕТРО SHOP', 'link': 'https://t.me/metroshopDYAD'},
    {'name': 'Дядь АНДРЕЙ', 'link': 'https://t.me/BAZADYADKI'},
]



