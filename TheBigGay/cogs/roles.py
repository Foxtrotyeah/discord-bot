import discord
from discord.ext import commands

from .utils.audio import play


# creates the 'banished' role
async def banish_role(guild: discord.Guild):
    role = await guild.create_role(name="Banished", hoist=True)
    for category in guild.categories:
        await category.set_permissions(role, connect=False)


# creates the 'bitch' role
async def bitch_role(guild: discord.Guild):
    role = await guild.create_role(name="Bitch", hoist=True)
    for category in guild.categories:
        await category.set_permissions(role, speak=False)


# creates the 'admin lite' role
async def adminlite_role(guild: discord.Guild):
    perms = discord.Permissions(1110751554672)
    await guild.create_role(name="Admin Lite", hoist=True, color=discord.Color.red(), permissions=perms)


# creates the 'windows' role
async def windows_role(guild: discord.Guild):
    await guild.create_role(name="Windows", color=discord.Color.dark_blue())


# creates the 'daddy' role
async def daddy_role(guild: discord.Guild):
    await guild.create_role(name="Daddy", color=discord.Color.red())

# creates the 'mommy' role
async def mommy_role(guild: discord.Guild):
    await guild.create_role(name="Mommy", color=discord.Color.fuchsia())

# creates the 'step_bro' role
async def step_bro_role(guild: discord.Guild):
    await guild.create_role(name="Step Bro", color=discord.Color.blue())


# creates the 'he/him' role
async def he_role(guild: discord.Guild):
    await guild.create_role(name="he/him", color=discord.Color.blue())


# creates the 'she/her' role
async def she_role(guild: discord.Guild):
    await guild.create_role(name="she/her", color=discord.Color.red())


# creates the 'they/them' role
async def they_role(guild: discord.Guild):
    await guild.create_role(name="they/them", color=discord.Color.purple())


# creates the 'gamer' role
async def gamer_role(guild: discord.Guild):
    await guild.create_role(name="Game Notified", color=discord.Color.gold())


# creates the 'casual' role
async def casual_role(guild: discord.Guild):
    await guild.create_role(name="casual", color=discord.Color.orange())


# creates the 'gremlin' role
async def gremlin_role(guild: discord.Guild):
    await guild.create_role(name="gremlin", color=discord.Color.purple())


# creates the 'shitter' role
async def shitter_role(guild: discord.Guild):
    await guild.create_role(name="shitter", color=discord.Color.dark_blue())


class Roles(commands.Cog):
    pronouns = {
        "❤": "she/her",
        "💙": "he/him",
        "💜": "they/them",
        "color": discord.Color.teal,
        "title": "Pronouns"
    }
    notifications = {
        "🤡": ("Receive notifications from people wanting to play games", "Game Notified"),
        "color": discord.Color.magenta,
        "title": "Notifications"
    }
    funny = {
        "👶": "casual",
        "👺": "gremlin",
        "💩": "shitter",
        "color": discord.Color.green,
        "title": "Funny Roles"
    }
    needed_roles = {
        "Banished": banish_role,
        "Bitch": bitch_role,
        "Admin Lite": adminlite_role,
        "Windows": windows_role,
        "Daddy": daddy_role,
        "Mommy": mommy_role,
        "Step Bro": step_bro_role,
        "she/her": she_role,
        "he/him": he_role,
        "they/them": they_role,
        "Game Notified": gamer_role,
        "casual": casual_role,
        "gremlin": gremlin_role,
        "shitter": shitter_role
    }

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guilds = self.bot.guilds

        for guild in guilds:
            # Check for roles used by the bot
            roles = [x.name for x in guild.roles]
            for role, function in self.needed_roles.items():
                if role not in roles:
                    await function(guild)

            # Check for get-your-roles channel
            channels = [x.name for x in guild.text_channels]

            if "get-your-roles" not in channels:
                await self.create_roles_channel(guild)

    async def create_roles_channel(self, guild: discord.Guild):
        welcome_category = discord.utils.get(guild.categories, name="Welcome")
        if not welcome_category:
            welcome_category = await guild.create_category("Welcome", position=0)
            
            # Shuffle categories down after adding Welcome to the top
            for category in guild.categories:
                if category.name == "Welcome":
                    continue
                await category.edit(position=category.position + 1)
                
        roles_channel = await guild.create_text_channel(
            name="get-your-roles",
            category=welcome_category, position=0,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=False,
                    add_reactions=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    add_reactions=True
                )
            }
        )

        for emoji_list in [self.pronouns, self.notifications, self.funny]:
            description = str()
            for key, value in emoji_list.items():
                if len(key) > 1:
                    continue
                if type(value) is tuple:
                    value = value[-1]
                description += f"{key}, {value}\n"
            embed = discord.Embed(title=emoji_list["title"], description=description, color=emoji_list["color"]())
            message = await roles_channel.send(embed=embed)

            for key, value in emoji_list.items():
                if len(key) == 1:
                    await message.add_reaction(key)

    # TODO idk what to actually do with this
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # 'Step Bro' role functionality
        roles = [x.name for x in message.author.roles]
        if "Step Bro" in roles:
            ctx = await self.bot.get_context(message)
            await ctx.send("*sure thing, step bro*")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.channel is None:
            return

        roles = [x.name for x in member.roles]

        if "Windows" in roles:
            role = discord.utils.get(member.guild.roles, name="Windows")
            await member.remove_roles(role)

            innocent = [individual for individual in after.channel.members if individual.id != member.id]
            for member in innocent:
                await member.edit(deafen=True)

            await play(self.bot, channel=after.channel, name="windows.mp3", wait=True)

            for member in innocent:
                await member.edit(deafen=False)

        if "Banished" in roles:
            if after.channel.name != "Hell":
                try:
                    return await member.move_to(None)
                except Exception as e:
                    print(e)

        if "Bitch" not in roles:
            if member.voice.mute:
                await member.edit(mute=False)
        # If the member has the bitch role but isn't muted yet
        elif not member.voice.mute:
            await member.edit(mute=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel.name != "get-your-roles":
            return

        guild = self.bot.get_guild(payload.guild_id)

        for emoji_list in [self.pronouns, self.notifications, self.funny]:
            if str(payload.emoji) in emoji_list:
                role_name = emoji_list[str(payload.emoji)]
                if type(role_name) is tuple: 
                    role_name = role_name[-1]

                role = discord.utils.get(guild.roles, name=role_name)
                await payload.member.add_roles(role)
                return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel.name != "get-your-roles":
            return
        
        for emoji_list in [self.pronouns, self.notifications, self.funny]:
            if str(payload.emoji) in emoji_list:
                role_name = emoji_list[str(payload.emoji)]
                if type(role_name) is tuple: 
                    role_name = role_name[-1]

                role = discord.utils.get(guild.roles, name=role_name)
                await member.remove_roles(role)
                return


async def setup(bot):
    await bot.add_cog(Roles(bot))
