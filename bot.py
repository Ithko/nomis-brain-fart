import logging
import os
from typing import Optional
import mysql.connector
import datetime
import math

import discord
import discord.ext.commands as commands
from discord.flags import Intents
from discord import app_commands
from discord.ext import tasks

import views

logger = logging.getLogger("mybot")

console_log = logging.StreamHandler()
#file_log = logging.FileHandler(filename="bot.log", encoding="utf-8", mode="w")
#file_log_format = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{")
#file_log.setFormatter(file_log_format)

logger.setLevel(logging.INFO)
#logger.addHandler(file_log)
logger.addHandler(console_log)

intents = discord.Intents.all()

class Bot(discord.Client):
    def db(self):
        return mysql.connector.connect(
                host = os.getenv("DB_HOST"),
                user = os.getenv("DB_USER"),
                password = os.getenv("DB_PASSWORD"),
                database = os.getenv("DB_DATABASE"),
            )
    def __init__(self, *, intents: Intents) -> None:
        super().__init__(intents=intents)
        
        db = self.db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM server_options")
        options = cursor.fetchall()

        self.server_options = dict()
        self.message_array = list()
        self.processed = False

        if options is not None:
            for option in options:
                self.server_options[option[0]] = option[1:]

        keys = self.server_options.keys()

        for guild in self.guilds:
            if guild.id not in keys:
                cursor.execute("INSERT INTO server_options VALUES(%s, %s)", (guild.id, False))
                self.server_options[guild.id] = [False,]

        cursor.close()
        db.commit()
        db.close()

    async def on_ready(self):
        logger.info(f'Logged on as {self.user}!')
        game = discord.Game("with the API")
        await self.change_presence(status=discord.Status.online, activity=game)

    # @tasks.loop(seconds=10)
    # async def process_messages(self):
    #     now = datetime.datetime.now()
    #     if now.minute == 0:
    #         if self.processed:
    #             return

    #         if len(self.message_array) == 0:
    #             self.processed = True;
    #             return

    #         channels_activity = dict()
    #         user_activity = dict()
    #         channel_user_activity = dict()

    #         for message in self.message_array:
    #             channels_activity[(message["server_id"], message["channel_id"])][0]+=1
    #             channels_activity[(message["server_id"], message["channel_id"])][1]+=len(message["content"])

    #             user_activity[(message["server_id"], message["user_id"])][0]+=1
    #             user_activity[(message["server_id"], message["user_id"])][1]+=len(message["content"])

    #             channel_user_activity[(message["server_id"], message["channel_id"], message["user_id"])][0]+=1
    #             channel_user_activity[(message["server_id"], message["channel_id"], message["user_id"])][1]+=len(message["content"])

    #         channels_values = []
    #         user_values = []
    #         channel_user_values = []

    #         current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:00:00")
    #         for key in channels_activity.keys():
    #             channels_values.append((key[0], key[1], channels_activity[key][0], channels_activity[key][1], current_time))

    #         for key in user_activity.keys():
    #             user_values.append((key[0], key[1], channels_activity[key][0], channels_activity[key][1], current_time))

    #         for key in channel_user_activity.keys():
    #             channel_user_values.append((key[0], key[1], key[2], channels_activity[key][0], channels_activity[key][1], current_time))

    #         db = self.db()
    #         cursor = db.cursor();
    #         cursor.executemany("INSERT INTO channel_activity VALUES (%s, %s, %s, %s, %s)", channels_values)
    #         cursor.executemany("INSERT INTO user_activity VALUES (%s, %s, %s, %s, %s)", user_values)
    #         cursor.executemany("INSERT INTO channel_user_activity VALUES (%s, %s, %s, %s, %s, %s)", channel_user_values)
    #         cursor.close()
    #         db.commit()
    #         db.close()
    #     else:
    #         self.processed = False

    async def on_member_join(self, member: discord.Member):
        logger.info(f'Member {member.name} joined with nick {member.nick} and id {member.id}!')
        memdate = member.created_at
        today = datetime.datetime.now(datetime.timezone.utc)
        if memdate > (today - datetime.timedelta(days=14)):
            response = discord.Embed()
            response.title = "Moderation message"
            response.description = "Account under 2 weeks old,\nplease rejoin when your account is old enough!"
            await member.send(embed=response)
            await member.kick(reason="Account under 2 weeks old")
            logger.info(f'Member {member.name} (id {member.id}) was kicked due to account not being old enough.')
        else:
            logger.info(f'Member {member.name} (id {member.id}) account is old enough.')

    # async def on_message(self, message: discord.Message):
    #     if (message.type == discord.MessageType.default or message.type == discord.MessageType.reply) and message.channel.type == discord.ChannelType.text:
    #         guild = message.channel.guild
    #         if guild is None:
    #             return
    #         guild_id = guild.id
    #         if self.server_options[guild_id][0] == 0:
    #             return
    #         content = message.content
    #         created_at = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
    #         author_id = message.author.id
    #         channel_id = message.channel.id
    #         self.message_array.append({"guild_id": guild_id, "content": content, "created_at": created_at, "author_id": author_id, "channel_id": channel_id})
    #         # cursor = self.db.cursor()
    #         # cursor.execute("INSERT INTO messages VALUE(%s, %s, %s, %s, %s)", (guild_id, content, created_at, author_id, channel_id))
    #         # cursor.close()


