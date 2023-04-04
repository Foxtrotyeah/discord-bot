import discord
from discord import app_commands
from discord.ext import commands
import requests
import asyncio
import os
from collections import Counter

from cogs.utils import checks


# The Big Gay version 3.0.0


# Bot link
r = requests.head(url='https://discord.com/api/v1')
try:
    print(f"Rate limit {int(r.headers['Retry-After']) / 60} minutes left")
except:
    print("No rate limit")

command_prefix = '.'

description = "Hey there~ I'm a bot written by my daddy, Foxtrot."

help_command = commands.DefaultHelpCommand(no_category="Default Commands", verify_checks=False)

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
    'gambling',
    'economy',
    'misc',
    'polls',
    'roles',
    'shop'
)


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

        self.spam_control = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)

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

        if message.author.bot or not ctx.command:
            return

        # Only invoke gambling and economy commands in the Gambling category
        if message.channel.category.name == 'Gambling' and ctx.command.name != 'help':
            if ctx.command.cog_name not in ('Gambling', 'Economy'):
                return 

        # Spam control
        bucket = self.spam_control.get_bucket(message)
        retry_after = bucket.update_rate_limit()

        author_id = message.author.id

        if retry_after and author_id != self.owner_id:
            await message.delete()

            self._spam_counter[author_id] += 1
            if self._spam_counter[author_id] == 1:
                await ctx.send(f"Spam. Try again in {round(retry_after)} seconds.")

            return
        else:
            self._spam_counter.pop(author_id, None)

        # Continue command execution
        await self.invoke(ctx)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            return await ctx.send_help(ctx.command)

        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(error, delete_after=5)

        elif isinstance(error, (checks.WrongChannel, checks.MinimumBet)):                
            await ctx.send(f"{ctx.author.mention} {error}", delete_after=10)

            await asyncio.sleep(10)
            await ctx.message.delete()
            return

        else:
            return await ctx.send(f"{ctx.author.mention} {error}")


    async def on_ready(self):
        await self.tree.sync()
        
        game = discord.Game("with a DILF")
        await self.change_presence(status=discord.Status.online, activity=game)

        print(f"Bot is ready: {self.user} with ID: {self.user.id}")

    def run(self):
        return super().run(os.environ['TOKEN'])
    

bot = GayBot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    print(error)

    error_message = "Uh oh... \**grunts*\* something's not right here... \**farts*\*"
    try:
        await interaction.response.send_message(error_message, ephemeral=True)
    except discord.errors.InteractionResponded:
        await interaction.edit_original_response(content=error_message, embed=None, view=None)

if __name__ == '__main__':
    bot.run()
