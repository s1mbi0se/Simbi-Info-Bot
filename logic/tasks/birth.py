import datetime
from io import BytesIO

import httpx
from config import Config
from discord import File
from discord.ext import commands, tasks

from utils.birthday import get_birthdays
from utils.get_time import get_time_from_api
from utils.logging import write_error_log, write_report_log

EVERY_DAY = datetime.time(
    hour=Config.BIRTH_HOUR, minute=Config.BIRTH_MINUTE, tzinfo=Config.TIME_ZONE
)


class Birth(commands.Cog):
    """
    Schedule tasks to post birthdays
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Birth is ready")
        self.verify_sheet.start()

    @tasks.loop(seconds=60)
    async def verify_sheet(self):
        now = get_time_from_api()
        current_time = now.time()

        # if (
        #     current_time.hour != EVERY_DAY.hour
        #     or current_time.minute != EVERY_DAY.minute
        # ):
        #     return

        write_report_log(sender="BIRTH", msg="Starting daily birth check")

        try:
            channel = self.bot.get_channel(Config.BIRTHDAY_CHANNEL)

            LIST_OF_MEMBERS = get_birthdays()

            discord_files = []
            if LIST_OF_MEMBERS:
                names = ""
                pix = ""

                for pos, member in enumerate(LIST_OF_MEMBERS):
                    names += f"{' e ' if pos > 0 else ''}**{member['Membro']}**"  # noqa
                    pix += (
                        f"Chave PIX para quem quiser/puder"
                        f" enviar um presentinho para"
                        f" {member['Membro'].split(' ')[0]}: {member['PIX']} \n"  # noqa
                        if member["PIX"]
                        else ""
                    )

                    image_request = httpx.get(
                        member.get("Foto"), follow_redirects=True
                    )
                    image_bytes = BytesIO(image_request.content)

                    discord_file = File(
                        image_bytes, filename=f"{member.get('Membro')}.png"
                    )
                    discord_files.append(discord_file)

                cargo_ids = Config.BIRTHDAY_CARGOS

                cargos = (
                    [
                        channel.guild.get_role(int(cargo_id))
                        for cargo_id in cargo_ids
                    ]
                    if cargo_ids
                    else None
                )

                cargo_mentions = (
                    (
                        " ".join([cargo.mention for cargo in cargos if cargos])
                        + "\n"
                    )
                    if cargos
                    else None
                )

                # await channel.send(
                #     f"{cargo_mentions if cargo_mentions else ''}"
                #     f"**MINHAS SINCERAS E ELETRÔNICAS DESCULPAS...**\n\n"
                #     f"Nesse mês tivemos o aniversário de {names}, mas eu estava fora do ar 💥💥\n"  # NOQA
                #     f"De qualquer forma, vamos comemorar a vida de {names} 🎉 🎉\n"  # NOQA
                #     f"Parabéns! Muitas felicidades,"
                #     f" que este novo ciclo que se inicia "
                #     f"seja repleto de realizações e conquistas! \n\n"
                #     f"{pix}",
                #     files=discord_files,
                # )

                await channel.send(
                    f"{cargo_mentions if cargo_mentions else ''}"
                    f"**HOJE É DIA DE  COMEMORAR!**\n\n"
                    f"Hoje comemoramos a vida de {names} 🎉 🎉\n"
                    f"Parabéns! Muitas felicidades,"
                    f" que este novo ciclo que se inicia "
                    f"seja repleto de realizações e conquistas! \n\n"
                    f"{pix}",
                    files=discord_files,
                )
            else:
                return
        except Exception as e:
            write_error_log(sender="BIRTH", msg=str(e))


async def setup(bot):
    await bot.add_cog(Birth(bot))