bot = Bot(intents=intents)
tree = discord.app_commands.CommandTree(bot)
owner_id = int(os.getenv("OWNER_ID"))
owner_name = os.getenv("OWNER_NAME")
if owner_name is None:
    logger.error("Owner name needs to be set")
    exit()

async def get_recaps(date: datetime.date, server_id: int):
    db = bot.db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, content FROM recaps WHERE date = %s AND server_id = %s", (date, server_id))
    out = cursor.fetchall()
    cursor.close()
    db.close()
    if out is None:
        return None
    recaps = []
    for line in out:
        recap = {"user": line[0], "content": line[1]}
        recaps.append(recap)
    return recaps

async def get_recap_list(member_id, guild_id):
    db = bot.db()
    cursor = db.cursor()
    cursor.execute("SELECT id, date, content from recaps where user_id = %s and server_id = %s", (member_id, guild_id))
    out = cursor.fetchall()
    cursor.close()
    db.close()
    if out is None:
        return None
    recaps = []
    for line in out:
        recap = {"id": line[0], "date": line[1], "content": line[2]}
        recaps.append(recap)
    return recaps

@app_commands.guild_only()
class GuildGroup(app_commands.Group):
    pass
recap_group = GuildGroup(name='recap', description='Recap commands!')

@recap_group.command(
        name="show",
        description="Prints a recap for given day"
        )
@app_commands.describe(
        date="Recap's date in YYYY-MM-DD format"
        )
@app_commands.guild_only()
async def recap(context: discord.Interaction, date: Optional[str]):
    if context.guild_id is None:
        await context.response.send_message(f"Available only on servers", ephemeral=True)
        return
    if date is not None:
        try:
            date_new = datetime.date.fromisoformat(date)
        except ValueError:
            await context.response.send_message(f"Wrong date format (correct format - YYYY-MM-DD)", ephemeral=True)
            return
    else:
        date_new = datetime.date.today()
    if not isinstance(context.user, discord.Member) or context.guild == None:
        await context.response.send_message(content="Available only on servers!", ephemeral=True)
        return
    response = discord.Embed()
    response.title = "Recap for "+date_new.strftime("%Y-%m-%d")+":\n"
    recaps = await get_recaps(date_new, context.guild_id)
    if recaps is None or len(recaps) == 0:
        response.description = "No recaps for that day!"
        await context.response.send_message(embed=response)
        return
    response.description = ""
    response.set_footer(text=("1/"+str(math.ceil(len(recaps)/5))))
    recaps_list = list()
    for recap in recaps[0:5]:
        response.description += f'<@{recap["user"]}>:\n{recap["content"]}\n\n'
    for recap in recaps:
        recaps_list.append(f'<@{recap["user"]}>:\n{recap["content"]}\n')
    recapview = views.ListView(response, context, recaps_list)
    await context.response.send_message(embed=response, view=recapview)


@recap_group.command(
        name="add",
        description="Removes a given recap"
        )
@app_commands.describe(
        text="Recap's content",
        date="Recap's date in YYYY-MM-DD format"
        )
