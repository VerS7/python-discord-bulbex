"""
Discord cog с основным функционалом
"""
from typing import List, Callable

import discord
from discord import Option
from discord.ext import commands

from loguru import logger

from .vkmusic import VKMusicSearch, KateMobile, AccessCredentials, Song
from .config import GUILD_ID, FFMPEG, BITRATE

GUILD_IDS = []
if GUILD_ID:
    GUILD_IDS.append(GUILD_ID)


def seconds_to_time(seconds: int) -> str:
    """Превращает секунды в строку"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"


class StartingToPlayEmbed(discord.Embed):
    """Embed запуска проигрывателя"""
    def __init__(self, ctx: discord.ApplicationContext, song: Song, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title = "ВКонтакте | Запуск"
        self.color = discord.Color.dark_red()

        self.add_field(name="Трэк:", value=f"`{song.artist} - {song.title}`")
        self.add_field(name="Запрос от:", value=f"{ctx.author.mention}")
        self.add_field(name="Длительность:", value=f"{seconds_to_time(song.duration)}.")


class QueueEmbed(discord.Embed):
    """Embed для списка очереди трэков"""
    def __init__(self, queue: List[Song], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = f"Очередь | Всего: `{len(queue)}`"
        self.color = discord.Color.dark_red()

        for i, song in enumerate(queue):
            self.add_field(name=f"`#{i+1}`", value=f"`{song.artist} - {song.title}`", inline=False)


class SearchEmbed(discord.Embed):
    """Embed результата поиска"""
    def __init__(self, queue: List[Song], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = f"Поиск"
        self.color = discord.Color.dark_red()

        for i, song in enumerate(queue):
            self.add_field(name=f"`#{i + 1}`", value=f"`{song.artist} - {song.title}`", inline=False)


class SearchVariantButton(discord.ui.Button):
    """Кнопка варианта выбора трэка"""
    def __init__(self, label: str, parent_view: discord.ui.View, callback_: Callable, song, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = discord.ButtonStyle.primary
        self.label = label
        self._parent_view = parent_view
        self._callback = callback_
        self._song = song

    async def callback(self, ctx: discord.Interaction):
        """Callback на нажатие кнопки"""
        self.style = discord.ButtonStyle.green

        await self._callback(self._song)
        await ctx.response.edit_message(view=self._parent_view)


class SearchView(discord.ui.View):
    """View с кнопками выбора трэка"""
    def __init__(self,
                 ctx: discord.ApplicationContext,
                 queue: List[Song],
                 songs: List[Song],
                 _play_next,
                 *args,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.timeout = 30
        self.disable_on_timeout = True

        self._ctx = ctx
        self._message = ctx.message
        self._songs = songs
        self._queue = queue
        self._play_next = _play_next

        for i, song in enumerate(self._songs):
            self.add_item(SearchVariantButton(label=f"{i+1}",
                                              parent_view=self,
                                              song=song,
                                              callback_=self.btn_callback))

    async def on_timeout(self):
        """Выходит с голосового канала если трэк не выбран и бот не проигрывает трэки"""
        if self._ctx.voice_client and not self._ctx.voice_client.is_playing():
            await self._ctx.voice_client.disconnect(force=True)

        self.disable_all_items()
        await self._message.edit(view=self)

    async def btn_callback(self, song: Song):
        """Callback для кнопки выбора трэка"""
        self._queue.append(song)

        if self._ctx.voice_client and self._ctx.voice_client.is_playing():
            await self._ctx.respond(f"**Добавлено в очередь `{song.artist} - {song.title}`. "
                                    f"Трэков впереди: `{len(self._queue)}`**")

        await self._play_next(self._ctx)

        self.disable_all_items()


class MusicCog(commands.Cog):
    """Cog музыкального плеера"""

    def __init__(self, bot_: discord.Bot):
        self._bot = bot_
        self._vk_search = VKMusicSearch(KateMobile, AccessCredentials)
        self._queue: List[Song] = []

    @commands.slash_command(name="play", description="Проигрывает музыку из ВКонтакте", guild_ids=GUILD_IDS)
    async def play_vkontakte(self, ctx: discord.ApplicationContext, song: Option(str, "Название трэка")):
        """Находит и запускает проигрывание трэка из ВКонтакте"""
        requestor_channel = ctx.author.voice.channel if ctx.author.voice else None
        voice_client = ctx.voice_client

        logger.info(f"{ctx.guild.name} | Вызов /play от {ctx.author.name} в чате {ctx.channel.name}. "
                    f"{f'Голосовой канал: {requestor_channel}. ' if requestor_channel else ''}Запрос: {song}.")

        if not requestor_channel:
            await ctx.respond("**Вы не находитесь в голосовом канале!**")
            return

        if not voice_client or not voice_client.is_connected():
            voice_client = await requestor_channel.connect()

        if voice_client and voice_client.channel != requestor_channel:
            await voice_client.disconnect(force=True)

        try:
            song = await self._vk_search.first_match(query=song)
        except Exception as e:
            logger.exception(e)
            await ctx.respond("**Сервис ВКонтакте сейчас не работает**")
            return

        self._queue.append(song)

        if voice_client.is_playing():
            await ctx.respond(f"**Добавлено в очередь `{song.artist} - {song.title}`. "
                              f"Трэков впереди: `{len(self._queue)}`**")
        else:
            await ctx.respond(f"**Запрошен трэк `{song.artist} - {song.title}`**")

        await self._play_next(ctx)

    @commands.slash_command(name="queue", description="Список трэков в очереди", guild_ids=GUILD_IDS)
    async def queue(self, ctx: discord.ApplicationContext):
        """Выводит трэки в очереди"""
        logger.info(f"{ctx.guild.name} | Вызов /queue от {ctx.author.name} в чате {ctx.channel.name}")
        if len(self._queue) == 0:
            await ctx.respond("**Очередь пуста**")
            return

        await ctx.respond(embed=QueueEmbed(self._queue))

    @commands.slash_command(name="search", description="Поиск музыки во ВКонтакте", guild_ids=GUILD_IDS)
    async def search_vkontakte(self, ctx: discord.ApplicationContext, song: Option(str, "Название трэка")):
        """Поиск музыки во ВКонтакте"""
        requestor_channel = ctx.author.voice.channel if ctx.author.voice else None
        voice_client = ctx.voice_client

        logger.info(f"{ctx.guild.name} | Вызов /search от {ctx.author.name} в чате {ctx.channel.name}. "
                    f"{f'Голосовой канал: {requestor_channel}. ' if requestor_channel else ''}Запрос: {song}.")

        if not requestor_channel:
            await ctx.respond("**Вы не находитесь в голосовом канале!**")
            return

        if not voice_client:
            await requestor_channel.connect()

        if voice_client and voice_client.channel != requestor_channel:
            await voice_client.disconnect(force=True)

        await ctx.defer()

        try:
            songs = await self._vk_search.all(query=song)
        except Exception as e:
            logger.exception(e)
            await ctx.respond("**Очередь пуста**")
            return

        await ctx.respond("", embed=SearchEmbed(songs), view=SearchView(ctx, self._queue, songs, self._play_next))

    @commands.slash_command(name="skip", description="Пропустить текущий трэк", guild_ids=GUILD_IDS)
    async def skip(self, ctx: discord.ApplicationContext):
        """Пропускает текущий трэк в проигрывателе"""
        logger.info(f"{ctx.guild.name} | Вызов /skip от {ctx.author.name} в чате {ctx.channel.name}")

        if not ctx.voice_client:
            await ctx.respond("**Бот не находится в голосовом канале!**")
            return

        if ctx.voice_client and not ctx.voice_client.is_playing():
            await ctx.respond("**Очередь пуста!**")
            return

        ctx.voice_client.stop()
        await ctx.respond("**Текущий трэк пропущен.**")

    @commands.slash_command(name="stop", description="Отключить проигрыватель", guild_ids=GUILD_IDS)
    async def stop(self, ctx: discord.ApplicationContext):
        """Отключает проигрыватель и очищает очередь"""
        logger.info(f"{ctx.guild.name} | Вызов /stop от {ctx.author.name} в чате {ctx.channel.name}")

        if not ctx.voice_client:
            await ctx.respond("**Бот не находится в голосовом канале!**")
            return

        ctx.voice_client.stop()
        self._queue.clear()
        await ctx.respond("**Проигрыватель отключён.**")

    async def _play_next(self, ctx: discord.ApplicationContext):
        """Запускает проигрывание трэка из очереди"""
        if len(self._queue) == 0:
            if ctx.voice_client:
                await ctx.voice_client.disconnect(force=True)

            await ctx.send("**Проигрыватель закончил свою работу.**")

            logger.info(f"{ctx.guild.name} | Сессия проигрывателя закончена.")

            return

        if ctx.voice_client and ctx.voice_client.is_playing():
            return

        song = self._queue.pop(0)

        logger.info(f"{ctx.guild.name} | Запущен трэк {song.artist} - {song.title} в канале {ctx.author.voice.channel}")

        ctx.voice_client.play(
            source=discord.FFmpegOpusAudio(song.link, bitrate=BITRATE, executable=FFMPEG),
            after=lambda _: self._bot.loop.create_task(self._play_next(ctx))
        )

        await ctx.send(embed=StartingToPlayEmbed(ctx, song))
