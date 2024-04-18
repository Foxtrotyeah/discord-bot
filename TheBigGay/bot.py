import discord
from discord import app_commands
from discord.ext import commands
import requests
from dotenv import load_dotenv
import os

from cogs.utils import checks


# Load environment variables
load_dotenv()

# Bot link
r = requests.head(url='https://discord.com/api/v1')
try:
    print(f"Rate limit {int(r.headers['Retry-After']) / 60} minutes left")
except:
    print("No rate limit")

command_prefix = '.'

description = "Hey there~ I'm a bot written by my daddy, Foxtrot."

# Right now the bot is set to admin permissions (permissions=8).
intents = discord.Intents(
    guilds=True,
    members=True,
    presences=True,
    bans=True,
    emojis=True,
    voice_states=True,
    messages=True,
    reactions=True,
    message_content=True,
)

extensions = (
    'context',
    'economy',
    'gambling',
    'misc',
    'polls',
    'roles',
    'shop'
)


class GaybotCommandTree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, exception: discord.app_commands.AppCommandError):
        if isinstance(exception, (checks.MinimumBet, app_commands.CheckFailure, app_commands.CommandInvokeError)):
            error_message = exception
        else:
            error_message = "Uh oh... \**grunts*\* something's not right here... \**farts*\*"

        try:
            await interaction.response.send_message(error_message, ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.edit_original_response(content=error_message, embed=None, view=None)


class GayBot(commands.AutoShardedBot):
    user: discord.ClientUser
    app_info: discord.AppInfo

    def __init__(self):
        super().__init__(
            command_prefix=command_prefix,
            description=description,
            intents=intents,
            help_command=None,
            tree_cls=GaybotCommandTree
        )

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

    async def on_command_error(self, ctx: commands.Context, exception: commands.CommandError):
        if isinstance(exception, commands.errors.CommandNotFound):
            return

    async def on_ready(self):
        await self.tree.sync()
        
        game = discord.Game("with a DILF")
        await self.change_presence(status=discord.Status.online, activity=game)

        print(f"Bot is ready: {self.user} with ID: {self.user.id}")

    def run(self):
        return super().run(os.environ['TOKEN'])
