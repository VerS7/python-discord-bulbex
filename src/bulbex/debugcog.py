"""
Discord cog для дебага
"""
from typing import List

import discord
from discord.ext import commands

from loguru import logger

from .config import GUILD_ID, TRUSTED_IDS

GUILD_IDS = []
if GUILD_ID:
    GUILD_IDS.append(GUILD_ID)


def trusted_only(ctx: commands.Context):
    """Callback-проверка ID пользователя на наличие в списке доверенных"""
    return ctx.author.id in TRUSTED_IDS


class LinkedGuildsEmbed(discord.Embed):
    """Embed гильдий с ботом"""
    def __init__(self, guilds: List[discord.Guild], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = f"Подключенные гильдии"
        self.color = discord.Color.dark_red()

        for i, guild in enumerate(guilds):
            self.add_field(name=f"`#{i + 1} {guild.name}`", value=f"`{guild.id}`")


class DebugCog(commands.Cog):
    """Cog с дебаг-командами"""

    def __init__(self, bot_: discord.Bot):
        self._bot = bot_

    @commands.slash_command(name="debug_resync",
                            description="Ручная сихронизация слэш-комманд с гильдиями",
                            guild_ids=GUILD_IDS)
    @commands.check(trusted_only)
    async def sync(self, ctx: discord.ApplicationContext):
        """Повторная синхронизация гильдий. Занимает некоторое время"""
        logger.info(f"{ctx.guild.name} | Вызов /debug_resync от {ctx.author.name} в чате {ctx.channel.name}.")

        await ctx.respond("**Запущена повторная синхронизация...**")
        await self._bot.sync_commands(guild_ids=[guild.id for guild in self._bot.guilds])
        await ctx.send_followup("**Синхронизация завершена.**")

    @commands.slash_command(name="debug_guilds",
                            description="Подключенные к боту гильдии",
                            guild_ids=GUILD_IDS)
    @commands.check(trusted_only)
    async def guilds(self, ctx: discord.ApplicationContext):
        """Все гильдии, в которых числится бот"""
        logger.info(f"{ctx.guild.name} | Вызов /debug_guilds от {ctx.author.name} в чате {ctx.channel.name}.")

        await ctx.respond(embed=LinkedGuildsEmbed(self._bot.guilds))
