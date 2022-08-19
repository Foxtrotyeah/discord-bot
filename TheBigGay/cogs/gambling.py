import random
import time
import asyncio
import discord
from discord.ext import commands

from .utils import mysql
from .utils import checks


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            overwrites={
                guild.default_role: discord.PermissionOverwrite(
                    add_reactions=False
                ),
                guild.me: discord.PermissionOverwrite(
                    add_reactions=True
                )
            },
            position=32
        )

        await guild.create_text_channel(
            "main-hall",
            topic="This is where you gamble your gaybucks away.",
            category=gambling_category,
            position=0
        )

        await guild.create_text_channel(
            "high-roller-hall",
            topic="Private gambling for the pros.",
            category=gambling_category,
            position=0
        )

    # No messages except for commands in the Gambling category.
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)

        if message.author.bot:
            return            

        if message.channel.category.name == 'Gambling':
            # Check if message is actually a gambling/economy command being called
            if ctx.command:
                if ctx.command.cog_name in ('Gambling', 'Economy') or ctx.command.name == 'help':
                    return

            await message.delete()

    async def cog_check(self, ctx: commands.Context) -> bool:
        return checks.is_gambling_category_pred(ctx)

    @commands.command(brief="Show the leaderboard for gambling games",
                      description="Check who has won the most money in each of the gambling games.")
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
    async def odds(self, ctx: commands.Context, bet: int):
        checks.is_valid_bet(ctx, ctx.author, bet)

        options = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

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

        for option in options:
            if option == "1️⃣":
                continue
            await message1.add_reaction(option)

        def react_check(reaction: discord.Reaction, user: discord.User):
            return user.id == ctx.author.id and reaction.message.id == message1.id and str(reaction) in options

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            return await message1.delete()

        choice = options.index(str(reaction)) + 1
        await message1.delete()

        # Message to actually guess the number with reactions
        embed = discord.Embed(
            title="Odds",
            description=(
                f"You chose 1 in {choice} odds. Here we go: three, two, one..."
                f"\n \nUser: {ctx.author.mention}"
            ),
            color=discord.Color.green()
        )                 
        message2 = await ctx.send(embed=embed)

        for i in range(choice):
            await message2.add_reaction(options[i])

        def react_check(reaction: discord.Reaction, user: discord.User):
            return user.id == ctx.author.id and reaction.message.id == message2.id and str(reaction) in options

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            await message2.delete()
            return

        result = options.index(str(reaction)) + 1
        pick = random.randint(1, choice)

        if result == pick:
            payout = bet * choice
            balance = mysql.update_balance(ctx.author, payout - bet)

            embed = discord.Embed(
                title="Odds",
                description=(
                    f"You chose 1 in {choice}. Here we go: three, two, one..."
                    f"\n \n**{pick}!** Congrats, {ctx.author.mention}! "
                    f"At **{choice}:1 odds**, your payout is **{payout} gaybucks**."
                ),
                color=discord.Color.green()
            )
            embed.add_field(name="Balance", value=f"You now have {balance} gaybucks.",
                            inline=False)

            if mysql.check_leaderboard("Odds", ctx.author, payout):
                await ctx.send("New Odds high score!")
        else:
            balance = mysql.update_balance(ctx.author, -bet)
            mysql.add_to_lottery(self.bot, ctx.guild, bet)
            embed = discord.Embed(
                title="Odds",
                description=(
                    f"You chose 1 in {choice}. Here we go: three, two, one..."
                    f"\n \n**{pick}!** Sorry,{ctx.author.mention}, better luck next time."
                ),
                color=discord.Color.red()
            )
            embed.add_field(name="Balance", value=f"You now have {balance} gaybucks.",
                            inline=False)

        await message2.edit(embed=embed)

    @commands.command(brief="(2 Players) Higher card wins.",
                      discription="Bet with a friend to see who wins with a higher card.")
    async def cardcut(self, ctx: commands.Context, member: discord.Member, bet: int):
        checks.is_valid_bet(ctx, ctx.author, bet)

        options = ["❌", "✅"]
        suits = ["♠️", "♥️", "♣️", "♦️"]
        values = ["2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🇯", "🇶", "🇰", "🇦"]

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

        for option in options:
            await message.add_reaction(option)

        def react_check(reaction: discord.Reaction, user: discord.User):
            if user.id == player2.id and reaction.message.id == message.id and str(reaction) in options:
                return checks.is_valid_bet(ctx, user, bet)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            return await message.delete()

        if str(reaction) == "❌":
            embed = discord.Embed(
                title="Card Cutting",
                description=(
                    f"{player2.mention} has declined the bet."
                    f"\n \nUser: {ctx.author.mention}"
                ),
                color=discord.Color.red()
            )
            return await message.edit(embed=embed)

        await message.delete()

        pot = bet * 2

        # Game starts
        description = (
            f"Bets are in, with a total pot of **{pot} gaybucks**. {player1.mention}, {player2.mention}, you have 60 seconds " 
            f"while I'm shuffling to hit ❌ for me to stop on a card. The player with the higher " 
            f"card wins!\n\n__**Cards:**__"
        )
        embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
        card_cut = await ctx.send(embed=embed)
        await card_cut.add_reaction("❌")

        used = int

        def generate_card():
            nonlocal used

            suit_num = random.randint(0, 3)
            number_num = random.randint(0, 12)

            if (number_num * 10) + suit_num == used:
                return generate_card()

            used = (number_num * 10) + suit_num

            suit = suits[suit_num]
            number = values[number_num]
            return number + suit, (number_num * 10) + suit_num

        def check(reaction: discord.Reaction, user: discord.User):
            return user in players and reaction.message.id == card_cut.id and str(reaction) == "❌"

        cards = {}
        for _ in range(2):
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                players.remove(user)
                cards[user] = generate_card()

                description += f"\n{user.mention} {cards[user][0]}"
                embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
                await card_cut.edit(embed=embed)
            except asyncio.TimeoutError:
                cards[player1] = generate_card()
                cards[player2] = generate_card()

                description += (
                    f"\n{player1.mention} {cards[player1][0]}\n{player2.mention} {cards[player2][0]}"
                    f"\n(*dealer hit the bottom of the deck*)"
                )
                embed = discord.Embed(title="Card Cutting", description=description, color=discord.Color.green())
                await card_cut.edit(embed=embed)
                break

        final = sorted(cards.items(), key=lambda x: x[1][1], reverse=True)
        winner = final[0][0]
        loser = final[1][0]

        winner_balance = mysql.update_balance(winner, pot - bet)
        loser_balance = mysql.update_balance(loser, -bet)
        mysql.add_to_lottery(self.bot, ctx.guild, bet)

        embed = discord.Embed(title="Card Cutting",
                              description=f"Congratulations, {winner.mention}! You've won **{pot} gaybucks**!",
                              color=discord.Color.green())
        embed.add_field(
            name=f"Balances",
            value=(
                f"{winner.mention}: {winner_balance} GB\n"
                f"{loser.mention}: {loser_balance} GB"
            ),
            inline=False
        )
        await ctx.send(embed=embed)

        if mysql.check_leaderboard("Cardcut", winner, pot):
            await ctx.send("New Cardcut high score!")

    @commands.command(brief="(1 Player) Horse race.",
                      discription="Bet with 5x odds on which of the five horses will reach the finish line first.")
    async def horse(self, ctx: commands.Context, bet: int):        
        checks.is_valid_bet(ctx, ctx.author, bet)

        horses = [
            "🏁- - - - - 🏇**1.**",
            "🏁- - - - - 🏇**2.**",
            "🏁- - - - - 🏇**3.**",
            "🏁- - - - - 🏇**4.**",
            "🏁- - - - - 🏇**5.**"
        ]

        options = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        description = (
            "Choose your horse!\n \n"
            f"{horses[0]}\n \n{horses[1]}\n \n{horses[2]}\n \n{horses[3]}" 
            f"\n \n{horses[4]}\n \nUser: {ctx.author.mention}"
        )
        embed = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
        message = await ctx.send(embed=embed)

        for option in options:
            await message.add_reaction(option)

        def react_check(reaction: discord.Reaction, user: discord.User):
            return user.id == ctx.author.id and reaction.message.id == message.id and str(reaction) in options

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
            guess = options.index(str(reaction)) + 1
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
            profit = bet * 2
            balance = mysql.update_balance(ctx.author, profit)
            description = f"**Horse {winner} Wins!**\n{ctx.author.mention} You have won {bet * 3} gaybucks!"
            color = discord.Color.green()

        elif int(third) == guess or (int(second) == guess and tie):
            profit = bet
            balance = mysql.update_balance(ctx.author, profit)
            description = f"**Horse {second} Comes in Second (tie)!**\n{ctx.author.mention} You have won {bet * 2} gaybucks!"
            color = discord.Color.green()          

        elif int(second) == guess:
            profit = bet
            balance = mysql.update_balance(ctx.author, profit)
            description = f"**Horse {second} Comes in Second!**\n{ctx.author.mention} You have won {bet * 2} gaybucks!"
            color = discord.Color.green()

        else:
            profit = -bet
            balance = mysql.update_balance(ctx.author, profit)
            mysql.add_to_lottery(self.bot, ctx.guild, bet)
            description = f"**Horse {winner} Wins**\n{ctx.author.mention} You have lost {bet} gaybucks."
            color = discord.Color.red()

        embed2 = discord.Embed(title=f"Horse Racing", description=description, color=color)
        embed2.add_field(name="Balance", value=f"You now have {balance} gaybucks", inline=False)
        await ctx.send(embed=embed2)

        if profit > 0 and mysql.check_leaderboard("Horse", ctx.author, bet * 2):
                await ctx.send("New Horse high score!")

    @commands.command(brief="(1 Player) Cash out before the crash.",
                      description="The multiplier and your payout will keep going higher. "
                                  "If it crashes before you stop it, you lose your bet.")
    async def crash(self, ctx: commands.Context, bet: int):
        checks.is_valid_bet(ctx, ctx.author, bet)

        multiplier = 1.0
        profit = (bet * multiplier) - bet

        embed = discord.Embed(title="Crash", color=discord.Color.green())
        embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Profit", value=f"{int(profit)} gaybucks", inline=True)
        embed.add_field(name="\u200b", value=f"React with :x: to stop!\nUser: {ctx.author.mention}", inline=False)
        message = await ctx.send(embed=embed)
        await message.add_reaction('❌')

        delay = 0.65

        while True:
            await asyncio.sleep(delay)

            start = time.time()

            new_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
            reactions = next((x for x in new_msg.reactions if x.emoji =='❌'), None)
            reactors = [user async for user in reactions.users()]
            if ctx.author in reactors:
                embed = discord.Embed(title="Crash", color=discord.Color.green())
                embed.add_field(name="Stopped at", value="{:.1f}x".format(multiplier), inline=True)
                break

            previous = 1/multiplier
            multiplier += 0.1
            profit = int(round((bet * multiplier) - bet))

            risk = 1/(previous*multiplier)
            if random.random() >= risk:
                profit = -bet
                mysql.add_to_lottery(self.bot, ctx.guild, bet)

                embed = discord.Embed(title="Crash", color=discord.Color.red())
                embed.add_field(name="Crashed at", value="{:.1f}x".format(multiplier), inline=True)
                break

            embed = discord.Embed(title="Crash", color=discord.Color.green())
            embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Profit", value=f"{profit} gaybucks", inline=True)
            embed.add_field(name="\u200b", value=f"React with :x: to stop!\nUser: {ctx.author.mention}", inline=False)
            await message.edit(embed=embed)

            # Smooth out tick speed
            total = time.time() - start
            offset = 1 - total - delay
            if offset > 0:
                await asyncio.sleep(offset)

        balance = mysql.update_balance(ctx.author, profit)
        
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Profit", value=f"{profit} gaybucks", inline=True)
        embed.add_field(name="Balance", value=f"You now have {balance} gaybucks.\n\nUser: {ctx.author.mention}",
                        inline=False)
        await message.edit(embed=embed)

        if mysql.check_leaderboard("Crash", ctx.author, int(round(profit))):
            await ctx.send("New Crash high score!")


    @commands.command(brief="(1 Player) How many squares can you clear?",
                      description="There are two mines in a field. "
                                  "Clear as many squares as you can before you blow up.")
    async def minesweeper(self, ctx: commands.Context, bet: int):
        checks.is_valid_bet(ctx, ctx.author, bet)

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

        indices = ["A", "B", "C", "D", "1", "2", "3", "4"]
        options = ["🇦", "🇧", "🇨", "🇩", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "❌"]

        bombs = []
        while len(bombs) < 2:
            new = random.choice(indices[:4]) + random.choice(indices[-4:])
            if new not in bombs:
                bombs.append(new)

        remaining = 16
        odds = (remaining - 2) / remaining
        cumulative_odds = odds

        next_score = int(round(bet/odds)) - bet
        total = 0

        embed = discord.Embed(title="Minesweeper", description=f"There are 2 bombs out there...",
                              color=discord.Color.green())
        embed.add_field(name="Next Score", value=f"+{next_score} gaybucks", inline=False)
        embed.add_field(name="Total Profit", value=f"{total} gaybucks", inline=False)
        embed.add_field(name="Odds of Scoring", value="{:.2f}%".format(odds * 100), inline=False)
        embed.add_field(name="\u200b", value=f"Select the row and column of the square you wish to reveal, or select ❌ to stop. Please wait until the reactions reset before inputting your next square.\nUser: {ctx.author.mention}", inline=False)
        message = await ctx.send(embed=embed)
        field_msg = await ctx.send(field)

        for option in options:
            await field_msg.add_reaction(option)

        # Just row and column names
        available = options[:-1]

        def check(reaction: discord.Reaction, user: discord.User):
            if user.id == ctx.author.id and reaction.message.id == field_msg.id and str(reaction) in options:
                if str(reaction) == "❌":
                    return True

                nonlocal available
                if str(reaction) in available:
                    index = options.index(str(reaction))

                    if index < 4:
                        available = available[-4:]
                        return True
                    elif index >= 4:
                        available = available[:4]
                        return True
            
            return False

        while True:
            try:
                first_reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                if str(first_reaction) == "❌":
                    break
                first_index = options.index(str(first_reaction))

                second_reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                if str(second_reaction) == "❌":
                    break
                second_index = options.index(str(second_reaction))

            except asyncio.TimeoutError:
                break

            if first_index < second_index:
                choice = indices[first_index] + indices[second_index]
            else: 
                choice = indices[second_index] + indices[first_index]

            if choice not in field:
                # Reset options
                available = options[:-1]

                await first_reaction.remove(ctx.author)
                await second_reaction.remove(ctx.author)
                continue

            if choice in bombs:
                field = field.replace(choice, '❌')
                bombs.remove(choice)
                field = field.replace(bombs[0], '💣')
                await field_msg.edit(content=field)

                balance = mysql.update_balance(ctx.author, -bet)
                mysql.add_to_lottery(self.bot, ctx.guild, bet)

                embed = discord.Embed(title="Minesweeper", color=discord.Color.red())
                embed.add_field(name="KABOOM!", value=f"{ctx.author.mention} You lost {bet} gaybucks",
                                inline=False)
                embed.add_field(name="Balance", value=f"You now have {balance} gaybucks",
                                inline=False)
                await ctx.send(embed=embed)
                return

            field = field.replace(choice, '✅')
            await field_msg.edit(content=field)

            total += next_score  # update total score with previous prediction
            remaining -= 1  # one less square
            # Win!
            if remaining - 2 == 0:
                break

            # Calc next odds and score
            odds = (remaining - 2) / remaining
            cumulative_odds *= odds
            next_score = int(round(bet/cumulative_odds)) - bet - total

            embed = discord.Embed(title="Minesweeper", description=f"There are 2 bombs out there...",
                                  color=discord.Color.green())
            embed.add_field(name="Next Score", value=f"+{next_score} gaybucks", inline=False)
            embed.add_field(name="Total Profit", value=f"{total} gaybucks", inline=False)
            embed.add_field(name="Odds of Scoring", value="{:.2f}%".format(odds * 100), inline=False)
            embed.add_field(name="\u200b", value=f"Select the row and column, or ❌ to stop.\nUser: {ctx.author.mention}", inline=False)
            await message.edit(embed=embed)

            # Reset options
            available = options[:-1]

            await first_reaction.remove(ctx.author)
            await second_reaction.remove(ctx.author)

        # Loop broken by either stopping or winning
        for i in range(len(bombs)):
            field = field.replace(bombs[i], '💣')
        await field_msg.edit(content=field)

        balance = mysql.update_balance(ctx.author, total)

        embed = discord.Embed(title="Minesweeper", color=discord.Color.green())
        embed.add_field(name="Winner!", value=f"{ctx.author.mention} You have won {total} gaybucks",
                        inline=False)
        embed.add_field(name="Balance", value=f"You now have {balance} gaybucks",
                        inline=False)
        await ctx.send(embed=embed)

        if mysql.check_leaderboard("Minesweeper", ctx.author, total):
                await ctx.send("New Minesweeper high score!")
        return

    @commands.command(brief="(1+ Players) Smoke or fire, the card game.",
                      description="Just like the first four rounds of the card game Smoke or Fire. "
                                  "You can play by yourself or up to 13 players.")
    async def smokefire(self, ctx: commands.Context, bet: int):
        checks.is_valid_bet(ctx, ctx.author, bet)

        options = ["❌", "✅"]
        smoke_fire = ["💨", "🔥"]
        higher_lower = ["⬆", "⬇"]
        in_out = ["↔", "↩"]

        suits = ["♠️", "♥️", "♣️", "♦️"]
        values = ["2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🇯", "🇶", "🇰", "🇦"]

        players = [ctx.author]

        description = (
            f"A round of smoke or fire is about to start. Buy-in is **{bet} gaybucks**. React with ✅ to join! Game starts in 30 seconds..."
            f"\n{ctx.author.mention}, you can hit ❌ to start earlier."
        )

        embed = discord.Embed(title="Smoke or Fire", description=description, color=discord.Color.green())
        embed.add_field(name="Players:", value=players[0].mention, inline=False)
        message = await ctx.send(embed=embed)

        for option in options:
            await message.add_reaction(option)

        blacklist = []

        def react_check(reaction: discord.Reaction, user: discord.User):
            if reaction.message.id == message.id and user.id not in blacklist and not user.bot:
                if str(reaction) == "❌" and user.id == ctx.author.id:
                    return True
                elif str(reaction) == "✅" and user.id != ctx.author.id:
                    blacklist.append(user.id)
                    return checks.is_valid_bet(ctx, user, bet)

                return False
    
        start = time.time()
        while time.time() - start < 30 and len(blacklist) <= 13:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=react_check)
                if str(reaction) == "❌":
                    break
        
                players.append(user)

                embed = discord.Embed(title="Smoke or Fire", description=description, color=discord.Color.green())

                value = ""
                for player in players:
                    value += f"{player.mention}\n"
                embed.add_field(name="Players:", value=value, inline=False)

                await message.edit(embed=embed)
                
            except asyncio.TimeoutError:
                return await message.delete()

            except commands.CommandError:
                continue

        await message.clear_reactions()

        game = {player: {'cards': [], 'profit': 0, 'round': 1,'inactive': False} for player in players}
        used = []

        def game_status() -> str:
            description = ""
            for player, values in game.items():
                cards = '  '.join(x[0] + x[1] for x in values['cards'])
                description += f"{player.mention}: {cards} \u200b\u200b **{values['profit']} GB**"

                if values['inactive']:
                    description += " (removed for inactivity)"

                description += "\n"

            return description

        def generate_card() -> tuple[str, str]:
            nonlocal used

            suit_num = random.randint(0, 3)
            value_num = random.randint(0, 12)

            suit = suits[suit_num]
            value = values[value_num]
            card = (value, suit)

            # No duplicate cards
            if card in used:
                return generate_card()

            used.append(card)
            return card

        i = 1
        new_round = True
        while i < 5:
            current_player = players[0]
            game[current_player]['round'] += 1

            description = f"It's your turn, {current_player.mention}."

            if i == 1:
                description += f" Smoke or Fire? For **{int(round(bet * 0.1 * i))} gaybuck(s)**."
                emoji_list = smoke_fire
            elif i == 2:
                description += f" Higher or Lower? For **{int(round(bet * 0.1 * i))} gaybuck(s)**."
                emoji_list = higher_lower
            elif i == 3:
                description += f" In Between or Out? For **{int(round(bet * 0.1 * i))} gaybuck(s)**."
                emoji_list = in_out
            elif i == 4:
                description += f" Guess the suit. For **{int(round(bet * 0.1 * i))} gaybuck(s)**."
                emoji_list = suits

            embed = discord.Embed(title="Smoke or Fire", description=description, color=discord.Color.green())
            embed.add_field(name="Players:", value=game_status(), inline=False)
            await message.edit(embed=embed)

            if new_round:
                await message.clear_reactions()

                for emoji in emoji_list:
                    await message.add_reaction(emoji)

                new_round = False

            def react_check(reaction: discord.Reaction, user: discord.User):
                return reaction.message.id == message.id and user.id == current_player.id

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
            except asyncio.TimeoutError:
                game[current_player]['profit'] -= int(round(bet * 0.1 * i))
                game[current_player]['inactive'] = True

                players.remove(current_player)
                if not players:
                    # No players left, end the game
                    break

                if game[players[0]]['round'] != i:
                    i += 1
                    new_round = True
                continue

            card = generate_card()

            # Add card to player's list
            game[current_player]['cards'].append(card)

            if i == 1:
                if ((reaction.emoji == "💨" and card[1] in ("♠️", "♣️")) or 
                        (reaction.emoji == "🔥" and card[1] in ("♥️", "♦️"))):
                    outcome = int(round(bet * 0.1 * i))
                else:
                    outcome = -int(round(bet * 0.1 * i))
            elif i == 2:
                card_value = values.index(card[0])
                first_card_value = values.index(game[current_player]['cards'][0][0])

                if ((reaction.emoji == "⬆" and card_value > first_card_value) or 
                        (reaction.emoji == "⬇" and card_value < first_card_value)):
                    outcome = int(round(bet * 0.1 * i))
                else:
                    outcome = -int(round(bet * 0.1 * i))
            elif i == 3:
                card_value = values.index(card[0])
                first_card_value = values.index(game[current_player]['cards'][0][0])
                second_card_value = values.index(game[current_player]['cards'][1][0])

                value_range = range(*sorted((first_card_value, second_card_value)))

                if ((reaction.emoji == "↔" and card_value in value_range) or 
                        (reaction.emoji == "↩" and card_value not in value_range)):
                    outcome = int(round(bet * 0.1 * i))
                else:
                    outcome = -int(round(bet * 0.1 * i))
            elif i == 4:
                if reaction.emoji == card[1]:
                    outcome = int(round(bet * 0.1 * i))
                else:
                    outcome = -int(round(bet * 0.1 * i))

            game[current_player]['profit'] += outcome

            embed = discord.Embed(title="Smoke or Fire", description=description, color=discord.Color.green())
            embed.add_field(name="Players:", value=game_status(), inline=False)
            await message.edit(embed=embed)

            # Rotate players list
            players = players[1:] + players[:1]
            if game[players[0]]['round'] != i:
                i += 1
                new_round = True

        await asyncio.sleep(2)

        await message.clear_reactions()

        description = "Congratulations on your winnings... or losings!"

        value = ""
        for player, values in game.items():
            balance = mysql.update_balance(player, values['profit'])
            if values['profit'] > 0:
                if mysql.check_leaderboard("SmokeOrFire", player, values['profit']):
                    await ctx.send("New Smoke or Fire high score!")
                mysql.add_to_lottery(self.bot, ctx.guild, bet)

            value += f"{player.mention}: {balance} GB\n"

        embed = discord.Embed(title="Smoke or Fire", description=description, color=discord.Color.green())
        embed.add_field(name="Balance:", value=value, inline=False)
        await message.edit(embed=embed)


    # TODO This is much more complicated than I anticipated. Actual board and logic will required a lot of work.
    @commands.command(hidden=True)
    async def connect4(self, ctx: commands.Context, member: discord.Member, bet: int):
        checks.is_valid_bet(ctx, ctx.author, bet)

        # if member.id == ctx.author.id:

        board = [
            "``` -----------------------------------", 
            "| ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |", 
            " -----------------------------------", 
            "| ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |", 
            " -----------------------------------", 
            "| ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |", 
            " -----------------------------------", 
            "| ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |", 
            " -----------------------------------", 
            "| ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |",
            " -----------------------------------", 
            "| ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |", 
            " -----------------------------------```"
        ]

        yes_no = ["❌", "✅"]
        options = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]

        players = [ctx.author]


        if member.bot:
            description = (
                f"So, you've chosen death. I'll let you go first--not like it'll matter."
                f"\n \nUser: {ctx.author.mention}"
            )
        else:
            description = (
                f"{member.mention} Do you accept the challenge? React to this message accordingly."
                f"\n \nUser: {ctx.author.mention}"
            )

        embed = discord.Embed(title="Connect Four", description=description, color=discord.Color.green())
        message = await ctx.send(embed=embed)

        if not member.bot:
            for reaction in yes_no:
                await message.add_reaction(reaction)

            def react_check(reaction: discord.Reaction, user: discord.User):
                if user.id == member.id and reaction.message.id == message.id and str(reaction) in yes_no:
                    return checks.is_valid_bet(ctx, user, bet)

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
            except asyncio.TimeoutError:
                return await message.delete()

            if str(reaction) == "❌":
                return await message.delete()

            await message.clear_reactions()

            players.append(member)

            description = (
                f"{member.mention}, you start."
                f"\n \nUsers: {ctx.author.mention} and {member.mention}"
            )

            embed = discord.Embed(title="Connect Four", description=description, color=discord.Color.green())
            await message.edit(embed=embed)

        board_msg = await ctx.send(board)

        for option in options:
            await board_msg.add_reaction(option)

        def react_check(reaction: discord.Reaction, user: discord.User):
            nonlocal players
            return user.id == players[0].id and reaction.message.id == message.id and str(reaction) in options


        timeout = False

        while True:
            if member.bot:
                return
            else:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
                except asyncio.TimeoutError:
                    timeout = True
                    break 



            players[1], players[0] = players[0], players[1]

        # players[0] timed out.
        if timeout:
            player2_bal = mysql.update_balance(players[1], bet * 2)
            player1_bal = mysql.update_balance(players[0], -bet)
            mysql.add_to_lottery(self.bot, ctx.guild, bet)

            description = f"Winner! Kinda. {member.mention} has forfeited (timeout)."
            embed = discord.Embed(title="Connect Four", description=description, color=discord.Color.green())
            embed.add_field(
                name=f"Balances",
                value=(
                    f"{players[1]}: {player2_bal} GB\n"
                    f"{players[0]}: {player1_bal} GB"
                ),
                    inline=False
                )
            return await ctx.send(embed=embed)

                


async def setup(bot):
    await bot.add_cog(Gambling(bot))
