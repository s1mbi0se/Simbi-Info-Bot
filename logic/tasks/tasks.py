from discord import DMChannel
from discord.ext import commands

from config import Config
from utils.supabase.SupabaseClient import SupabaseClient

COMMAND_REPORT_ALIAS = ['lembrete', 'LEMBRETE']
MESSAGE_WITH_LINK = "Olá! Abaixo você encontrará o link para gerenciar os " \
                    "lembretes relacionados ao usuário **{{USER}}**:\n" \
                    "- {{URL}}"


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=COMMAND_REPORT_ALIAS)
    async def on_message(self, ctx, *, arg):
        # Check if the message was sent privately
        is_private_message = isinstance(ctx.channel, DMChannel)
        commands = arg.split(' ')
        if is_private_message:
            if len(commands) == 1 and "mostrar" == commands[0]:
                message = MESSAGE_WITH_LINK.replace("{{URL}}", Config.FRONT_TASK_PERSONAL_URL + str(ctx.author.id))\
                    .replace("{{USER}}", ctx.author.global_name)
                await ctx.channel.send(message)
                return
            SupabaseClient.create_task(task=arg, created_by_id=ctx.author.id, created_by_name=ctx.author.global_name,
                                       created_to_id=ctx.author.id, created_to_name=ctx.author.global_name)
            await ctx.channel.send("Lembrete criado com sucesso!")
        else:
            mentions = ctx.message.mentions if ctx.message.mentions else []
            if len(commands) == 2 and "mostrar" in commands[0]:
                message = MESSAGE_WITH_LINK.replace("{{URL}}", Config.FRONT_TASK_OTHER_URL + str(mentions[0].id))\
                    .replace("{{USER}}", mentions[0].global_name)
                await ctx.channel.send(message)
                return
            SupabaseClient.create_task(task=" ".join(commands[len(mentions):]),
                                       created_by_id=ctx.author.id, created_by_name=ctx.author.global_name,
                                       created_to_id=mentions[0].id, created_to_name=mentions[0].global_name)
            await ctx.channel.send("Lembrete criado com sucesso!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Tasks listener is ready!")


async def setup(bot):
    await bot.add_cog(Tasks(bot))
