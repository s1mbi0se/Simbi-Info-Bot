import os
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
from utils import generate_presentation
load_dotenv()


class Presentation(commands.Cog):
    """
    Presentation for the Marcado Topografico
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        allowed_channel_id = os.getenv("CHANNEL_ALLOWED_FOR_PRESENTATION")
        if message.author == self.bot.user or message.channel.id != allowed_channel_id:
            return

        if message.content.startswith("!mt-presentation"):
            await message.channel.send("Um momento, estou preparando a apresentação...")
            current_sprint, presentation_url = generate_presentation.main()
            mt_role_name = os.getenv("MT_ROLE_NAME")
            role = get(message.guild.roles, name=mt_role_name)
            await message.channel.send(
                f"{message.author.mention} e {role.mention } aqui está a apresentação da **Sprint Review {current_sprint}**: "
                f"{presentation_url}")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Presentation is ready")


async def setup(bot):
    await bot.add_cog(Presentation(bot))
