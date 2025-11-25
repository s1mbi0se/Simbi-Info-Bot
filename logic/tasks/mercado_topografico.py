import os

from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

from utils.logging import write_report_log_async
from utils.mercado_topografico.azure_devops.estimate import estimated_efforts
from utils.mercado_topografico.google_apis.presentation import (
    generate_presentation,
)
from utils.mercado_topografico.infra_tools.deployment import (
    deploy_production,
    deploy_stage,
    deploy_whitelabel,
)
from utils.mercado_topografico.status_verify.utils_status_mt import ping_notify

load_dotenv()


class MercadoTopografico(commands.Cog):
    """
    Tasks for the Marcado Topografico
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        allowed_channel_id = int(
            os.getenv("CHANNEL_ALLOWED_FOR_PRESENTATION", default=0)
        )
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
            elif "verify" in message.content:
                await self.process_verify_command(message)
            elif "prod" in message.content:
                await self.deploy_production_command(message)
            elif "whitelabel" in message.content:
                await self.deploy_whitelabel_command(message)
            elif "homo" in message.content:
                await self.deploy_stage_command(message)
            else:
                await self.send_invalid_command_message(message)

    @staticmethod
    async def process_presentation_command(message):
        await message.channel.send(
            "Um momento, estou preparando a apresentação..."
        )
        (
            current_sprint,
            tasks_without_estimates,
            presentation_url,
            message_tasks,
        ) = generate_presentation()

        message_to_send = message_tasks["message"]
        mt_role_name = os.getenv("MT_ROLE_NAME")
        role = get(message.guild.roles, name=mt_role_name)

        if not message_tasks["all_estimated"]:
            await message.channel.send(
                f"{message_to_send}\n" f"{role.mention}"
            )
        else:
            await message.channel.send(
                f"{message.author.mention} e {role.mention} aqui está"
                f" a apresentação da **Sprint Review {current_sprint}**:\n"
                f"{presentation_url}\n"
                f"{message_to_send}"
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
    async def process_verify_command(message):
        await message.channel.send(
            "Um momento, vou verificar as instâncias..."
        )

        instances_url = [
            "https://mercadotopografico.com.br",
            "https://prod01.mercadotopografico.com.br",
            "https://prod02.mercadotopografico.com.br",
            "https://www.mercadotopografico.com.br",
            "https://geomarkett.com",
            "https://www.geomarkett.com",
            "https://geomarkett.cl",
            "https://www.geomarkett.cl",
            "https://teste.mercadotopografico.com.br",
            "https://devtest.mercadotopografico.com.br",
            "https://app.mercadotopografico.com.br",
        ]

        response = f"\nSTATUS DAS INSTÂNCIAS:\n"
        for url in instances_url:
            status = await ping_notify(url)
            response += f"{status}\n"

        await message.channel.send(f"{message.author.mention} {response}")

    @staticmethod
    async def deploy_production_command(message):
        await message.channel.send(
            "Um momento, vou iniciar o deploy para produção..."
        )

        deploy_message = deploy_production()
        await message.channel.send(
            f"{message.author.mention} {deploy_message}"
        )

    @staticmethod
    async def deploy_whitelabel_command(message):
        await message.channel.send(
            "Um momento, vou iniciar o deploy para whitelabel..."
        )

        deploy_message = deploy_whitelabel()
        await message.channel.send(
            f"{message.author.mention} {deploy_message}"
        )

    @staticmethod
    async def deploy_stage_command(message):
        await message.channel.send(
            "Um momento, vou iniciar o deploy para homologação..."
        )

        deploy_message = deploy_stage()
        await message.channel.send(
            f"{message.author.mention} {deploy_message}"
        )

    @staticmethod
    async def send_invalid_command_message(message):
        await message.channel.send(
            "### Comando inválido\n"
            "Use um dos comandos abaixo:\n"
            "**!mt-presentation** para gerar a apresentação da sprint review\n"
            "**!mt-estimate** para obter as estimativas da sprint atual\n"
            "**!mt-verify** para obter o status das instâncias do Mercado Topografico\n"
            "**!mt-prod** para deploy em produção\n"
            "**!mt-whitelabel** para deploy em whitelabel\n"
            "**!mt-homo** para deploy em homologação\n"
        )

    @commands.Cog.listener()
    async def on_ready(self):
        await write_report_log_async(
            sender="MT-PRESENTATION", msg="STATUS - OK"
        )
        print("Presentation is ready")


async def setup(bot):
    await bot.add_cog(MercadoTopografico(bot))
