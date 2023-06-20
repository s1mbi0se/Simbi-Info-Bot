import datetime

from config import Config
from discord.ext import commands, tasks

from utils.get_time import get_time_from_api
from utils.spread import get_next_revaluation

EVERY_DAY = datetime.time(
    hour=Config.HOUR, minute=Config.MINUTE, tzinfo=Config.TIME_ZONE
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
        now = get_time_from_api()
        current_time = now.time()

        if (
            current_time.hour != EVERY_DAY.hour
            or current_time.minute != EVERY_DAY.minute
        ):
            return

        with open("revaluation_report.log", "a") as f:
            f.write(f'{now}: "Starting daily revaluation check"\n')

        try:
            channel = self.bot.get_channel(Config.INFO_CHANNEL)

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

                await channel.send(
                    f"{cargo_mentions if cargo_mentions else ''}"
                    f"**REAVALIAÇÃO À VISTA!**\n\n"
                    f"{response}"
                )
            else:
                return
        except Exception as e:
            now = get_time_from_api()
            with open("error.log", "a") as f:
                f.write(f"{now}: REVALUATION ERROR: {str(e)}\n")


async def setup(bot):
    await bot.add_cog(Revaluation(bot))
