import datetime

import pytz
from config import Config
from discord.ext import commands, tasks

from utils.spread import get_next_revaluation

time_zone = pytz.timezone("America/Sao_Paulo")
EVERY_DAY = datetime.time(
    hour=Config.HOUR, minute=Config.MINUTE, tzinfo=time_zone
)


class Revaluation(commands.Cog):
    """
    Schedule tasks to post infos
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Revaluation is ready")
        self.verify_sheet.start()

    @tasks.loop(seconds=60)
    async def verify_sheet(self):
        now = datetime.datetime.now(time_zone)
        current_time = now.time()

        if (
            current_time.hour != EVERY_DAY.hour
            or current_time.minute != EVERY_DAY.minute
        ):
            return

        channel = self.bot.get_channel(int(Config.INFO_CHANNEL))

        LIST_OF_MEMBERS = get_next_revaluation()

        if LIST_OF_MEMBERS:
            response = ""
            for member in LIST_OF_MEMBERS:
                response += (
                    f'A Reavaliação de **{member.get("Membro")}**'
                    f" está próxima! Deverá ocorrer no dia "
                    f'**{member.get("Próxima reavaliação").strftime("%d/%m/%Y")}**! \n'  # noqa
                )

            cargo_ids = Config.CARGOS
            cargos = [
                channel.guild.get_role(int(cargo_id)) for cargo_id in cargo_ids
            ]
            cargo_mentions = (
                " ".join([cargo.mention for cargo in cargos]) + "\n"
            )

            await channel.send(
                f"{cargo_mentions}"
                f"**REAVALIAÇÃO À VISTA!**\n\n"
                f"{response}"
            )
        else:
            return


async def setup(bot):
    await bot.add_cog(Revaluation(bot))
