from rocketry import Rocketry
from rocketry.conditions.api import daily

from config import Config
from discord.ext import commands


MESSAGE_WITH_LINK = "Olá! Abaixo você encontrará o link para gerenciar os " \
                    "lembretes relacionados ao usuário **{{USER}}**:\n" \
                    "- {{URL}}"
schedule = Rocketry(
    config={
        "task_execution": "async",
        "timezone": Config.TIME_ZONE,
    }
)


class SchedulerTasks(commands.Cog):
    """
    Schedule tasks to post daily tasks links
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("SchedulerTasks is ready")

        @schedule.task(daily.at("08:00"), name="Generate tasks link")
        async def send_tasks_link():
            try:
                for guild in self.bot.guilds:
                    for member in guild.members:
                        message = MESSAGE_WITH_LINK.replace("{{URL}}", Config.FRONT_BASE_URL + str(member.id)) \
                            .replace("{{USER}}", member.global_name)
                        await member.send(message)
            except Exception as e:
                print(e)
        await schedule.serve()


async def setup(bot):
    await bot.add_cog(SchedulerTasks(bot))