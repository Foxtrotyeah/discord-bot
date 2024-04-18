from dotenv import load_dotenv
import os


load_dotenv()

env_vars = [
    'TOKEN',
    'MYSQL_DATABASE',
    'MYSQL_HOST',
    'MYSQL_PASSWORD',
    'MYSQL_USER'
]

for var in env_vars:
    if var not in os.environ:
        raise KeyError(f"Missing environment variable {var}. Ensure that .env is configured correctly.")
