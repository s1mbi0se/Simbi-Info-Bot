import os

import discord
from discord import DMChannel
from discord.ext import commands

from utils.supabase.SupabaseClient import SupabaseClient

COMMAND_REPORT_ALIAS = ['lembrete', 'LEMBRETE']


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=COMMAND_REPORT_ALIAS)
    async def on_message(self, ctx, *, arg):
        # Check if the message was sent privately
        is_private_message = isinstance(ctx.channel, DMChannel)
        commands = arg.split(' ')
        if is_private_message:
            if len(commands) == 1 and "mostrar" in commands:
                print("Lógica para envio de URL")
                return
            SupabaseClient.create_task(task=arg, created_by_id=ctx.author.id, created_by_name=ctx.author.global_name,
                                       created_to_id=ctx.author.id, created_to_name=ctx.author.global_name)
        else:
            if len(commands) == 2 and "mostrar" in commands[0]:
                user_id = commands[0]
                print("Lógica para envio de URL")
                return
            mentions = ctx.message.mentions if ctx.message.mentions else []
            SupabaseClient.create_task(task=" ".join(commands[len(mentions):]),
                                       created_by_id=ctx.author.id, created_by_name=ctx.author.global_name,
                                       created_to_id=mentions[0].id, created_to_name=mentions[0].global_name)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Tasks listener is ready!")


async def setup(bot):
    await bot.add_cog(Tasks(bot))
