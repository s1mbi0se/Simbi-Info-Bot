from io import BytesIO

import httpx
from config import Config
from discord import File
from discord.ext import commands
from rocketry import Rocketry
from rocketry.conditions.api import daily

from utils.birthday import get_birthdays
from utils.get_time import get_time_from_api
from utils.logging import write_error_log_async, write_report_log_async

schedule = Rocketry(
    config={
        "task_execution": "async",
        "timezone": Config.TIME_ZONE,
    }
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

        @schedule.task(daily.at("08:00"), name="Verify birthdays")
        async def verify_sheet():
            await write_report_log_async(
                sender="BIRTH", msg="Iniciando verificação de aniversários"
            )

            now = get_time_from_api()

            try:
                channel = self.bot.get_channel(Config.BIRTHDAY_CHANNEL)
                if not channel:
                    await write_error_log_async(
                        sender="BIRTH",
                        msg="Canal de aniversário não encontrado",
                        now=now,
                    )
                    return
                print(f"GET MEMBERS LIST: {now.date()} - {now.time()}")
                LIST_OF_MEMBERS = get_birthdays(today=now.date())

                await write_report_log_async(
                    sender="BIRTH",
                    msg=f"{len(LIST_OF_MEMBERS) if LIST_OF_MEMBERS else 0} aniversariantes encontrados",
                    now=now,
                )

                if LIST_OF_MEMBERS:
                    discord_files = []
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

                        await write_report_log_async(
                            sender="BIRTH",
                            msg=f"Processando membro: {member['Membro']}",
                            now=now,
                        )

                        image_request = httpx.get(
                            member.get("Foto"), follow_redirects=True
                        )

                        if image_request.status_code != 200:
                            await write_error_log_async(
                                sender="BIRTH",
                                msg=f"Falha ao baixar foto de {member['Membro']}: Status {image_request.status_code}",
                                now=now,
                            )
                            continue

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
                            " ".join(
                                [cargo.mention for cargo in cargos if cargos]
                            )
                            + "\n"
                        )
                        if cargos
                        else None
                    )

                    await write_report_log_async(
                        sender="BIRTH",
                        msg="Enviando mensagem ao canal",
                        now=now,
                    )
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
                    await write_report_log_async(
                        sender="BIRTH",
                        msg="Mensagem enviada com sucesso",
                        now=now,
                    )
                else:
                    await write_report_log_async(
                        sender="BIRTH",
                        msg="Nenhum aniversariante encontrado hoje",
                        now=now,
                    )
            except Exception as e:
                await write_error_log_async(
                    sender="BIRTH", msg=f"Erro na execução: {str(e)}", now=now
                )

        await schedule.serve()


async def setup(bot):
    await bot.add_cog(Birth(bot))
