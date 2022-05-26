import discord
from discord.ext import commands


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


# creates the 'daddy' role
async def daddy_role(guild: discord.Guild):
    await guild.create_role(name="Daddy", color=discord.Color.red())


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
        "💜": "they/them"
    }
    notifications = {
        "🤡": ("Receive notifications from people wanting to play games", "Game Notified")
    }
    funny = {
        "👶": "casual",
        "👺": "gremlin",
        "💩": "shitter"
    }
    needed_roles = {
        "Banished": banish_role,
        "Bitch": bitch_role,
        "Admin Lite": adminlite_role,
        "Daddy": daddy_role,
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
                                                    
        description = str()
        for key, value in self.pronouns.items():
            description += f"{key} {value}\n"
        embed = discord.Embed(title="Pronouns", description=description, color=discord.Color.teal())
        pronoun_message = await roles_channel.send(embed=embed)

        for key, value in self.pronouns.items():
            await pronoun_message.add_reaction(key)

        description = str()
        for key, value in self.notifications.items():
            description += f"{key} {value[0]}\n"
        embed = discord.Embed(title="Notifications", description=description, color=discord.Color.magenta())
        notif_message = await roles_channel.send(embed=embed)

        for key, value in self.notifications.items():
            await notif_message.add_reaction(key)

        description = str()
        for key, value in self.funny.items():
            description += f"{key} {value}\n"
        embed = discord.Embed(title="Funny Roles", description=description, color=discord.Color.green())
        funny_message = await roles_channel.send(embed=embed)

        for key, value in self.funny.items():
            await funny_message.add_reaction(key)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.channel is None:
            return

        if "Banished" in [x.name for x in member.roles]:
            if after.channel.name != "Hell":
                try:
                    return await member.move_to(None)
                except Exception as e:
                    print(e)

        if "Bitch" not in [x.name for x in member.roles]:
            if member.voice.mute:
                await member.edit(mute=False)
        # If the member has the bitch role but isn't muted yet
        elif not member.voice.mute:
            await member.edit(mute=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return

        channel = await self.bot.fetch_channel(payload.channel_id)
        if channel.name != "get-your-roles":
            return

        guild = await self.bot.fetch_guild(payload.guild_id)

        if str(payload.emoji) in self.pronouns:
            role = discord.utils.get(guild.roles, name=self.pronouns[str(payload.emoji)])
            await payload.member.add_roles(role)

        elif str(payload.emoji) in self.notifications:
            role = discord.utils.get(guild.roles, name=self.notifications[str(payload.emoji)][1])
            await payload.member.add_roles(role)

        elif str(payload.emoji) in self.funny:
            role = discord.utils.get(guild.roles, name=self.funny[str(payload.emoji)])
            await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        if user.bot:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel.name != "get-your-roles":
            return

        if str(payload.emoji) in self.pronouns:
            role = discord.utils.get(guild.roles, name=self.pronouns[str(payload.emoji)])
            await user.remove_roles(role)

        elif str(payload.emoji) in self.notifications:
            role = discord.utils.get(guild.roles, name=self.notifications[str(payload.emoji)][1])
            await user.remove_roles(role)

        elif str(payload.emoji) in self.funny:
            role = discord.utils.get(guild.roles, name=self.funny[str(payload.emoji)])
            await user.remove_roles(role)


async def setup(bot):
    await bot.add_cog(Roles(bot))
