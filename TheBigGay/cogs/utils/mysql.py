import discord
import pymysql
import os
from datetime import datetime
import pytz


# TODO Typecheck all of this. Put in function suggestions -> etc


config = {
    "host": os.environ['MYSQL_HOST'],
    "user": os.environ['MYSQL_USER'],
    "password": os.environ['MYSQL_PASSWORD'],
    "database": os.environ['MYSQL_DATABASE'],
    "connect_timeout": 86400
}

timezone = pytz.timezone("US/Pacific")

db = pymysql.connect(**config)
cursor = db.cursor()

# TODO Useful?
# cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")


# def ping():
#     while True:
#         try: 
#             db.ping()
#             break
#         except Exception as e:
#             print(e)
#             db.ping(True)

# TODO Implement this everywhere
def _test_connection(function: callable):
    while True:
        try:
            function()
            break
        except Exception as e:
            print(e)
            db.ping(reconnect=True)


def execute(sql: str, commit: bool = False) -> tuple[tuple, ...]:
    cursor.execute(sql)
    result = cursor.fetchall()

    if commit:
        db.commit()

    return result


def create_economy_table(guild_id: int):
    sql = f"CREATE TABLE {str(guild_id) + '_economy'} "\
        "(user_id VARCHAR(20) NOT NULL, "\
        "balance INTEGER(9) NOT NULL, "\
        "subsidy_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"\
        "PRIMARY KEY (user_id))" 
    execute(sql, commit=True)
    

def create_leaderboard_table(guild_id: int):
    sql = f"CREATE TABLE {str(guild_id) + '_leaderboard'} "\
        "(game VARCHAR(20) NOT NULL, "\
        "user_id VARCHAR(20) NOT NULL, "\
        "score INTEGER(9) NOT NULL,"\
        "date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"\
        "PRIMARY KEY (game))"
    execute(sql, commit=True)


def initialize_guild(guild: discord.Guild):
    sql = "SHOW TABLES LIKE '{}_economy'".format(str(guild.id))
    result = execute(sql)
    
    if not result:
        print(f"Creating economy table for guild, {guild.id}")
        create_economy_table(guild.id)

    sql = "SHOW TABLES LIKE '{}_leaderboard'".format(str(guild.id))
    result = execute(sql)

    if not result:
        print(f"Creating leaderboard table for guild, {guild.id}")
        create_leaderboard_table(guild.id)


def _check_status(table: str, user_id: str):
    _test_connection(lambda: cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE user_id={user_id})"))
    
    if cursor.fetchone()[0] != 1:
        cursor.execute(
            f"INSERT into {table}(user_id, balance, subsidy_date) "
			f"VALUES ({user_id}, 50, %s)", (datetime.now(timezone).date(),)
        )
        db.commit()


def _get_user_data(member: discord.Member):
    table = str(member.guild.id) + "_economy"
    user_id = str(member.id)

    _check_status(table, user_id)

    cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
    result = cursor.fetchone()

    return result


def get_balance(member: discord.Member):
    result = _get_user_data(member)

    return result[1]


def check_subsidy(member: discord.Member):
    result = _get_user_data(member)

    if result[1] < 100 and result[2].date() < datetime.now(timezone).date():
        return True
    else:
        return False


# Get all economy data
def get_economy(guild: discord.Guild):
    table = str(guild.id) + "_economy"

    cursor.execute(f"SELECT user_id, balance from {table}")
    result = cursor.fetchall()

    return result


# Updates a user's balance
async def update_balance(ctx, member: discord.Member, amt: int):
    table = str(member.guild.id) + "_economy"
    user_id = str(member.id)

    _check_status(table, user_id)

    cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
    result = cursor.fetchone()

    new_bal = max(result[1] + amt, 0)

    cursor.execute(f"UPDATE {table} SET balance={new_bal} WHERE user_id={user_id}")
    db.commit()

    if new_bal == 0:
        await ctx.send(f"{member.mention} is broke! LOL")


def subsidize(member: discord.Member):
    table = str(member.guild.id) + "_economy"
    user_id = str(member.id)

    _check_status(table, user_id)

    cursor.execute(f"SELECT * from {table} WHERE user_id={user_id}")
    result = cursor.fetchone()

    new_bal = max(result[1] + 50, 0)
    
    cursor.execute(
        f"UPDATE {table} " \
        f"SET balance={new_bal}, subsidy_date=%s " \
        f"WHERE user_id={user_id}", (datetime.now(timezone).date(),)
    )
    db.commit()


def get_leaderboard(guild: discord.Guild):
    table = str(guild.id) + "_leaderboard"

    cursor.execute(f"SELECT game, user_id, score, date from {table}")

    return cursor.fetchall()


def check_leaderboard(game: str, member: discord.Member, score: int) -> bool:
    table = str(member.guild.id) + "_leaderboard"

    cursor.execute(f"SELECT EXISTS(SELECT * from {table} WHERE game='{game}')")

    if cursor.fetchone()[0] == 1:
        cursor.execute(f"SELECT * from {table} WHERE game='{game}'")
        result = cursor.fetchone()

        if score > int(result[2]):
            # new high score
            cursor.execute(
                f"UPDATE {table} SET user_id={member.id}, score={score}, date=%s WHERE game='{game}'",
                (datetime.now(timezone).date(),)
            )
            db.commit()
            return True
    else:
        # new game high score
        cursor.execute(
            f"INSERT into {table}(game, user_id, score, date) " \
            f"VALUES ('{game}', {member.id}, {score}, %s)", 
            (datetime.now(timezone).date(),)
        )
        db.commit()
        return True

    return False
