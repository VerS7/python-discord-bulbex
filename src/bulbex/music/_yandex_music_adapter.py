"""
Поисковик музыки в Yandex.Music
"""

from yandex_music import ClientAsync
from .song import Song, Playlist, Search


class YandexMusicSearch(Search):
    """Поисковик трэков в Яндекс.Музыке"""

    def __init__(self, token: str) -> None:
        self._client = ClientAsync(token)

    async def async_init_client(self) -> None:
        """Асинхронная инициализация клиента"""
        await self._client.init()

    async def first_match(self, query: str) -> Song:
        """Возвращает первый найденный трэк по запросу"""
        response = await self._search(query, count=1)
        track = response[0]
        download_info = await track.get_download_info(get_direct_links=True)
        direct_link = await download_info[0].get_direct_link_async()

        return Song(
            artist=", ".join([a.name for a in track.artists]),
            title=track.title,
            duration=int(track.duration_ms / 1000),
            download_link=direct_link,
        )

    async def all(self, query: str, count: int = 5) -> Playlist:
        """Возвращает список трэков по запросу и количеству"""
        response = await self._search(query, count)
        tracks = []

        for track in response:
            download_info = await track.get_download_info(get_direct_links=True)
            direct_link = await download_info[0].get_direct_link_async()

            tracks.append(
                Song(
                    artist=", ".join([a.name for a in track.artists]),
                    title=track.title,
                    duration=int(track.duration_ms / 1000),
                    download_link=direct_link,
                )
            )

        return Playlist(tracks)

    def playlist(self, url: str) -> Playlist:
        raise NotImplementedError()

    async def _search(self, query: str, count: int):
        """Запрашивает трэки"""
        response = await self._client.search(type_="track", text=query)
        return response.tracks.results[:count]
