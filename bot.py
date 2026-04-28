import logging
import os
from typing import Optional
# import mysql.connector
import datetime

import discord
from discord.flags import Intents
from discord import app_commands


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
    def __init__(self, *, intents: Intents) -> None:
        super().__init__(intents=intents)
        # self.db = mysql.connector.connect(
        #         host = os.getenv("DB_HOST"),
        #         user = os.getenv("DB_USER"),
        #         password = os.getenv("DB_PASSWORD"),
        #         database = os.getenv("DB_DATABASE"),
        #     )
    async def on_ready(self):
        # await tree.sync()
        logger.info(f'Logged on as {self.user}!')

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


bot = Bot(intents=intents)
tree = discord.app_commands.CommandTree(bot)
owner_id = int(os.getenv("OWNER_ID"))
owner_name = os.getenv("OWNER_NAME")
if owner_name is None:
    logger.error("Owner name needs to be set")
    exit()

@tree.command(
        name="hi",
        description=f"Says hi from {owner_name}"
        )
async def hi(context: discord.Interaction, member: Optional[discord.Member]):
    if context.user.id != owner_id:
        await context.response.send_message(f"Only {owner_name} can use this command :(", ephemeral=True)
        return
    if not isinstance(context.user, discord.Member) or context.guild == None:
        await context.response.send_message(content="Available only on servers!", ephemeral=True)
        return
    response = discord.Embed()
    test = await context.guild.fetch_member(owner_id)
    response.set_author(name="Nomi", icon_url=test.display_avatar.url)
    if member is None:
        response.title = "Hiya!"
    else:
        response.title = "Hiya "+member.mention+"!"
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
