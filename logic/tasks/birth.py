import asyncio
from io import BytesIO

import discord
import httpx
from config import Config
from discord import File
from discord.ext import commands
from discord.ui import View, Button
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


class ConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label="Sim", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Confirmado! Enviando mensagem...", ephemeral=True)
        self.value = True
        self.stop()

    @discord.ui.button(label="Não", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Cancelado.", ephemeral=True)
        self.value = False
        self.stop()


class Birth(commands.Cog):
    """
    Schedule tasks to post birthdays
    """

    def __init__(self, bot):
        self.bot = bot

    async def verify_birthdays(self, manual=False, dm_channel=None):
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
                if manual and dm_channel:
                    await dm_channel.send("Erro: Canal de aniversário não encontrado.")
                return

            print(f"GET MEMBERS LIST: {now.date()} - {now.time()}")
            LIST_OF_MEMBERS = get_birthdays(today=now.date())

            await write_report_log_async(
                sender="BIRTH",
                msg=f"{len(LIST_OF_MEMBERS) if LIST_OF_MEMBERS else 0} aniversariantes encontrados",
                now=now,
            )

            if not LIST_OF_MEMBERS:
                await write_report_log_async(
                    sender="BIRTH",
                    msg="Nenhum aniversariante encontrado hoje",
                    now=now,
                )
                if manual and dm_channel:
                    await dm_channel.send("Nenhum aniversariante encontrado hoje.")
                return

            image_data_list = []
            names = ""
            pix = ""

            for pos, member in enumerate(LIST_OF_MEMBERS):
                names += f"{' e ' if pos > 0 else ''}**{member['Membro']}**"
                pix += (
                    f"Chave PIX para quem quiser/puder"
                    f" enviar um presentinho para"
                    f" {member['Membro'].split(' ')[0]}: {member['PIX']} \n"
                    if member.get("PIX")
                    else ""
                )

            # Download images with timeout and continue on failure (with retries)
            timeout = httpx.Timeout(connect=5.0, read=15.0, write=15.0, pool=15.0)
            async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
                for member in LIST_OF_MEMBERS:
                    url = member.get("Foto")
                    if not url:
                        continue
                    for attempt in range(2):
                        try:
                            resp = await client.get(url)
                            resp.raise_for_status()
                            image_data_list.append({
                                "bytes": resp.content,
                                "filename": f"{member.get('Membro')}.png",
                            })
                            break
                        except (httpx.TimeoutException, httpx.RequestError) as err:
                            if attempt == 0:
                                await asyncio.sleep(1)
                                continue
                            await write_error_log_async(
                                sender="BIRTH",
                                msg=f"Falha ao baixar foto de {member.get('Membro')}: {str(err)}",
                                now=now,
                            )
                            break

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

            message_content = (
                f"{cargo_mentions if cargo_mentions else ''}"
                f"**HOJE É DIA DE  COMEMORAR!**\n\n"
                f"Hoje comemoramos a vida de {names} 🎉 🎉\n"
                f"Parabéns! Muitas felicidades,"
                f" que este novo ciclo que se inicia "
                f"seja repleto de realizações e conquistas! \n\n"
                f"{pix}"
            )

            if manual and dm_channel:
                total_photos = len(image_data_list)
                preview_message = (
                    f"**PREVIEW DA MENSAGEM:**\n\n"
                    f"Aniversariante(s): {names}\n"
                    f"Total de fotos: {total_photos}\n"
                )
                # Cap preview to 10 files per Discord DM message
                preview_files = []
                for idx, img_data in enumerate(image_data_list):
                    if idx >= 10:
                        break
                    preview_files.append(
                        File(BytesIO(img_data["bytes"]), filename=img_data["filename"])
                    )
                if total_photos > 10:
                    preview_message += f"(Mostrando 10 de {total_photos} fotos no preview)\n\n"
                preview_message += "Deseja enviar esta mensagem ao canal?"

                view = ConfirmView()
                await dm_channel.send(preview_message, files=preview_files, view=view)
                await view.wait()

                if view.value is None:
                    await dm_channel.send("Tempo esgotado. Postagem cancelada.")
                    return
                if not view.value:
                    await write_report_log_async(
                        sender="BIRTH",
                        msg="Usuário cancelou envio manual",
                        now=now,
                    )
                    await dm_channel.send("Postagem cancelada.")
                    return
                await write_report_log_async(
                    sender="BIRTH",
                    msg="Usuário confirmou envio manual",
                    now=now,
                )
                await dm_channel.send("Enviando mensagem ao canal...")

            # Build final files from bytes (send in chunks of up to 10 files)
            def _chunk(lst, size):
                for i in range(0, len(lst), size):
                    yield lst[i:i + size]

            all_files = [
                File(BytesIO(img_data["bytes"]), filename=img_data["filename"])
                for img_data in image_data_list
            ]

            await write_report_log_async(
                sender="BIRTH",
                msg="Enviando mensagem ao canal",
                now=now,
            )

            # First message with the text and up to 10 files
            first_batch = list(_chunk(all_files, 10))
            if first_batch:
                await channel.send(message_content, files=first_batch[0])
                # Additional images, if any
                for extra_batch in first_batch[1:]:
                    await channel.send(files=extra_batch)
            else:
                # No images available, just send the text
                await channel.send(message_content)

            await write_report_log_async(
                sender="BIRTH",
                msg="Mensagem enviada com sucesso",
                now=now,
            )

            if manual and dm_channel:
                await dm_channel.send("Mensagem enviada com sucesso! ✅")

        except Exception as e:
            await write_error_log_async(
                sender="BIRTH", msg=f"Erro na execução: {str(e)}", now=now
            )
            if manual and dm_channel:
                await dm_channel.send(f"Erro ao processar: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if not isinstance(message.channel, discord.DMChannel):
            return

        if message.author.id not in Config.BIRTHDAY_AUTHORIZED_USERS:
            return

        if message.content.startswith("!birth"):
            await message.channel.send("Verificando aniversários...")
            await self.verify_birthdays(manual=True, dm_channel=message.channel)
            await message.channel.send("Processo concluído!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Birth is ready")
        await write_report_log_async(sender="BIRTH", msg="STATUS - OK")

        @schedule.task(daily.at("11:11"), name="Verify birthdays")
        async def verify_sheet():
            await self.verify_birthdays()

        await schedule.serve()


async def setup(bot):
    await bot.add_cog(Birth(bot))
