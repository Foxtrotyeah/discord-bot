import discord

    
class Roles:
    def __init__(self):
        self.required_list = {
            "Banished": self.banish_role,
            "Bitch": self.bitch_role,
            "Admin Lite": self.adminlite_role,
            "Daddy": self.daddy_role,
            "she/her": self.she_role,
            "he/him": self.he_role,
            "they/them": self.they_role,
            "Game Notified": self.gamer_role,
            "casual": self.casual_role,
            "gremlin": self.gremlin_role,
            "shitter": self.shitter_role
        }

    # creates the 'banished' role
    @classmethod
    async def banish_role(guild):
        role = await guild.create_role(name="Banished", hoist=True)
        for category in guild.categories:
            await category.set_permissions(role, connect=False)


    # creates the 'bitch' role
    @classmethod
    async def bitch_role(guild):
        role = await guild.create_role(name="Bitch", hoist=True)
        for category in guild.categories:
            await category.set_permissions(role, speak=False)


    # creates the 'admin lite' role
    @classmethod
    async def adminlite_role(guild):
        perms = discord.Permissions(1341586240)
        await guild.create_role(name="Admin Lite", hoist=True, color=discord.Color.red(), permissions=perms)


    # creates the 'daddy' role
    @classmethod
    async def daddy_role(guild):
        await guild.create_role(name="Daddy", color=discord.Color.red())


    # creates the 'he/him' role
    @classmethod
    async def he_role(guild):
        await guild.create_role(name="he/him", color=discord.Color.blue())


    # creates the 'she/her' role
    @classmethod
    async def she_role(guild):
        await guild.create_role(name="she/her", color=discord.Color.red())


    # creates the 'they/them' role
    @classmethod
    async def they_role(guild):
        await guild.create_role(name="they/them", color=discord.Color.purple())


    # creates the 'gamer' role
    @classmethod
    async def gamer_role(guild):
        await guild.create_role(name="Game Notified", color=discord.Color.gold())


    # creates the 'casual' role
    @classmethod
    async def casual_role(guild):
        await guild.create_role(name="casual", color=discord.Color.orange())


    # creates the 'gremlin' role
    @classmethod
    async def gremlin_role(guild):
        await guild.create_role(name="gremlin", color=discord.Color.purple())


    # creates the 'shitter' role
    @classmethod
    async def shitter_role(guild):
        await guild.create_role(name="shitter", color=discord.Color.dark_blue())
