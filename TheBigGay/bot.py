import discord
from discord.ext import commands
import requests
import os
from collections import Counter

from utils.roles import Roles


# Bot link
r = requests.head(url=os.environ['URL'])
try:
    print(f"Rate limit {int(r.headers['Retry-After']) / 60} minutes left")
except:
    print("No rate limit")

command_prefix = '.'

description = "Hey there~ I'm a bot written by my daddy Foxtrot."

help_command = commands.DefaultHelpCommand(no_category="Default Commands")

# Right now the bot is set to admin permissions (permissions=8).
intents = discord.Intents.all()

extensions = (
    'audio',
    'economy',
    'events',
    'gambling',
    'misc',
    'polls',
    'shop'
)


def initialize_databases():
    pass


def initialize_roles():
    pass


class GayBot(commands.AutoShardedBot):
    user: discord.ClientUser
    app_info: discord.AppInfo

    def __init__(self):
        super().__init__(
            command_prefix=command_prefix,
            description=description,
            intents=intents,
            help_command=help_command
        )

        self.spam_control = commands.CooldownMapping.from_cooldown(2, 3.0, commands.BucketType.user)

        self._spam_counter = Counter()

    async def setup_hook(self):
        self.app_info = await self.application_info()
        self.owner_id = self.app_info.owner.id

        for extension in extensions:
            try:
                await self.load_extension(f'cogs.{extension}')
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}.")
                print(e)
    
    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)

        bucket = self.spam_control.get_bucket(message)
        retry_after = bucket.update_rate_limit()

        author_id = message.author.id

        if retry_after and author_id != self.owner_id:
            await message.delete()

            self._spam_counter[author_id] += 1
            if self._spam_counter[author_id] == 1:
                await ctx.send(f"Spam. Try again in {round(retry_after)} seconds.")
        else:
            self._spam_counter.pop(author_id, None)

        # Continue command execution
        await self.invoke(ctx)

    async def on_ready(self):
        initialize_databases()
        initialize_roles()

        game = discord.Game("with a DILF | .help")
        await self.change_presence(status=discord.Status.online, activity=game)

        print(f"Bot is ready: {self.user} with ID: {self.user.id}")

    def run(self):
        return super().run(os.environ['TOKEN'])
