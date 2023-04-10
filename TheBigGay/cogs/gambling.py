import random
import time
import asyncio
import discord
from discord import app_commands
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
        if message.author.bot:
            return            

        if message.channel.category.name == 'Gambling':
            await message.delete()

    @app_commands.command(description="Check who has won the most money in each of the gambling games.")
    async def leaderboard(self, interaction: discord.Interaction):
        leaderboard = mysql.get_leaderboard(interaction.guild)

        embed = discord.Embed(title="Leaderboard", color=discord.Color.purple())
        for row in leaderboard:
            game = row[0]
            member = interaction.guild.get_member(int(row[1]))
            score = row[2]
            embed.add_field(name=f"{game}", value=f"{member.name}\n*{score}GB*", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="(1 Player) What are the odds I give you money? (1 in...?)")
    @app_commands.describe(odds="one in ...? (2-10)", bet="your bet in gaybucks")
    async def odds(self, interaction: discord.Interaction, odds: int, bet: int):
        checks.is_valid_bet(interaction.channel, interaction.user, bet)

        if not 2 <= odds <= 10:
            return await interaction.response.send_message("Make sure your 'odds' input is an integer between 2 and 10.", ephemeral=True, delete_after=5)

        options = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        embed = discord.Embed(
            title="Odds",
            description=(
                f"You chose 1 in {odds} odds. Here we go: three, two, one..."
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)   
        message = await interaction.original_response()

        for i in range(odds):
            await message.add_reaction(options[i])

        def react_check(reaction: discord.Reaction, user: discord.User):
            return user.id == interaction.user.id and reaction.message.id == message.id and str(reaction) in options

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            await interaction.delete_original_response()
            return

        result = options.index(str(reaction)) + 1
        pick = random.randint(1, odds)

        if result == pick:
            payout = bet * odds
            balance = mysql.update_balance(interaction.user, payout - bet)

            embed.description += f"\n\n...**{pick}!** Congrats, {interaction.user.mention}! "\
                f"At **{odds}:1 odds**, your payout is **{payout} gaybucks**."

            embed.add_field(name="Balance", value=f"You now have {balance} gaybucks.",
                            inline=False)

            if mysql.check_leaderboard("Odds", interaction.user, payout):
                await interaction.followup.send(f"New Odds high score of **{payout}GB**, set by {interaction.user.mention}!")
        else:
            balance = mysql.update_balance(interaction.user, -bet)
            mysql.add_to_lottery(self.bot.application_id, interaction.guild, bet)

            embed.description += f"\n\n...**{pick}!** Sorry,{interaction.user.mention}. Better luck next time."
            embed.color = discord.Color.red()

            embed.add_field(name="Balance", value=f"You now have {balance} gaybucks.",
                            inline=False)

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(description="(2 Players) Bet with a friend to see who wins with a higher card.")
    @app_commands.describe(member="player 2", bet="your bet in gaybucks")
    async def cardcut(self, interaction: discord.Interaction, member: discord.Member, bet: int):
        checks.is_valid_bet(interaction.channel, interaction.user, bet)

        options = ["❌", "✅"]
        suits = ["♠️", "♥️", "♣️", "♦️"]
        values = ["2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🇯", "🇶", "🇰", "🇦"]

        player1 = interaction.user
        player2 = member
        players = [player1, player2]

        if player1.id == player2.id:
            return await interaction.response.send_message("You can't just play with yourself in front of everyone!", ephemeral=True, delete_after=5)
        elif player2.bot:
            return await interaction.response.send_message("I'm sure you can find a human to play with!", ephemeral=True, delete_after=5)

        # Initial prompt to get player 2's consent
        embed = discord.Embed(
            title="Card Cutting",
            description=(
                f"A card-cutting bet has started against "
                f"{player2.mention}. Do you accept?"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for option in options:
            await message.add_reaction(option)

        def react_check(reaction: discord.Reaction, user: discord.User):
            if user.id == player2.id and reaction.message.id == message.id and str(reaction) in options:
                return checks.is_valid_bet(interaction.channel, user, bet)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
        except asyncio.TimeoutError:
            embed.description += f"\n\n{player2.mention} did not respond."
            embed.color = discord.Color.red()
            return await interaction.edit_original_response(embed=embed)

        if str(reaction) == "❌":
            embed.description = f"{player2.mention} has declined the bet."
            embed.color = discord.Color.red()
            return await interaction.edit_original_response(embed=embed)

        pot = bet * 2

        # Game starts
        description = (
            f"Bets are in, with a total pot of **{pot} gaybucks**. {player1.mention}, {player2.mention}, you have 60 seconds " 
            f"while I'm shuffling to hit ❌ for me to stop on a card. The player with the higher " 
            f"card wins!\n\n__**Cards:**__"
        )
        embed.description = description
        await interaction.edit_original_response(embed=embed)
        card_cut = await interaction.original_response()
        await card_cut.clear_reaction("✅")

        used = int()

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
        for i in range(2):
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                players.remove(user)
                cards[user] = generate_card()

                description += f"\n{user.mention} {cards[user][0]}"
                embed.description = description
                if i == 0:
                    await interaction.edit_original_response(embed=embed)
            except asyncio.TimeoutError:
                cards[player1] = generate_card()
                cards[player2] = generate_card()

                description += (
                    f"\n{player1.mention} {cards[player1][0]}\n{player2.mention} {cards[player2][0]}"
                    f"\n(*dealer hit the bottom of the deck*)"
                )
                embed.description = description
                await interaction.edit_original_response(embed=embed)
                break

        final = sorted(cards.items(), key=lambda x: x[1][1], reverse=True)
        winner = final[0][0]
        loser = final[1][0]

        winner_balance = mysql.update_balance(winner, pot - bet)
        loser_balance = mysql.update_balance(loser, -bet)

        embed.description = embed.description.split("\n\n")[1] + f"\n\nCongratulations, {winner.mention}! You've won **{pot} gaybucks**!"
        embed.add_field(
            name=f"Balances",
            value=(
                f"{winner.mention}: {winner_balance}GB\n"
                f"{loser.mention}: {loser_balance}GB"
            ),
            inline=False
        )
        await interaction.edit_original_response(embed=embed)

        mysql.add_to_lottery(self.bot.application_id, interaction.guild, bet)

        if mysql.check_leaderboard("Cardcut", winner, pot):
            await interaction.followup.send(f"New Cardcut high score of **{pot}GB**, set by {winner.mention}!")

    @app_commands.command(description="(1 Player) Bet with 5x odds on which of the five horses will reach the finish line first.")
    @app_commands.describe(bet="your bet in gaybucks")
    async def horse(self, interaction: discord.Interaction, bet: int):        
        checks.is_valid_bet(interaction.channel, interaction.user, bet)

        horses = [
            "🏁- - - - - 🏇**1.**",
            "🏁- - - - - 🏇**2.**",
            "🏁- - - - - 🏇**3.**",
            "🏁- - - - - 🏇**4.**",
            "🏁- - - - - 🏇**5.**"
        ]

        options = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        description = (
            "Choose your horse!\n\n"
            f"{horses[0]}\n\n{horses[1]}\n\n{horses[2]}\n\n{horses[3]}" 
            f"\n\n{horses[4]}"
        )
        embed = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for option in options:
            await message.add_reaction(option)

        def react_check(reaction: discord.Reaction, user: discord.User):
            return user.id == interaction.user.id and reaction.message.id == message.id and str(reaction) in options

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
            guess = options.index(str(reaction)) + 1
        except asyncio.TimeoutError:
            return await interaction.delete_original_response()

        tied = []
        while True:
            choice = random.randint(0, 4)

            horses[choice] = horses[choice][0] + horses[choice][3:]

            description = (
                f"And they're off!\n\n"
                f"{horses[0]}\n\n{horses[1]}\n\n{horses[2]}\n\n{horses[3]}"
                f"\n\n{horses[4]}"
            )
            embed = discord.Embed(title=f"Horse Racing", description=description, color=discord.Color.green())
            await message.edit(embed=embed)

            if horses[choice][1] == "🏇":
                winner = choice + 1
                sorted_horses = sorted(horses, key=len)
                second = int(sorted_horses[1][-4])

                for i in range(2, len(sorted_horses)):
                    if len(sorted_horses[1]) == len(sorted_horses[i]):
                        if i == 2:
                            tied.append(int(sorted_horses[1][-4]))
                        tied.append(int(sorted_horses[i][-4]))
                break

            await asyncio.sleep(1)

        if winner == guess:
            profit = bet * 2
            embed.description += f"\n\n**Horse {winner} Wins!**\nYou have won **{bet * 3} gaybucks**!"     

        elif tied and guess in tied:
            profit = bet
            embed.description += f"\n\n**Horse {guess} Comes in Second (tie)!**\nYou have won **{bet * 2} gaybucks**!"

        elif second == guess:
            profit = bet
            embed.description += f"\n\n**Horse {second} Comes in Second!**\nYou have won **{bet * 2} gaybucks**!"
                
        else:
            profit = -bet
            mysql.add_to_lottery(self.bot.application_id, interaction.guild, bet)
            embed.description += f"\n\n**Horse {winner} Wins**\nYou have lost **{bet} gaybucks**."
            embed.color = discord.Color.red()

        balance = mysql.update_balance(interaction.user, profit)

        embed.add_field(name="Balance", value=f"You now have {balance} gaybucks", inline=False)
        await interaction.edit_original_response(embed=embed)

        if profit > 0 and mysql.check_leaderboard("Horse", interaction.user, bet + profit):
                await interaction.followup.send(f"New Horse high score of **{bet + profit}GB**, set by {interaction.user.mention}!")

    @app_commands.command(description="(1 Player) Cash out before the crash.")
    @app_commands.describe(bet="your bet in gaybucks")
    async def crash(self, interaction: discord.Interaction, bet: int):
        checks.is_valid_bet(interaction.channel, interaction.user, bet)

        multiplier = 1.0
        profit = int(round((bet * multiplier) - bet))

        embed = discord.Embed(title="Crash", color=discord.Color.green())
        embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Profit", value=f"{int(profit)} gaybucks", inline=True)
        embed.add_field(name="\u200b", value=f"React with :x: to stop!", inline=False)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction('❌')

        await asyncio.sleep(1)

        while True:
            start = time.time()

            new_msg = discord.utils.get(self.bot.cached_messages, id=message.id)

            reaction = next((x for x in new_msg.reactions if x.emoji == '❌'), None)
            if reaction.count > 1:
                reactors = [user async for user in reaction.users()]

                if interaction.user in reactors:
                    embed = discord.Embed(title="Crash", color=discord.Color.green())
                    embed.add_field(name="Stopped at", value="{:.1f}x".format(multiplier), inline=True)
                    break

            previous = 1/multiplier
            multiplier += 0.1
            profit = int(round((bet * multiplier) - bet))

            risk = 1/(previous*multiplier)
            if random.random() >= risk:
                profit = -bet
                mysql.add_to_lottery(self.bot.application_id, interaction.guild, bet)

                embed = discord.Embed(title="Crash", color=discord.Color.red())
                embed.add_field(name="Crashed at", value="{:.1f}x".format(multiplier), inline=True)
                break

            embed = discord.Embed(title="Crash", color=discord.Color.green())
            embed.add_field(name="Multiplier", value="{:.1f}x".format(multiplier), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Profit", value=f"{profit} gaybucks", inline=True)
            embed.add_field(name="\u200b", value=f"React with :x: to stop!", inline=False)

            await interaction.edit_original_response(embed=embed)

            # Smooth out tick speed to be roughly 1 second
            total = time.time() - start
            offset = 1 - total

            if offset > 0:
                await asyncio.sleep(offset)

        balance = mysql.update_balance(interaction.user, profit)
        
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Profit", value=f"{profit} gaybucks", inline=True)
        embed.add_field(name="Balance", value=f"You now have {balance} gaybucks.",
                        inline=False)
        await interaction.edit_original_response(embed=embed)

        if mysql.check_leaderboard("Crash", interaction.user, profit):
            await interaction.followup.send(f"New Crash high score of **{profit}GB**, set by {interaction.user.mention}!")


    @app_commands.command(description="(1 Player) How many squares can you clear?")
    @app_commands.describe(bet="your bet in gaybucks")
    async def minesweeper(self, interaction: discord.Interaction, bet: int):
        checks.is_valid_bet(interaction.channel, interaction.user, bet)

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
        embed.add_field(name="\u200b", value=f"Select the row and column of the square you wish to reveal, or select ❌ to stop. Please wait until the reactions reset before inputting your next square.", inline=False)
        embed.add_field(name="\u200b", value=field, inline=False)
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for option in options:
            await message.add_reaction(option)

        # Just row and column names
        available = options[:-1]

        def check(reaction: discord.Reaction, user: discord.User):
            if user.id == interaction.user.id and reaction.message.id == message.id and str(reaction) in options:
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

            choice = indices[min(first_index, second_index)] + indices[max(first_index, second_index)]

            if choice not in field:
                # Choice was previously selected already. Reset options
                available = options[:-1]

                await first_reaction.remove(interaction.user)
                await second_reaction.remove(interaction.user)
                continue

            if choice in bombs:
                field = field.replace(choice, '❌')
                bombs.remove(choice)
                field = field.replace(bombs[0], '💣')
                embed.set_field_at(-1, name="\u200b", value=field, inline=False)

                balance = mysql.update_balance(interaction.user, -bet)

                embed.color=discord.Color.red()
                embed.add_field(name="KABOOM!", value=f"You lost **{bet} gaybucks**",
                                inline=False)
                embed.add_field(name="Balance", value=f"You now have {balance} gaybucks",
                                inline=False)
                await interaction.edit_original_response(embed=embed)

                mysql.add_to_lottery(self.bot.application_id, interaction.guild, bet)
                return

            field = field.replace(choice, '✅')
            # embed.set_field_at(-1, name="\u200b", value=field, inline=False)
            # await interaction.edit_original_response(embed=embed)

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
            embed.add_field(name="\u200b", value=f"Select the row and column, or ❌ to stop.", inline=False)
            embed.add_field(name="\u200b", value=field, inline=False)

            await message.edit(embed=embed)

            # Reset options
            available = options[:-1]

            await first_reaction.remove(interaction.user)
            await second_reaction.remove(interaction.user)

        # Loop broken by either stopping or winning
        for i in range(len(bombs)):
            field = field.replace(bombs[i], '💣')
        embed.set_field_at(-1, name="\u200b", value=field, inline=False)

        balance = mysql.update_balance(interaction.user, total)

        embed.add_field(name="Winner!", value=f"You have won **{total} gaybucks**",
                        inline=False)
        embed.add_field(name="Balance", value=f"You now have {balance} gaybucks",
                        inline=False)
        await interaction.edit_original_response(embed=embed)

        if mysql.check_leaderboard("Minesweeper", interaction.user, total):
                await interaction.followup.send(f"New Minesweeper high score of **{total}GB**, set by {interaction.user.mention}!")

    @app_commands.command(description="(1-13 Players) Smoke or fire, the card game")
    @app_commands.describe(bet="your bet in gaybucks")
    async def smokefire(self, interaction: discord.Interaction, bet: int):
        checks.is_valid_bet(interaction.channel, interaction.user, bet)

        options = ["❌", "✅"]
        smoke_fire = ["💨", "🔥"]
        higher_lower = ["⬆", "⬇"]
        in_out = ["↔", "↩"]

        suits = ["♠️", "♥️", "♣️", "♦️"]
        values = ["2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "🇯", "🇶", "🇰", "🇦"]

        players = [interaction.user]

        description = (
            f"A round of smoke or fire is about to start. Buy-in is **{bet} gaybucks**. React with ✅ to join! Game starts in 30 seconds..."
            f"\n{interaction.user.mention}, you can hit ❌ to start earlier."
        )

        embed = discord.Embed(title="Smoke or Fire", description=description, color=discord.Color.green())
        embed.add_field(name="Players:", value=players[0].mention, inline=False)
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for option in options:
            await message.add_reaction(option)

        blacklist = []

        def react_check(reaction: discord.Reaction, user: discord.User):
            if reaction.message.id == message.id and user.id not in blacklist and not user.bot:
                if str(reaction) == "❌" and user.id == interaction.user.id:
                    return True
                elif str(reaction) == "✅" and user.id != interaction.user.id:
                    blacklist.append(user.id)
                    return checks.is_valid_bet(interaction.channel, user, bet)

                return False
    
        start = time.time()
        while time.time() - start < 30 and len(players) <= 13:
            timeout = 30 - (time.time() - start)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=timeout, check=react_check)
                if str(reaction) == "❌":
                    break
        
                players.append(user)

                value = ""
                for player in players:
                    value += f"{player.mention}\n"
                embed.set_field_at(-1, name="Players:", value=value)

                await interaction.edit_original_response(embed=embed)
                
            except asyncio.TimeoutError:
                continue

            except app_commands.AppCommandError:
                continue

        await message.clear_reactions()

        game = {player: {'cards': [], 'profit': 0, 'round': 1,'inactive': False} for player in players}
        used = []

        def game_status() -> str:
            description = ""
            for player, values in game.items():
                cards = '  '.join(x[0] + x[1] for x in values['cards'])
                description += f"{player.mention}: {cards} \u200b\u200b **{values['profit']}GB**"

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

            embed.description = description
            embed.set_field_at(-1, name="Players:", value=game_status())
            await interaction.edit_original_response(embed=embed)

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

            embed.description = description
            embed.set_field_at(-1, name="Players:", value=game_status())
            await interaction.edit_original_response(embed=embed)

            # Rotate players list
            players = players[1:] + players[:1]
            if game[players[0]]['round'] != i:
                i += 1
                new_round = True

        await asyncio.sleep(2)

        await message.clear_reactions()

        value = ""
        for player, values in game.items():
            balance = mysql.update_balance(player, values['profit'])
            if values['profit'] > 0:
                if mysql.check_leaderboard("SmokeOrFire", player, values['profit']):
                    await interaction.followup.send(f"New Smoke or Fire high score of **{values['profit']}GB**, set by {interaction.user.mention}!")
                mysql.add_to_lottery(self.bot.application_id, interaction.guild, bet)

            value += f"{player.mention}: {balance}GB\n"

        embed.description = "Congratulations on your winnings... or losings!"
        embed.add_field(name="Balance:", value=value, inline=False)
        await interaction.edit_original_response(embed=embed)


    # TODO This is much more complicated than I anticipated. Actual board and logic will required a lot of work.
    @app_commands.command(description="(2 players) Connect 4")
    @app_commands.describe(member="player 2", bet="your bet in gaybucks")
    async def connect4(self, interaction: discord.Interaction, member: discord.Member, bet: int):
        checks.is_valid_bet(interaction.channel, interaction.user, bet)

        if member.id == interaction.user.id:
            return await interaction.response.send_message("You can't just play with yourself in front of everyone!", ephemeral=True, delete_after=5)

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

        player1 = interaction.user
        players = [player1]


        if member.bot:
            description = (f"So, you've chosen death. I'll let you go first--not like it'll matter.")
        else:
            description = (f"{member.mention}, do you accept the challenge? React to this message accordingly.")

        embed = discord.Embed(title="Connect Four", description=description, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
        message = interaction.original_response()

        if not member.bot:
            for reaction in yes_no:
                await message.add_reaction(reaction)

            def react_check(reaction: discord.Reaction, user: discord.User):
                if user.id == member.id and reaction.message.id == message.id and str(reaction) in yes_no:
                    return checks.is_valid_bet(reaction.channel, user, bet)

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=react_check)
            except asyncio.TimeoutError:
                return await interaction.delete_original_response()

            if str(reaction) == "❌":
                embed.description = f"{member.mention} has declined the bet."
                embed.color = discord.Color.red()
                return await interaction.edit_original_response(embed=embed)

            await message.clear_reactions()

            players.append(member)

            description = (
                f"{member.mention}, you start."
                f"\n \nPlayers: {players[0].mention} and {players[1].mention}"
            )

            embed = discord.Embed(title="Connect Four", description=description, color=discord.Color.green())
            await message.edit(embed=embed)
        else:
            players.append(self.bot)

            # TODO more here

        embed.add_field(name="\u200b", value=board, inline=False)
        await interaction.edit_original_response(embed=embed)

        for option in options:
            await message.add_reaction(option)

        def react_check(reaction: discord.Reaction, user: discord.User):
            nonlocal players
            return user.id == players[0].id and reaction.message.id == message.id and str(reaction) in options


        timeout = False

        # Game loop
        while True:
            if not member.bot:
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
            mysql.add_to_lottery(self.bot.application_id, interaction.guild, bet)

            embed.description = f"Winner! Kinda. {players[0].mention} has forfeited (timeout)."
            embed.add_field(
                name=f"Balances",
                value=(
                    f"{players[1].mention}: {player2_bal}GB\n"
                    f"{players[0].mention}: {player1_bal}GB"
                ),
                    inline=False
                )
            return await interaction.followup.send(embed=embed)

                


async def setup(bot):
    await bot.add_cog(Gambling(bot))
