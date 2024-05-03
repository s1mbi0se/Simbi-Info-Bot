from config import Config
from discord.ext import commands
from rocketry import Rocketry
from rocketry.conditions.api import every

from utils.get_time import get_time_from_api
from utils.mercado_topografico.status_verify.utils_status_mt import ping_notify, generate_message

schedule_status = Rocketry(
    config={
        "task_execution": "async",
        "timezone": Config.TIME_ZONE,
    }
)


class Status(commands.Cog):
    """
    Schedule tasks to post birthdays
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Status Verify is ready")

        @schedule_status.task(every("20m"), name="Verify status MT")
        async def verify_sheet():
            print("Iniciando verificação de status...")
            print("--------------------------")

            channel = self.bot.get_channel(Config.MT_ALERTS_CHANNEL)

            title = (
                f"** ##############    VERIFICAÇÃO DE STATUS"
                "    ############## **\n\n"
                "```   Intervalo de Verificação: "
                f"20 minutos ```"
            )

            now = get_time_from_api().strftime("%d de %B de %Y %H:%M:%S")
            format_date = f"Horário local (Brasil): {now}"

            status_apps = "```"
            status_apps += "   --------- SERVIÇOS MARKETPLACE ---------\n"
            mt_prod = ping_notify(Config.MT_URL_PROD)
            status_apps += generate_message(
                name="SISTEMA MERCADO - PROD", status=mt_prod
            )

            mt_homo = ping_notify(Config.MT_URL_HOMO)
            status_apps += generate_message(
                name="SISTEMA MERCADO - HOMO", status=mt_homo
            )

            final_message = title + status_apps + f"\n\n{format_date}```"
            last_message_id = channel.last_message_id
            last_message = await channel.fetch_message(last_message_id)
            last_message_content = last_message.content


            if "❌" in final_message or "💀" in final_message:
                cargo_ids = Config.MT_ALERTS_CARGOS

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


                await channel.send(
                    final_message + f"\n{cargo_mentions if cargo_mentions else ''}"
                                    f" Há serviços fora do ar! \n"
                )
            else:
                if (
                        title in last_message_content
                        and "❌" not in last_message_content
                        and "💀" not in last_message_content
                ):
                    await last_message.edit(content=final_message)
                else:
                    await channel.send(final_message)

        await schedule_status.serve()


async def setup(bot):
    await bot.add_cog(Status(bot))
