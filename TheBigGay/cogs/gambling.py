import random
import asyncio
import discord
from discord.ext import commands

from ..utils import mysql


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guilds = self.bot.guilds

        for guild in guilds:
            channels = [x.name for x in guild.text_channels]

            if "gambling-hall" not in channels:
                await self.create_gambling_channel(guild)

    async def create_gambling_channel(self, guild):
        general_category = discord.utils.get(guild.categories, name="Text Channels")
        if not general_category:
            general_category = await guild.create_category("Text Channels", position=1)
        await guild.create_text_channel(
            "gambling-hall",
            topic="This is where you gamble your gaybucks away.",
            category=general_category,
            position=32
        )

    @commands.command(brief="Show the leaderboard for gambling games",
                      description="Check who has won the most money in each of the gambling games.")
    @commands.check(check_status)
    @commands.check(check_channel)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def leaderboard(self, ctx):
        leaderboard = get_leaderboard(ctx)

        embed = discord.Embed(title="Leaderboard", color=discord.Color.purple())
        for row in leaderboard:
            game = row[0]
            member = ctx.guild.get_member(int(row[1]))
            score = row[2]
            embed.add_field(name=f"{game}", value=f"{member.name}\n*{score} GB*", inline=False)

        await ctx.send(embed=embed)

    @commands.command(brief="(1 Player) What are the odds?",
                      description="What are the odds I give you money? (1 in...?)")
    @commands.check(check_channel)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def odds(self, ctx, bet=None):
        if not bet:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        try:
            bet = int(bet)
        except ValueError:
            raise commands.CommandError(f"{ctx.author.mention} Your bet must be an integer (whole) number.")
        check_funds(ctx, bet)

        # Initial prompt to get the 1:? odds
        embed = discord.Embed(title="Odds",
                              description=f"{ctx.author.mention} What are the odds I give you money? "
                                          f"(Reply with a number between 2 and 10)",
                              color=discord.Color.green())
        message1 = await ctx.send(embed=embed)

        def check(msg):
            if msg.author.id != ctx.author.id:
                return False
            try:
                if 1 < int(msg.content) <= 10:
                    test = True
                else:
                    test = False
            except ValueError:
                return False
            return msg.author.id == ctx.author.id and test

        try:
            message = await self.bot.wait_for('message', timeout=60, check=check)
            choice = int(message.content)
        except asyncio.TimeoutError:
            return await message1.delete()

        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        # Message to actually guess the number with reactions
        embed = discord.Embed(title="Odds",
                              description=f"{ctx.author.mention} What are the odds I give you money? "
                                          f"(Reply with a number between 2 and 10)\n \n"
                                          f"You chose 1 in {choice}. Here we go: three, two, one...",
                              color=discord.Color.green())
        await message1.edit(embed=embed)

        for i in range(choice):
            await message1.add_reaction(reactions[i])

        def react_check(reaction, user: discord.Member):
            return user.id == ctx.author.id and reaction.message.id == message1.id

        try:
            emoji, member = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            return await message1.delete()

        result = reactions.index(str(emoji)) + 1
        pick = random.randint(1, choice)

        if result == pick:
            payout = bet * choice
            await update_bal(ctx, ctx.author, ctx.guild, amt=int(payout - bet))

            embed = discord.Embed(title="Odds",
                                  description=f"**{pick}!** Congrats, {ctx.author.mention}! "
                                              f"At **{choice}:1 odds**, your payout is **{payout} gaybucks**.",
                                  color=discord.Color.green())
            embed.add_field(name="Balance", value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks.",
                            inline=False)

            if check_leaderboard(ctx, "Odds", ctx.author, payout):
                await ctx.send("New Odds high score!")
        else:
            await update_bal(ctx, ctx.author, ctx.guild, amt=-bet)
            embed = discord.Embed(title="Odds",
                                  description=f"**{pick}!** Sorry,{ctx.author.mention}, better luck next time.",
                                  color=discord.Color.red())
            embed.add_field(name="Balance", value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks.",
                            inline=False)

        await ctx.send(embed=embed)

    @commands.command(brief="(2 Players) Bet to see who wins with a higher card",
                      discription="Bet with a friend to see who wins with a higher card.")
    @commands.check(check_channel)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cardcut(self, ctx, member: discord.Member = None, bet=None):
        if not member or not bet:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        try:
            bet = int(bet)
        except ValueError:
            raise commands.CommandError(f"{ctx.author.mention} Your bet must be an integer (whole) number.")
        check_funds(ctx, bet)

        player1 = ctx.author
        player2 = member
        players = [player1, player2]

        if player1.id == player2.id:
            raise commands.CommandError(f"{ctx.author.mention} You can't just play with yourself in front of everyone!")

        # Initial prompt to get player 2's consent
        embed = discord.Embed(title="Card Cutting",
                              description=f"{player1.mention} has started a card-cutting bet against "
                                          f"{player2.mention}. Do you accept? Type **yes** to accept with a bet of "
                                          f"{bet} gaybucks, or type **no** to decline.",
                              color=discord.Color.green())
        message = await ctx.send(embed=embed)

        def check(msg):
            if msg.author.id != player2.id:
                return False
            answer = str(msg.content).lower()
            if "yes" in answer:
                try:
                    if check_funds(msg, bet):
                        return True
                    else:
                        return False
                except ValueError:
                    return False
                except IndexError:
                    return False
            elif "no" in answer:
                raise commands.CommandError("Player 2 has declined the bet.")
            return False

        try:
            await self.bot.wait_for('message', timeout=60, check=check)
        except asyncio.TimeoutError:
            return await message.delete()

        pot = bet * 2

        # Game starts
        description = f"Bets are in, with a total pot of **{pot} gaybucks**. Each player, you have 60 seconds while " \
                      f"I'm shuffling to type **stop** for me to stop on a card. The player with the higher " \
                      f"card wins!\n\n__**Cards:**__"
        embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
        card_cut = await ctx.send(embed=embed)

        suits = ["♠", "♥", "♣", "♦"]
        numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "**Jack**", "👸", "🤴"]

        def card():
            suit_num = random.randint(0, 3)
            number_num = random.randint(0, 12)

            suit = suits[suit_num]
            number = numbers[number_num]
            return number + suit, (number_num * 10) + suit_num

        def check(msg):
            if msg.author not in players:
                return False
            if "stop" not in msg.content.lower():
                return False
            return True

        cards = {}
        for _ in range(2):
            try:
                message = await self.bot.wait_for('message', timeout=60, check=check)
                players.remove(message.author)
                cards[message.author] = card()

                description += f"\n{message.author.mention} {cards[message.author][0]}"
                embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
                await card_cut.edit(embed=embed)
            except asyncio.TimeoutError:
                cards[player1] = card()
                cards[player2] = card()

                description += f"\n{player1.mention} {cards[player1][0]}\n{player2.mention} {cards[player2][0]}" \
                               f"\n(*dealer hit the bottom of the deck*)"
                embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
                await card_cut.edit(embed=embed)
                break

        final = sorted(cards.items(), key=lambda x: x[1], reverse=True)
        winner = final[0][0]
        loser = final[1][0]

        await update_bal(ctx, winner, winner.guild, amt=pot - bet)
        await update_bal(ctx, loser, loser.guild, amt=-bet)

        if check_leaderboard(ctx, "Cardcut", ctx.author, pot):
            await ctx.send("New Cardcut high score!")

        # todo check_funds needs to check player2 not ctx
        embed = discord.Embed(title="Card Cutting",
                              description=f"Congratulations, {winner.mention}! You've won **{pot} gaybucks**!",
                              color=discord.Color.green())
        # embed.add_field(name=f"{winner.mention} Balance",
        #                 value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks.",
        #                 inline=False)
        # embed.add_field(name=f"{loser.mention} Balance",
        #                 value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks.",
        #                 inline=False)
        await ctx.send(embed=embed)

    @commands.command(brief="(1 Player) Bet on which horse will win the race.",
                      discription="Bet with 5x odds on which of the five horses will reach the finish line first.")
    @commands.check(check_channel)
    @commands.cooldown(1, 25, commands.BucketType.user)
    async def horse(self, ctx, guess=None, bet=None):
        if not bet or not guess:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        try:
            guess = int(guess)
            bet = int(bet)
            if 1 > guess > 5:
                raise commands.CommandError(f"{ctx.author.mention} Your guess must be a number from 1-5.")
        except ValueError:
            raise commands.CommandError(f"{ctx.author.mention} "
                                        f"and your bet must be an integer (whole) number.")
        check_funds(ctx, bet)

        horses = [
            "🏁- - - - - 🏇**1.**",
            "🏁- - - - - 🏇**2.**",
            "🏁- - - - - 🏇**3.**",
            "🏁- - - - - 🏇**4.**",
            "🏁- - - - - 🏇**5.**"
        ]

        description = f"{horses[0]}\n \n{horses[1]}\n \n{horses[2]}\n \n{horses[3]}" \
                      f"\n \n{horses[4]}\n \nUser: {ctx.author.mention}"
        embed = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
        message = await ctx.send(embed=embed)

        tie = False
        third = 6
        while True:
            await asyncio.sleep(1)
            choice = random.randint(0, 4)

            horses[choice] = horses[choice][0] + horses[choice][3:]

            description = f"{horses[0]}\n \n{horses[1]}\n \n{horses[2]}\n \n{horses[3]}" \
                          f"\n \n{horses[4]}\n \nUser: {ctx.author.mention}"
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

        if winner == guess:
            await update_bal(ctx, ctx.author, ctx.author.guild, amt=bet * 2)
            if check_leaderboard(ctx, "Horse", ctx.author, bet * 3):
                await ctx.send("New Horse high score!")

            description = f"**Horse {winner} Wins!**\n{ctx.author.mention} You have won {bet * 3} gaybucks!\n\n" \
                          f"**Balance**\nYou now have {check_funds(ctx, bal_check=True)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await ctx.send(embed=embed2)
        elif int(third) == guess or (int(second) == guess and tie):
            await update_bal(ctx, ctx.author, ctx.author.guild, amt=bet)
            if check_leaderboard(ctx, "Horse", ctx.author, bet * 2):
                await ctx.send("New Horse high score!")

            description = f"**Horse {second} Comes in Second (tie)!**\n{ctx.author.mention} You have won {bet * 2} gaybucks!\n\n" \
                          f"**Balance**\nYou now have {check_funds(ctx, bal_check=True)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await ctx.send(embed=embed2)
        elif int(second) == guess:
            await update_bal(ctx, ctx.author, ctx.author.guild, amt=bet)
            if check_leaderboard(ctx, "Horse", ctx.author, bet * 2):
                await ctx.send("New Horse high score!")

            description = f"**Horse {second} Comes in Second!**\n{ctx.author.mention} You have won {bet * 2} gaybucks!\n\n" \
                          f"**Balance**\nYou now have {check_funds(ctx, bal_check=True)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await ctx.send(embed=embed2)
        else:
            await update_bal(ctx, ctx.author, ctx.author.guild, amt=-bet)
            description = f"**Horse {winner} Wins**\n{ctx.author.mention} You have lost {bet} gaybucks.\n\n**Balance**" \
                          f"\nYou now have {check_funds(ctx, bal_check=True)} gaybucks"
            embed2 = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.red())
            await ctx.send(embed=embed2)

    @commands.command(brief="(1 Player) Multiplier will go higher, but you have to stop before it crashes.",
                      discription="The multiplier and your payout will keep going higher. "
                                  "If it crashes before you stop it, you lose your bet.")
    @commands.check(check_channel)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def crash(self, ctx, bet=None):
        if not bet:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        try:
            bet = int(bet)
        except ValueError:
            raise commands.CommandError(f"{ctx.author.mention} Your bet must be an integer (whole) number.")
        check_funds(ctx, int(bet))

        multiplier = 1.0
        profit = (bet * multiplier) - bet

        embed = discord.Embed(title="Crash", color=discord.Color.green())
        embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Profit", value=f"{int(profit)} gaybucks", inline=True)
        embed.add_field(name="\u200b", value=f"React with ❌ to stop!\nUser: {ctx.author.mention}", inline=False)
        message = await ctx.send(embed=embed)
        await message.add_reaction('❌')

        while True:
            await asyncio.sleep(1)

            new_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
            reactors = await new_msg.reactions[0].users().flatten()
            if ctx.author in reactors:
                if int(round(profit, 5)) != 0:
                    await update_bal(ctx, ctx.author, ctx.author.guild, amt=int(round(profit, 5)))
                    if check_leaderboard(ctx, "Crash", ctx.author, int(round(profit, 5))):
                        await ctx.send("New Crash high score!")

                embed = discord.Embed(title="Crash", color=discord.Color.green())
                embed.add_field(name="Stopped at", value="{:.1f}x".format(multiplier), inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="Profit", value=f"{int(round(profit, 5))} gaybucks", inline=True)
                embed.add_field(name="Balance", value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks.",
                                inline=False)
                embed.add_field(name="\u200b", value=f"User: {ctx.author.mention}", inline=False)
                await message.edit(embed=embed)
                break

            multiplier += 0.2
            profit = (bet * multiplier) - bet

            embed = discord.Embed(title="Crash", color=discord.Color.green())
            embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Profit", value=f"{int(round(profit, 5))} gaybucks", inline=True)
            embed.add_field(name="\u200b", value=f"React with ❌ to stop!\nUser: {ctx.author.mention}", inline=False)
            await message.edit(embed=embed)

            chance = random.randint(1, 8)
            if chance == 1:
                await update_bal(ctx, ctx.author, ctx.author.guild, amt=-bet)

                embed = discord.Embed(title="Crash", color=discord.Color.red())
                embed.add_field(name="Crashed at", value="{:.1f}x".format(multiplier), inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="Profit", value=f"{-bet} gaybucks", inline=True)
                embed.add_field(name="Balance", value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks.",
                                inline=False)
                embed.add_field(name="\u200b", value=f"User: {ctx.author.mention}", inline=False)
                await message.edit(embed=embed)
                break

    @commands.command(brief="(1 Player) See how many squares you can clear.",
                      description="There are three mines in a field. "
                                  "Clear as many squares as you can before you blow up.")
    @commands.check(check_channel)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def minesweeper(self, ctx, bet=None):
        if not bet:
            raise commands.CommandError(f"{ctx.author.mention} Try `.help` + `[the function name]` "
                                        f"to get more info on how to use this command.")
        try:
            bet = int(bet)
        except ValueError:
            raise commands.CommandError(f"{ctx.author.mention} Your bet must be an integer (whole) number.")
        check_funds(ctx, bet)

        field = "``` -------------------" \
                "\n| A1 | B1 | C1 | D1 |" \
                "\n -------------------" \
                "\n| A2 | B2 | C2 | D2 |" \
                "\n -------------------" \
                "\n| A3 | B3 | C3 | D3 |" \
                "\n -------------------" \
                "\n| A4 | B4 | C4 | D4 |" \
                "\n -------------------```"

        indexes = ["ABCD", "1234"]
        bombs = []
        while len(bombs) < 2:
            new = random.choice(indexes[0]) + random.choice(indexes[1])
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
        embed.add_field(name="\u200b", value=f"Type the name of a square or type `stop` to stop."
                                             f"\nUser: {ctx.author.mention}", inline=False)
        message = await ctx.send(embed=embed)
        field_msg = await ctx.send(field)

        def check(msg):
            if msg.author.id != ctx.author.id:
                return False
            if len(msg.content) < 2:
                return False
            if msg.content.upper()[0] in indexes[0] and msg.content[-1] in indexes[1]:
                if msg.content.upper() in field:
                    return True
            if msg.content.lower() == "stop":
                return True
            return False

        i = 1
        while True:
            try:
                response = await self.bot.wait_for('message', timeout=60, check=check)
                choice = response.content
            except asyncio.TimeoutError:
                choice = "stop"

            if choice.lower() == "stop":
                for i in range(len(bombs)):
                    field = field.replace(bombs[i], '💣')
                await field_msg.edit(content=field)

                if total > 0:
                    await update_bal(ctx, ctx.author, ctx.author.guild, amt=total)
                    if check_leaderboard(ctx, "Minesweeper", ctx.author, total):
                        await ctx.send("New Minesweeper high score!")

                embed = discord.Embed(title="Minesweeper", color=discord.Color.green())
                embed.add_field(name="You Stopped", value=f"{ctx.author.mention} You have won {total} gaybucks",
                                inline=False)
                embed.add_field(name="Balance", value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks",
                                inline=False)
                await ctx.send(embed=embed)
                return

            if choice.upper() in bombs:
                field = field.replace(choice.upper(), '❌')
                bombs.remove(choice.upper())
                field = field.replace(bombs[0], '💣')
                await field_msg.edit(content=field)

                await update_bal(ctx, ctx.author, ctx.author.guild, amt=-bet)

                embed = discord.Embed(title="Minesweeper", color=discord.Color.red())
                embed.add_field(name="KABOOM!", value=f"{ctx.author.mention} You lost {bet} gaybucks",
                                inline=False)
                embed.add_field(name="Balance", value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks",
                                inline=False)
                await ctx.send(embed=embed)
                return

            field = field.replace(choice.upper(), '✅')
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

                await update_bal(ctx, ctx.author, ctx.author.guild, amt=total)
                if check_leaderboard(ctx, "Minesweeper", ctx.author, total):
                    await ctx.send("New Minesweeper high score!")

                embed = discord.Embed(title="Minesweeper", color=discord.Color.green())
                embed.add_field(name="You Beat the Game!", value=f"{ctx.author.mention} You have won {total} gaybucks",
                                inline=False)
                embed.add_field(name="Balance", value=f"You now have {check_funds(ctx, bal_check=True)} gaybucks",
                                inline=False)
                await ctx.send(embed=embed)
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


async def setup(bot):
    await bot.add_cog(Gambling(bot))
