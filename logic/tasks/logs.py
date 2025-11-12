import os

import discord
from config import Config
from discord.ext import commands

from utils.logging import write_report_log_async


class Logs(commands.Cog):
    """
    Schedule tasks to post birthdays
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if not isinstance(message.channel, discord.DMChannel):
            return

        if message.content.startswith("!hi"):
            await message.channel.send("Hello!")

        elif message.content.startswith("!logs"):
            log_files = ["error.log", "report.log"]

            for log_file in log_files:
                if not os.path.exists(log_file):
                    with open(log_file, "w") as file:
                        file.write("\n")

                with open(log_file, "r") as file:
                    lines = file.readlines()
                    last_lines = lines[-10:]
                    await message.channel.send(
                        f"```markdown\n"
                        f"# {log_file}\n\n"
                        f"{''.join(last_lines)}```"
                    )
        elif message.content.startswith("!birth"):
            pass
        else:
            help_message = (
                "```markdown\n"
                "# Aqui estão meus comandos: \n\n"
                "## !hi\n"
                "> Com este comando, "
                "eu apenas retornarei Hello para você.\n"
                "## !logs\n"
                "> Com este comando, eu retornarei "
                "os arquivos `error.log` e `report.log`."
            )

            if message.author.id in Config.BIRTHDAY_AUTHORIZED_USERS:
                help_message += (
                    "\n## !birth\n"
                    "> Com este comando, eu verificarei "
                    "os aniversariantes do dia e farei a postagem."
                )

            help_message += "```"
            await message.channel.send(help_message)

    @commands.Cog.listener()
    async def on_ready(self):
        await write_report_log_async(sender="LOGS", msg="STATUS - OK")


async def setup(bot):
    await bot.add_cog(Logs(bot))
