import os
import asyncio
import io
from datetime import datetime

from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
from discord import File

from utils.logging import write_report_log_async
from utils.mercado_topografico.azure_devops.estimate import estimated_efforts
from utils.mercado_topografico.azure_devops.report import (
    generate_period_report,
)
from utils.mercado_topografico.github_report import get_github_report, GitHubReportError
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
        if message.author == self.bot.user:
            return

        content = message.content or ""

        # Se não for comando !mt ou !mt-gh-report, ignora
        if "!mt" not in content and "!mt-gh-report" not in content:
            return

        allowed_channel_id = int(
            os.getenv("CHANNEL_ALLOWED_FOR_PRESENTATION", default=0)
        )
        gh_report_channel_id = int(
            os.getenv("GH_REPORT_CHANNEL_ID", default=0)
        )

        # Comandos gerais do MT (presentation, estimate, verify, report Azure)
        if "!mt" in content and "gh-report" not in content:
            if message.channel.id != allowed_channel_id:
                return

            if "presentation" in content:
                await self.process_presentation_command(message)
            elif "estimate" in content:
                await self.process_estimate_command(message)
            elif "verify" in content:
                await self.process_verify_command(message)
            elif "report" in content:
                await self.process_report_command(message)
            elif "prod" in content:
                await self.deploy_production_command(message)
            elif "whitelabel" in content:
                await self.deploy_whitelabel_command(message)
            elif "homo" in content:
                await self.deploy_stage_command(message)
            else:
                await self.send_invalid_command_message(message)

        # Comando específico de GitHub report pode rodar em outro canal
        elif "!mt-gh-report" in content:
            if gh_report_channel_id and message.channel.id != gh_report_channel_id:
                return
            await self.process_github_report_command(message)

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
            "https://mtteste.com.br",
            "https://www.mtteste.com.br",
            "https://devtest.mtteste.com.br",
            "https://app.mtteste.com.br",
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

        loop = asyncio.get_event_loop()
        deploy_message = await loop.run_in_executor(None, deploy_production)

        if len(deploy_message) > 2000:
            file = File(
                io.BytesIO(deploy_message.encode()),
                filename="deploy_log.txt",
            )

            await message.channel.send(
                f"{message.author.mention} O deploy foi concluído, porem o log é muito grande. Enviando em anexo...",
                file=file
            )

        else:
            await message.channel.send(
                f"{message.author.mention} {deploy_message}"
            )

    @staticmethod
    async def deploy_whitelabel_command(message):
        await message.channel.send(
            "Um momento, vou iniciar o deploy para whitelabel..."
        )
        loop = asyncio.get_event_loop()
        deploy_message = await loop.run_in_executor(None, deploy_whitelabel)

        if len(deploy_message) > 2000:
            file = File(
                io.BytesIO(deploy_message.encode()),
                filename="deploy_log.txt",
            )

            await message.channel.send(
                f"{message.author.mention} O deploy foi concluído, porem o log é muito grande. Enviando em anexo...",
                file=file
            )

        else:
            await message.channel.send(
                f"{message.author.mention} {deploy_message}"
            )

    @staticmethod
    async def deploy_stage_command(message):
        await message.channel.send(
            "Um momento, vou iniciar o deploy para homologação..."
        )

        loop = asyncio.get_event_loop()
        deploy_message = await loop.run_in_executor(None, deploy_stage)

        if len(deploy_message) > 2000:
            file = File(
                io.BytesIO(deploy_message.encode()),
                filename="deploy_log.txt",
            )

            await message.channel.send(
                f"{message.author.mention} O deploy foi concluído, porem o log é muito grande. Enviando em anexo...",
                file=file
            )

        else:
            await message.channel.send(
                f"{message.author.mention} {deploy_message}"
            )

    @staticmethod
    async def process_report_command(message):
        content = message.content.strip()
        parts = content.split()

        if len(parts) != 3:
            await message.channel.send(
                "Uso incorreto. Use: **!mt-report dd-mm-aaaa dd-mm-aaaa**"
            )
            return

        try:
            start_date = datetime.strptime(parts[1], "%d-%m-%Y").date()
            end_date = datetime.strptime(parts[2], "%d-%m-%Y").date()
        except ValueError:
            await message.channel.send(
                "Datas inválidas. Use o formato **dd-mm-aaaa**, por exemplo: "
                "`!mt-report 01-01-2025 16-12-2025`"
            )
            return

        if start_date > end_date:
            await message.channel.send(
                "A data inicial não pode ser maior que a data final."
            )
            return

        await message.channel.send(
            "Um momento, estou gerando o relatório do período..."
        )

        try:
            report_message = generate_period_report(start_date, end_date)
        except Exception:
            await message.channel.send(
                "Não foi possível gerar o relatório agora. Tente novamente mais tarde."
            )
            return

        await message.channel.send(f"{message.author.mention} {report_message}")

    @staticmethod
    async def process_github_report_command(message):
        content = message.content.strip()
        parts = content.split()

        # Expected: !mt-gh-report dd-mm-aaaa dd-mm-aaaa <repo1> <repo2> ...
        if len(parts) < 4:
            await message.channel.send(
                "Uso incorreto. Use: **!mt-gh-report dd-mm-aaaa dd-mm-aaaa repo_url1 repo_url2 ...**"
            )
            return

        try:
            start_date = datetime.strptime(parts[1], "%d-%m-%Y").date()
            end_date = datetime.strptime(parts[2], "%d-%m-%Y").date()
        except ValueError:
            await message.channel.send(
                "Datas inválidas. Use o formato **dd-mm-aaaa**, por exemplo: "
                "`!mt-gh-report 01-01-2025 16-12-2025 https://github.com/org/repo`"
            )
            return

        if start_date > end_date:
            await message.channel.send(
                "A data inicial não pode ser maior que a data final."
            )
            return

        repo_urls = parts[3:]

        await message.channel.send(
            "Um momento, estou gerando o relatório do GitHub para os repositórios informados..."
        )

        try:
            report_message = await get_github_report(repo_urls, start_date, end_date)
        except GitHubReportError as e:
            await message.channel.send(str(e))
            return
        except Exception:
            await message.channel.send(
                "Não foi possível gerar o relatório do GitHub agora. Tente novamente mais tarde."
            )
            return

        await message.channel.send(f"{message.author.mention} {report_message}")

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
