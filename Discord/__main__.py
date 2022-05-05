from Discord import bot
import os

if __name__ == '__main__':
    token = os.environ['TOKEN']

    bot.run(token)
