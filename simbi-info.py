from asyncio import run

import discord
from config import Config
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

run(client.load_extension("logic.tasks.birth"))
run(client.load_extension("logic.tasks.logs"))
run(client.load_extension("logic.tasks.presentation"))

if __name__ == "__main__":
    client.run(Config.TOKEN)
