import discord
from discord.ext import commands
import mysql.connector

from .utils import mysql
from .utils import checks


# # Reconnects to the MySQL database
# def connect():
#     global db, cursor
#     db = mysql.connector.connect(**config)
#     cursor = db.cursor()
#     cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
#     return db, cursor


# # Checks if user is in the database, and also checks if the connection to the database has been lost.
# def check_status(ctx, member_id=None):
#     table = str(ctx.guild.id) + "_economy"
#     if member_id:
#         user_id = str(member_id)
#     else:
#         user_id = str(ctx.author.id)

#     try:
#         cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE user_id={user_id})")
#     except Exception as e:
#         print("reconnecting from status...", e)
#         connect()
#         return check_status(ctx)

#     if cursor.fetchone()[0] == 1:
#         return True
#     else:
#         cursor.execute(f"INSERT into {table}(user_id, balance, subsidy_date) "
#                        f"VALUES ({user_id}, 50, %s)", (datetime.now(timezone).date(),))
#         db.commit()
#         return True


# # Check someone's balance. If they're betting, check if they have the funds.
# # If they're applying for a subsidy, check if they are eligible.
# def check_funds(ctx, bet: int = None, bal_check=False, subsidy=False):
#     check_status(ctx)
#     table = str(ctx.guild.id) + "_economy"
#     user_id = str(ctx.author.id)

#     cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
#     result = cursor.fetchone()

#     if bal_check:
#         return result[1]
#     if subsidy:
#         if result[1] < 50 and result[2].date() < datetime.now(timezone).date():
#             return True
#         else:
#             return False
#     if result[1] >= bet:
#         return True
#     else:
#         raise commands.CommandError("Insufficient funds. Try '.balance' to see what is in your account.")


# # Get all economy data
# def get_economy(ctx):
#     table = str(ctx.guild.id) + "_economy"
#     cursor.execute(f"SELECT user_id, balance from {table}")
#     return cursor.fetchall()


# # Updates a user's balance
# async def update_bal(ctx, user: discord.Member, guild: discord.Guild, amt: int = None, subsidy=False):
#     if not amt and not subsidy:
#         return print("Yikes!! Called update_bal without an amount or subsidy request.")
#     check_status(ctx)

#     table = str(guild.id) + "_economy"
#     user_id = str(user.id)

#     cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
#     result = cursor.fetchone()

#     if subsidy:
#         new_bal = max(result[1] + 25, 0)
#         cursor.execute(f"UPDATE {table} "
#                        f"SET balance={new_bal}, subsidy_date=%s "
#                        f"WHERE user_id={user_id}", (datetime.now(timezone).date(),))
#         return db.commit()

#     new_bal = max(result[1] + amt, 0)
#     if new_bal == 0:
#         await ctx.send(f"{user.mention} is broke! LOL")

#     cursor.execute(f"UPDATE {table} SET balance={new_bal} WHERE user_id={user_id}")
#     db.commit()


# # Check to see if economy-related commands are being used in the correct channel.
# def check_channel(ctx):
#     if str(ctx.channel) != "gambling-hall":
#         raise commands.errors.CommandError(
#             f"{ctx.author.mention} You can't use that command in this channel. Try the gambling hall 👀")
#     else:
#         return True


# def get_leaderboard(ctx):
#     table = str(ctx.guild.id) + "_leaderboard"
#     cursor.execute(f"SELECT game, user_id, score, date from {table}")
#     return cursor.fetchall()


# def check_leaderboard(ctx, game, member, score: int):
#     table = str(ctx.guild.id) + "_leaderboard"

#     try:
#         cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE game='{game}')")
#     except Exception as e:
#         print("reconnecting from leader...", e)
#         connect()
#         return check_leaderboard(ctx, game, member, score)

#     if cursor.fetchone()[0] == 1:
#         cursor.execute(f"SELECT * from {table} WHERE game='{game}'")
#         result = cursor.fetchone()