@app_commands.guild_only()
async def recap_add(context: discord.Interaction, text: str, date: Optional[str]):
    if date is not None:
        try:
            date_new = datetime.date.fromisoformat(date)
        except ValueError:
            await context.response.send_message(f"Wrong date format (correct format - YYYY-MM-DD)", ephemeral=True)
            return
    else:
        date_new = datetime.date.today()

    if len(bytes(text, 'utf-8')) > 255:
        await context.response.send_message(f"Recap can't be longer than 255 chars", ephemeral=True)
        return

    try:
        db = bot.db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO recaps(server_id, user_id, date, content) VALUE(%s, %s, %s, %s)", (context.guild_id, context.user.id, date_new.strftime('%Y-%m-%d'), text))
        cursor.close()
        db.commit()
        db.close()
    except:
        await context.response.send_message(f"Something went wrong!", ephemeral=True)

    await context.response.send_message(f"Successfully added a new recap for date {date_new.strftime('%Y-%m-%d')}", ephemeral=True)

@recap_group.command(
        name="remove",
        description="Removes a given recap"
        )
@app_commands.describe(
        recap_id="Recap's id"
        )
@app_commands.guild_only()
async def recap_remove(context: discord.Interaction, recap_id: int):
    db = bot.db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id from recaps where id = %s and server_id = %s", (recap_id,context.guild_id))
    recap = cursor.fetchone()
    if recap is None:
        await context.response.send_message(f"There is no recap with that id!", ephemeral=True)
        return
    if recap[0] != context.user.id and not context.user.guild_permissions.manage_messages:
        await context.response.send_message(f"You do not have the permissions required to remove other people's recaps.", ephemeral=True)
        return
    try:
        cursor.execute("DELETE FROM recaps WHERE id = %s", (recap_id,))
        cursor.close()
        db.commit()
        db.close()
    except:
        await context.response.send_message(f"Something went wrong!", ephemeral=True)
        return
    await context.response.send_message(f"Successfully removed recap with id {recap_id}", ephemeral=True)

@recap_group.command(
        name="list",
        description=f"Lists recaps from given user"
        )
@app_commands.describe(
        target="Target user (self on empty)"
        )
@app_commands.guild_only()
async def recap_list(context: discord.Interaction, target: Optional[discord.Member]):
    if target is None:
        member = context.user
    else:
        member = target
    response = discord.Embed()
    response.title = "Recaps for "+member.display_name+":\n"
    recaps = await get_recap_list(member.id, context.guild_id)
    if recaps is None or len(recaps) == 0:
        response.description = "No recaps for that user!"
        await context.response.send_message(embed=response)
        return
    response.description = ""
    response.set_footer(text=("1/"+str(math.ceil(len(recaps)/5))))
    recaps_list = list()
    for recap in recaps[0:5]:
        response.description += f'id {recap["id"]} for {recap["date"]}:\n{recap["content"]}\n\n'
    for recap in recaps:
        recaps_list.append(f'id {recap["id"]} for {recap["date"]}:\n{recap["content"]}\n')
    recapview = views.ListView(response, context, recaps_list)
    await context.response.send_message(embed=response, view=recapview)

tree.add_command(recap_group)

# activity_group = GuildGroup(name='activity', description='Activity analytics commands!')

@tree.command(
        name="hi",
        description=f"Says something from {owner_name}"
        )
@app_commands.guild_only()
async def hi(context: discord.Interaction, string: Optional[str]):
    if context.user.id != owner_id:
        await context.response.send_message(f"Only {owner_name} can use this command :(", ephemeral=True)
        return
    response = discord.Embed()
    test = await context.guild.fetch_member(owner_id)
    response.set_author(name="Nomi", icon_url=test.display_avatar.url)
    if string is None:
        response.title = "Hiya!"
    else:
        response.title = string
    # response.set_thumbnail(url="https://tenor.com/view/hi-gif-3569838625539753897")
    await context.response.send_message(embed=response)

@tree.command(
        name='sync',
        description=f'{owner_name}-only, syncs the bot\'s command tree'
        )
@app_commands.guilds(715456652945653772) # just change this value or smth i dont care nearly enough to make it a variable
async def sync(context: discord.Interaction):
    if context.user.id != owner_id:
        await context.response.send_message(f"{owner_name}-only command for api stuff", ephemeral=True)
        return
    await tree.sync()
    logger.info('Command tree synced.')
    await context.response.send_message('Command tree synced.')

bot.run(os.getenv("TK"))
