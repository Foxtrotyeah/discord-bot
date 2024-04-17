# TheBigGay Discord Bot

A bot for personal use amongst my Discord servers.

## Setup

This bot can be ran by following these steps:

1. **Install dependencies**

This can be done with `pip install -U -r requirements.txt`

2. **Create a MySQL database**

Database, host, password, and username will all be needed for bot functionality.

3. **Set environment variables**

TOKEN is your Discord bot's token, and the MySQL variables are from the database you created.

```py
TOKEN=''
MYSQL_DATABASE=''
MYSQL_HOST=''
MYSQL_PASSWORD=''
MYSQL_USER=''`
```
4. **Run the bot!**

`python3 launcher.py`

The bot init will take care of creating any Discord channels and roles, and creating the MySQL tables for the server.
