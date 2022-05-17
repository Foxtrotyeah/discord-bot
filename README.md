# TheBigGay Discord Bot

A bot for personal use amongst my Discord servers.

## Setup

This bot is configured to run on a Heroku server using the Procfile, however it can be run by following these steps:

1. **Install dependencies**

This can be done with `pip install -U -r requirements.txt`

2. **Create a MySQL database**

If using Heroku, there is an add-on that makes this setup easy to integrate with Heroku.

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
