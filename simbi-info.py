from asyncio import run

import discord
from config import Config
from discord.ext import commands


intents = discord.Intents.all()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents)

run(client.load_extension("logic.tasks.tasks"))
run(client.load_extension("logic.scheduler.tasks"))

if __name__ == "__main__":
    client.run(Config.TOKEN)
