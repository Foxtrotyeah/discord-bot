import random
import asyncio
import discord
from discord.ext import commands

from .utils import mysql
from .utils import checks


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):        
        if isinstance(error, checks.WrongChannel):                
            await ctx.message.delete()
            return await ctx.send(f"{ctx.author.mention} {error}", delete_after=10)

        else:
            return await ctx.send(f"{ctx.author.mention} {error}")

    @commands.Cog.listener()
    async def on_ready(self):
        guilds = self.bot.guilds

        for guild in guilds:
            categories = [x.name for x in guild.categories]

            if "Gambling" not in categories:
                await self.create_gambling_category(guild)

    async def create_gambling_category(self, guild: discord.Guild):
        gambling_category = await guild.create_category(
            "Gambling", 
            # TODO Overwrites for not being allowed to touch threads
            # overwrites={
            #     guild.default_role: discord.PermissionOverwrite(
            #         send_messages=False,
            #         add_reactions=False
            #     ),
            #     guild.me: discord.PermissionOverwrite(
            #         read_messages=True,
            #         send_messages=True,
            #         add_reactions=True
            #     )
            # },
            position=32
        )

        await guild.create_text_channel(
            "main-hall",
            topic="This is where you gamble your gaybucks away.",
            category=gambling_category,
            position=0
        )

    # TODO Delete messages that are not commands
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

    async def cog_check(self, ctx: commands.Context) -> bool:
        return checks.is_gambling_category_pred(ctx)

    @commands.command(brief="Show the leaderboard for gambling games",
                      description="Check who has won the most money in each of the gambling games.")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def leaderboard(self, ctx: commands.Context):
        leaderboard = mysql.get_leaderboard(ctx.guild)

        embed = discord.Embed(title="Leaderboard", color=discord.Color.purple())
        for row in leaderboard:
            game = row[0]
            member = ctx.guild.get_member(int(row[1]))
            score = row[2]
            embed.add_field(name=f"{game}", value=f"{member.name}\n*{score} GB*", inline=False)

        await ctx.send(embed=embed)

    @commands.command(brief="(1 Player) What are the odds?",
                      description="What are the odds I give you money? (1 in...?)")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def odds(self, ctx: commands.Context, bet: int):
        checks.is_valid_bet(ctx.author, bet)

        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        # Initial prompt to get the 1:? odds
        embed = discord.Embed(
            title="Odds",
            description=(
                f"What are the odds I give you money? "
                "(Choose a number between 2 and 10)"
                f"\n \nUser: {ctx.author.mention}"
            ),
            color=discord.Color.green()
        )
        message1 = await ctx.send(embed=embed)

        for reaction in reactions:
            if reaction == "1️⃣":
                continue
            await message1.add_reaction(reaction)

        def react_check(reaction, user: discord.User):
            return user.id == ctx.author.id and reaction.message.id == message1.id and str(reaction) in reactions

        try:
            emoji, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
            choice = reactions.index(str(emoji)) + 1
        except asyncio.TimeoutError:
            return await message1.delete()

        # Message to actually guess the number with reactions
        embed = discord.Embed(
            title="Odds",
            description=(
                f"You chose 1 in {choice}. Here we go: three, two, one..."
                f"\n \nUser: {ctx.author.mention}"
            ),
            color=discord.Color.green()
        )                 
        message2 = await ctx.send(embed=embed)

        for reaction in range(choice):
            await message2.add_reaction(reactions[reaction])

        def react_check(reaction, user: discord.User):
            return user.id == ctx.author.id and reaction.message.id == message2.id and str(reaction) in reactions

        try:
            emoji, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            await message1.delete()
            await message2.delete()
            return

        result = reactions.index(str(emoji)) + 1
        pick = random.randint(1, choice)

        if result == pick:
            payout = bet * choice
            await mysql.update_balance(ctx, ctx.author, int(payout - bet))

            embed = discord.Embed(
                title="Odds",
                description=(
                    f"You chose 1 in {choice}. Here we go: three, two, one..."
                    f"\n \n**{pick}!** Congrats, {ctx.author.mention}! "
                    f"At **{choice}:1 odds**, your payout is **{payout} gaybucks**."
                ),
                color=discord.Color.green()
            )
            embed.add_field(name="Balance", value=f"You now have {mysql.get_balance(ctx.author)} gaybucks.",
                            inline=False)

            if mysql.check_leaderboard("Odds", ctx.author, payout):
                await ctx.send("New Odds high score!")
        else:
            await mysql.update_balance(ctx, ctx.author, -bet)
            embed = discord.Embed(
                title="Odds",
                description=(
                    f"You chose 1 in {choice}. Here we go: three, two, one..."
                    f"\n \n**{pick}!** Sorry,{ctx.author.mention}, better luck next time."
                ),
                color=discord.Color.red()
            )
            embed.add_field(name="Balance", value=f"You now have {mysql.get_balance(ctx.author)} gaybucks.",
                            inline=False)

        await message2.edit(embed=embed)

    # TODO Change response wait to reactions rather than yes/no
    @commands.command(brief="(2 Players) Bet to see who wins with a higher card",
                      discription="Bet with a friend to see who wins with a higher card.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cardcut(self, ctx: commands.Context, member: discord.Member, bet: int):
        checks.is_valid_bet(ctx.author, bet)

        reactions = ["❌", "✅"]
        suits = ["♠️", "♥️", "♣️", "♦️"]
        values = ["🇦", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🇯", "🇶", "🇰"]

        player1 = ctx.author
        player2 = member
        players = [player1, player2]

        if player1.id == player2.id:
            return await ctx.send(f"{ctx.author.mention} You can't just play with yourself in front of everyone!")

        # Initial prompt to get player 2's consent
        embed = discord.Embed(
            title="Card Cutting",
            description=(
                f"{player1.mention} has started a card-cutting bet against "
                f"{player2.mention}. Do you accept?"
                f"\n \nUser: {ctx.author.mention}"
            ),
            color=discord.Color.green()
        )
        message = await ctx.send(embed=embed)

        for reaction in reactions:
            await message.add_reaction(reaction)

        def react_check(reaction, user: discord.User):
            if user.id == player2.id and reaction.message.id == message.id and str(reaction) in reactions:
                return checks.is_valid_bet(user, bet)

        try:
            emoji, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            return await message.delete()

        if str(emoji) == "❌":
            embed = discord.Embed(
                title="Card Cutting",
                description=(
                    f"{player1.mention} has started a card-cutting bet with "
                    f"{player2.mention} for 10 gaybucks each. Do you accept?"
                    f"\n \n{player2.mention} has declined the bet."
                    f"\n \nUser: {ctx.author.mention}"
                ),
                color=discord.Color.red()
            )
            return await message.edit(embed=embed)

        pot = bet * 2

        # Game starts
        description = (
            f"Bets are in, with a total pot of **{pot} gaybucks**. Each player, you have 60 seconds while " 
            f"I'm shuffling to hit ❌ for me to stop on a card. The player with the higher " 
            f"card wins!\n\n__**Cards:**__"
        )
        embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
        card_cut = await ctx.send(embed=embed)
        await card_cut.add_reaction("❌")

        def card():
            suit_num = random.randint(0, 3)
            number_num = random.randint(0, 12)

            suit = suits[suit_num]
            number = values[number_num]
            return number + suit, (number_num * 10) + suit_num

        def check(reaction, user: discord.User):
            return user in players and reaction.message.id == card_cut.id and str(reaction) == "❌"

        cards = {}
        for _ in range(2):
            try:
                emoji, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                players.remove(user)
                cards[user] = card()

                description += f"\n{user.mention} {cards[user][0]}"
                embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
                await card_cut.edit(embed=embed)
            except asyncio.TimeoutError:
                cards[player1] = card()
                cards[player2] = card()

                description += (
                    f"\n{player1.mention} {cards[player1][0]}\n{player2.mention} {cards[player2][0]}"
                    f"\n(*dealer hit the bottom of the deck*)"
                )
                embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
                await card_cut.edit(embed=embed)
                break

        final = sorted(cards.items(), key=lambda x: x[1])
        winner = final[0][0]
        loser = final[1][0]

        await mysql.update_balance(ctx, winner, pot - bet)
        await mysql.update_balance(ctx, loser, -bet)

        embed = discord.Embed(title="Card Cutting",
                              description=f"Congratulations, {winner.mention}! You've won **{pot} gaybucks**!",
                              color=discord.Color.green())
        embed.add_field(
            name=f"Balance",
            value=(
                f"{winner.mention}: {mysql.get_balance(winner)} GB\n"
                f"{loser.mention}: {mysql.get_balance(loser)} GB"
            ),
            inline=False
        )
        await ctx.send(embed=embed)

        if mysql.check_leaderboard("Cardcut", winner, pot):
            await ctx.send("New Cardcut high score!")

    @commands.command(brief="(1 Player) Bet on which horse will win the race.",
                      discription="Bet with 5x odds on which of the five horses will reach the finish line first.")
    @commands.cooldown(1, 25, commands.BucketType.user)
    async def horse(self, ctx: commands.Context, bet: int):        
        checks.is_valid_bet(ctx.author, bet)

        horses = [
            "🏁- - - - - 🏇**1.**",
            "🏁- - - - - 🏇**2.**",
            "🏁- - - - - 🏇**3.**",
            "🏁- - - - - 🏇**4.**",
            "🏁- - - - - 🏇**5.**"
        ]

        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        description = (
            "Choose your horse!\n \n"
            f"{horses[0]}\n \n{horses[1]}\n \n{horses[2]}\n \n{horses[3]}" 
            f"\n \n{horses[4]}\n \nUser: {ctx.author.mention}"
        )
        embed = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
        message = await ctx.send(embed=embed)

        for reaction in reactions:
            await message.add_reaction(reaction)

        def react_check(reaction, user: discord.User):
            return user.id == ctx.author.id and reaction.message.id == message.id and str(reaction) in reactions

        try:
            emoji, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
            guess = reactions.index(str(emoji)) + 1
        except asyncio.TimeoutError:
            return await message.delete()

        tie = False
        third = 6
        while True:
            choice = random.randint(0, 4)

            horses[choice] = horses[choice][0] + horses[choice][3:]

            description = (
                f"And they're off!\n \n"
                f"{horses[0]}\n \n{horses[1]}\n \n{horses[2]}\n \n{horses[3]}"
                f"\n \n{horses[4]}\n \nUser: {ctx.author.mention}"
            )
            embed = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await message.edit(embed=embed)

            if horses[choice][1] == "🏇":
                winner = choice + 1
                sort = sorted(horses, key=len)
                second = sort[1][-4]
                if len(sort[1]) == len(sort[2]):
                    tie = True
                    third = sort[2][-4]
                break

            await asyncio.sleep(1)

        if winner == guess:
            await mysql.update_balance(ctx, ctx.author, bet * 2)

            description = f"**Horse {winner} Wins!**\n{ctx.author.mention} You have won {bet * 3} gaybucks!\n\n" \
                          f"**Balance**\nYou now have {mysql.get_balance(ctx.author)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await ctx.send(embed=embed2)

            if mysql.check_leaderboard("Horse", ctx.author, bet * 3):
                await ctx.send("New Horse high score!")

        elif int(third) == guess or (int(second) == guess and tie):
            await mysql.update_balance(ctx, ctx.author, bet)

            description = f"**Horse {second} Comes in Second (tie)!**\n{ctx.author.mention} You have won {bet * 2} gaybucks!\n\n" \
                          f"**Balance**\nYou now have {mysql.get_balance(ctx.author)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await ctx.send(embed=embed2)

            if mysql.check_leaderboard("Horse", ctx.author, bet * 2):
                await ctx.send("New Horse high score!")

        elif int(second) == guess:
            await mysql.update_balance(ctx, ctx.author, bet)

            description = f"**Horse {second} Comes in Second!**\n{ctx.author.mention} You have won {bet * 2} gaybucks!\n\n" \
                          f"**Balance**\nYou now have {mysql.get_balance(ctx.author)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await ctx.send(embed=embed2)

            if mysql.check_leaderboard("Horse", ctx.author, bet * 2):
                await ctx.send("New Horse high score!")

        else:
            await mysql.update_balance(ctx, ctx.author, -bet)
            description = f"**Horse {winner} Wins**\n{ctx.author.mention} You have lost {bet} gaybucks.\n\n**Balance**" \
                          f"\nYou now have {mysql.get_balance(ctx.author)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.red())
            await ctx.send(embed=embed2)

    @commands.command(brief="(1 Player) Multiplier will go higher, but you have to stop before it crashes.",
                      discription="The multiplier and your payout will keep going higher. "
                                  "If it crashes before you stop it, you lose your bet.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def crash(self, ctx: commands.Context, bet: int):
        checks.is_valid_bet(ctx.author, bet)

        multiplier = 1.0
        profit = (bet * multiplier) - bet

        embed = discord.Embed(title="Crash", color=discord.Color.green())
        embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Profit", value=f"{int(profit)} gaybucks", inline=True)
        embed.add_field(name="\u200b", value=f"React with :x: to stop!\nUser: {ctx.author.mention}", inline=False)
        message = await ctx.send(embed=embed)
        await message.add_reaction('❌')

        while True:
            await asyncio.sleep(1)

            new_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
            reactions = next((x for x in new_msg.reactions if x.emoji =='❌'), None)
            reactors = [user async for user in reactions.users()]
            if ctx.author in reactors:
                if int(round(profit, 5)) != 0:
                    await mysql.update_balance(ctx, ctx.author, int(round(profit, 5)))

                embed = discord.Embed(title="Crash", color=discord.Color.green())
                embed.add_field(name="Stopped at", value="{:.1f}x".format(multiplier), inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="Profit", value=f"{int(round(profit, 5))} gaybucks", inline=True)
                embed.add_field(name="Balance", value=f"You now have {mysql.get_balance(ctx.author)} gaybucks.",
                                inline=False)
                embed.add_field(name="\u200b", value=f"User: {ctx.author.mention}", inline=False)
                await message.edit(embed=embed)

                if mysql.check_leaderboard("Crash", ctx.author, int(round(profit, 5))):
                        await ctx.send("New Crash high score!")
                break

            multiplier += 0.2
            profit = (bet * multiplier) - bet

            embed = discord.Embed(title="Crash", color=discord.Color.green())
            embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Profit", value=f"{int(round(profit, 5))} gaybucks", inline=True)
            embed.add_field(name="\u200b", value=f"React with :x: to stop!\nUser: {ctx.author.mention}", inline=False)
            await message.edit(embed=embed)

            chance = random.randint(1, 8)
            if chance == 1:
                await mysql.update_balance(ctx, ctx.author, -bet)

                embed = discord.Embed(title="Crash", color=discord.Color.red())
                embed.add_field(name="Crashed at", value="{:.1f}x".format(multiplier), inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="Profit", value=f"{-bet} gaybucks", inline=True)
                embed.add_field(name="Balance", value=f"You now have {mysql.get_balance(ctx.author)} gaybucks.",
                                inline=False)
                embed.add_field(name="\u200b", value=f"User: {ctx.author.mention}", inline=False)
                await message.edit(embed=embed)
                break

    @commands.command(brief="(1 Player) See how many squares you can clear.",
                      description="There are three mines in a field. "
                                  "Clear as many squares as you can before you blow up.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def minesweeper(self, ctx: commands.Context, bet: int):
        checks.is_valid_bet(ctx.author, bet)

        field = (
            "``` -------------------" 
            "\n| A1 | B1 | C1 | D1 |" 
            "\n -------------------" 
            "\n| A2 | B2 | C2 | D2 |" 
            "\n -------------------" 
            "\n| A3 | B3 | C3 | D3 |"
            "\n -------------------" 
            "\n| A4 | B4 | C4 | D4 |" 
            "\n -------------------```"
        )

        indices = ["ABCD1234"]
        reactions = ["🇦", "🇧", "🇨", "🇩", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "❌"]

        bombs = []
        while len(bombs) < 2:
            new = random.choice(indices[:4]) + random.choice(indices[-4:])
            if new not in bombs:
                bombs.append(new)

        next_rate = 0.15
        next_score = int(round(next_rate * bet, 5))
        total = 0

        remaining = 16
        odds = (remaining - 2) / remaining

        embed = discord.Embed(title="Minesweeper", description=f"There are 2 bombs out there...",
                              color=discord.Color.green())
        embed.add_field(name="Next Score", value=f"{next_score} gaybucks", inline=False)
        embed.add_field(name="Total Profit", value=f"{total} gaybucks", inline=False)
        embed.add_field(name="Odds of Scoring", value="{:.2f}%".format(odds * 100), inline=False)
        embed.add_field(name="\u200b", value=f"Select the row and column, or ❌ to stop.\nUser: {ctx.author.mention}", inline=False)
        message = await ctx.send(embed=embed)
        field_msg = await ctx.send(field)

        for reaction in reactions:
            await message.add_reaction(reaction)

        column = None
        row = None
        stop = False

        def check(reaction, user: discord.User):
            global column, row, stop
            if user.id == ctx.author.id and reaction.message.id == message.id and str(reaction) in reactions:
                if str(reaction) == "❌":
                    stop = True
                    return True

                index = reactions.index(str(reaction))

                if index < 4 and not column:
                    column = indices[index]
                    return True
                elif index >= 4 and not row:
                    row = indices[index]
                    return True
            
            return False

        i = 1
        while True:
            try:
                emoji, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                if str(emoji) == "❌":
                    break

                emoji, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                if str(emoji) == "❌":
                    break

            except asyncio.TimeoutError:
                stop = True

            choice = column + row

            if choice in bombs:
                field = field.replace(choice, '❌')
                bombs.remove(choice)
                field = field.replace(bombs[0], '💣')
                await field_msg.edit(content=field)

                await mysql.update_balance(ctx, ctx.author, -bet)

                embed = discord.Embed(title="Minesweeper", color=discord.Color.red())
                embed.add_field(name="KABOOM!", value=f"{ctx.author.mention} You lost {bet} gaybucks",
                                inline=False)
                embed.add_field(name="Balance", value=f"You now have {mysql.get_balance(ctx.author)} gaybucks",
                                inline=False)
                await ctx.send(embed=embed)
                return

            field = field.replace(choice, '✅')
            await field_msg.edit(content=field)

            total += next_score  # update total score with previous prediction
            remaining -= 1  # one less square
            odds = (remaining - 2) / remaining

            next_rate += i / 100  # exp. rate/score
            next_score = int(round(next_rate * bet, 5))

            if remaining - 2 == 0:
                for i in range(len(bombs)):
                    field = field.replace(bombs[i], '💣')
                await field_msg.edit(content=field)

                await mysql.update_balance(ctx, ctx.author, total)

                embed = discord.Embed(title="Minesweeper", color=discord.Color.green())
                embed.add_field(name="You Beat the Game!", value=f"{ctx.author.mention} You have won {total} gaybucks",
                                inline=False)
                embed.add_field(name="Balance", value=f"You now have {mysql.get_balance(ctx.author)} gaybucks",
                                inline=False)
                await ctx.send(embed=embed)

                if mysql.check_leaderboard("Minesweeper", ctx.author, total):
                    await ctx.send("New Minesweeper high score!")

                return

            embed = discord.Embed(title="Minesweeper", description=f"There are 2 bombs out there...",
                                  color=discord.Color.green())
            embed.add_field(name="Next Score", value=f"{next_score} gaybucks", inline=False)
            embed.add_field(name="Total Profit", value=f"{total} gaybucks", inline=False)
            embed.add_field(name="Odds of Scoring", value="{:.2f}%".format(odds * 100), inline=False)
            embed.add_field(name="\u200b", value=f"Type the name of a square or type `stop` to stop."
                                                 f"\nUser: {ctx.author.mention}", inline=False)
            await message.edit(embed=embed)

            i *= 1.9

        if stop:
            for i in range(len(bombs)):
                field = field.replace(bombs[i], '💣')
            await field_msg.edit(content=field)

            if total > 0:
                await mysql.update_balance(ctx, ctx.author, total)

            embed = discord.Embed(title="Minesweeper", color=discord.Color.green())
            embed.add_field(name="You Stopped", value=f"{ctx.author.mention} You have won {total} gaybucks",
                            inline=False)
            embed.add_field(name="Balance", value=f"You now have {mysql.get_balance(ctx.author)} gaybucks",
                            inline=False)
            await ctx.send(embed=embed)

            if mysql.check_leaderboard("Minesweeper", ctx.author, total):
                    await ctx.send("New Minesweeper high score!")
            return


async def setup(bot):
    await bot.add_cog(Gambling(bot))