#         if score > int(result[2]):
#             update_leaderboard(ctx, game, member, score)
#             return True
#     else:
#         # new highscore?
#         cursor.execute(f"INSERT into {table}(game, user_id, score, date) "
#                        f"VALUES ('{game}', {member.id}, {score}, %s)", (datetime.now(timezone).date(),))
#         db.commit()
#         return True
#     return False


# def update_leaderboard(ctx, game, member, score: int):
#     table = str(ctx.guild.id) + "_leaderboard"
#     cursor.execute(f"UPDATE {table} SET user_id={member.id}, score={score}, date=%s WHERE game='{game}'",
#                    (datetime.now(timezone).date(),))
#     db.commit()


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Hidden commands from shop cog
        self.shop_items = [
            (".mute [user]", 50, "Mute a user for 60 seconds."),
            (".boot [user]", 100, "Force a user to disconnect until they message The Big Gay."),
            (".admin", 200, "Receive admin privileges for 30 minutes."),
            (".daddy", 1000, "Receive the permanent title of 'Daddy'.")
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        guilds = self.bot.guilds

        for guild in guilds:
            mysql.initialize_guild(guild)

    @commands.command(brief="Get your current balance.", description="Retrieve your current balance in gaybucks.")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def balance(self, ctx):
        result = mysql.get_balance(ctx.author)
        await ctx.send(f"{ctx.author.mention}, your balance is {result} gaybucks.")

    @commands.command(brief="Running low on funds? Use this once per day!",
                      description="You must have less than 50 gaybucks in your account to be eligible. "
                                  "You can also only receive a subsidy once per day.")
    @checks.is_gambling_category()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def subsidy(self, ctx):
        if not mysql.check_subsidy(ctx.author):
            return await ctx.send(
                f"{ctx.author.mention}, you are not eligible for a subsidy. "
                f"Either you have more than 100 gaybucks in your account, "
                f"or your sugar daddy has already bailed you out once today."
            )

        await mysql.subsidize(ctx.author)
        await ctx.send(f"{ctx.author.mention}, 50 gaybucks have been added to your account, "
                       f"courtesy of your sugar daddy 😉. (You now have {mysql.get_balance(ctx, bal_check=True)} GB)")

    @commands.command(brief="Check the current economy standings.",
                      description="Shows each member's current balance in gaybucks.")
    @checks.is_gambling_category()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def economy(self, ctx):
        economy = mysql.get_economy(ctx.guild)
        sorted_economy = sorted(economy, key=lambda tup: tup[1], reverse=True)

        embed = discord.Embed(title="Economy Standings", color=discord.Color.purple())
        for row in sorted_economy:
            member = ctx.guild.get_member(int(row[0]))
            balance = row[1]
            embed.add_field(name=f"{member.name}", value=f"{balance} GB", inline=False)

        await ctx.send(embed=embed)

    @commands.command(brief="Show the available options to spend gaybucks on.",
                      description="View and purchase options with your available gaybuck funds.")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def shop(self, ctx):
        message = "__You can purchase any of the following commands:__"
        for item, cost, description in self.shop_items:
            message += f"\n\n-**{item}** - *{cost} gb*: {description}"

        embed = discord.Embed(title="Shop", description=message, color=discord.Color.dark_gold())
        await ctx.send(embed=embed)

    @commands.command(brief="Donate gaybucks to another member of the server.",
                      description="Donate gaybucks to another member of the server.")
    @checks.is_gambling_category()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def donate(self, ctx, member: discord.Member, amt: int = None):
        # if not member or not amt:
        #     return  ctx.send(f"{ctx.author.mention} Try `.help` + `[the function name]` "
        #                                 f"to get more info on how to use this command.")
        # try:
        #     amt = int(amt)
        # except ValueError:
        #     return ctx.send(f"{ctx.author.mention} Your donation must be an integer (whole) number.")

        checks.has_funds(amt)

        await mysql.update_balance(ctx, ctx.author, -amt)
        await mysql.update_balance(ctx, member, amt)
        await ctx.send(f"{ctx.author.mention} has donated {amt} GB to {member.mention}!")


async def setup(bot):
    await bot.add_cog(Economy(bot))
