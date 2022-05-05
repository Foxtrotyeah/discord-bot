import discord
from discord.ext import commands
from Discord.cogs import admin, audio, economy, events, gambling, initialize, misc, polls
import requests
import os


# Bot link
# Right now the bot is set to admin permissions (permissions=8).
r = requests.head(url=os.environ['URL'])
try:
    print(f"Rate limit {int(r.headers['Retry-After']) / 60} minutes left")
except:
    print("No rate limit")

help_command = commands.DefaultHelpCommand(no_category="Default Commands")
intents = discord.Intents.all()

bot = commands.Bot(help_command=help_command, intents=intents, command_prefix='.')

cogs = [
    admin.Admin,
    audio.Audio,
    economy.Economy,
    events.Events,
    gambling.Gambling,
    initialize.Initialize,
    misc.Miscellaneous,
    polls.Polls
]


def run(token):
    for cog in cogs:
        bot.add_cog(cog(bot))

    bot.run(token)
