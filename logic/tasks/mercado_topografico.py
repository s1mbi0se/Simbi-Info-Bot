from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

from utils.mercado_topografico.azure_devops.estimate import estimated_efforts
from utils.mercado_topografico.google_apis.presentation import generate_presentation

load_dotenv()


class MercadoTopografico(commands.Cog):
    """
    Tasks for the Marcado Topografico
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        allowed_channel_id = 1214922291859947521
        # allowed_channel_id = int(
        #     os.getenv("CHANNEL_ALLOWED_FOR_PRESENTATION", default=0)
        # )
        if (
            message.author == self.bot.user
            or message.channel.id != allowed_channel_id
        ):
            return

        if message.content.startswith("!mt-presentation"):
            await message.channel.send(
                "Um momento, estou preparando a apresentação..."
            )
            current_sprint, presentation_url = generate_presentation()
            mt_role_name = "squad 1"
            # mt_role_name = os.getenv("MT_ROLE_NAME")
            role = get(message.guild.roles, name=mt_role_name)
            await message.channel.send(
                f"{message.author.mention} e {role.mention } aqui está"
                f" a apresentação da **Sprint Review {current_sprint}**: "
                f"{presentation_url}"
            )

        if message.content.startswith("!mt-estimate"):
            await message.channel.send(
                "Um momento, estou pegando as estimativas..."
            )

            estimate_message = estimated_efforts()

            await message.channel.send(
                f"{message.author.mention} {estimate_message}"
            )

    @commands.Cog.listener()
    async def on_ready(self):
        print("Presentation is ready")


async def setup(bot):
    await bot.add_cog(MercadoTopografico(bot))
