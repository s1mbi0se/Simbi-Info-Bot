import os

from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

from utils.mercado_topografico.azure_devops.estimate import estimated_efforts
from utils.mercado_topografico.google_apis.presentation import (
    generate_presentation
)

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

        if "!mt" in message.content:
            if "presentation" in message.content:
                await self.process_presentation_command(message)
            elif "estimate" in message.content:
                await self.process_estimate_command(message)
            else:
                await self.send_invalid_command_message(message)

    @staticmethod
    async def process_presentation_command(message):
        await message.channel.send(
            "Um momento, estou preparando a apresentação..."
        )
        current_sprint, presentation_url = generate_presentation()
        # mt_role_name = os.getenv("MT_ROLE_NAME")
        mt_role_name = "squad 1"
        role = get(message.guild.roles, name=mt_role_name)
        await message.channel.send(
            f"{message.author.mention} e {role.mention} aqui está"
            f" a apresentação da **Sprint Review {current_sprint}**: "
            f"{presentation_url}"
        )

    @staticmethod
    async def process_estimate_command(message):
        await message.channel.send(
            "Um momento, estou pegando as estimativas..."
        )
        estimate_message = estimated_efforts()
        await message.channel.send(
            f"{message.author.mention} {estimate_message}"
        )

    @staticmethod
    async def send_invalid_command_message(message):
        await message.channel.send(
            f"### Comando inválido\n"
            f"Use um dos comandos abaixo:\n"
            f"**!mt-presentation** para gerar a apresentação da sprint review\n"
            f"**!mt-estimate** para obter as estimativas da sprint atual"
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print("Presentation is ready")


async def setup(bot):
    await bot.add_cog(MercadoTopografico(bot))
