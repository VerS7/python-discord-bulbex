"""
Поисковик музыки во ВКонтакте
"""
import re
import asyncio

from typing import List, Tuple

from urllib.parse import urlparse

import aiohttp.web
from aiohttp import ClientSession, TCPConnector
from aiohttp.web import HTTPNotFound

from .config import VK_LOGIN, VK_PASSWORD, VK_BYPASS_AUTH, VK_BYPASS_ACCESS_TOKEN

PLAYLIST_ID_PATTERN = r"(?<=_)\d+(?=_)"
PLAYLIST_OWNER_PATTERN = r"-?\d+(?=_)"


def parse_playlist_url(url: str) -> Tuple[str, str]:
    """Возвращает код плейлиста по url"""
    url_data = urlparse(url)
    if "vk.com" not in url_data.netloc:
        raise ValueError("Переданный url не принадлежит vk.com")

    if not url_data.path:
        raise ValueError("Переданный url некорректный.")

    match_id = re.search(PLAYLIST_ID_PATTERN, url_data.path)
    match_owner = re.search(PLAYLIST_OWNER_PATTERN, url_data.path)
    if match_id and match_owner:
        return match_id.group(), match_owner.group()

    raise ValueError("Переданный url некорректный.")


class Credentials:
    """Логин и пароль для доступа во ВКонтакте"""

    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password


class Client:
    """Клиент для работы с ВКонтакте"""

    def __init__(self, user_agent: str, client_id: str, client_secret: str):
        self.user_agent = user_agent
        self.client_id = client_id
        self.client_secret = client_secret


class Song:
    """Трэк"""

    def __init__(self, artist: str, title: str, duration: int, download_link: str):
        self.artist = artist
        self.title = title
        self.duration = duration
        self.link = download_link

    def __repr__(self):
        return f"{self.artist} - {self.title}. Duration: {self.duration}s. Download: {self.link}"


class VKMusicSearch:
    """Поисковик трэков"""

    def __init__(self, client: Client, credentials: Credentials):
        self._client = client
        self._creds = credentials

        if VK_BYPASS_AUTH and VK_BYPASS_ACCESS_TOKEN:
            self._access_token = VK_BYPASS_ACCESS_TOKEN
        else:
            self._access_token = self._update_access_token()

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        self.session = ClientSession(headers={"User-Agent": self._client.user_agent}, loop=loop)

    async def first_match(self, query: str) -> Song:
        """Возвращает первый найденный трэк по запросу"""
        response = await self._search(query, count=1)
        content = response["response"]["items"][0]

        return Song(artist=content["artist"],
                    title=content["title"],
                    duration=content["duration"],
                    download_link=content["url"])

    async def all(self, query: str, count: int = 5) -> List[Song]:
        """Возвращает список трэков по запросу и количеству"""
        content = await self._search(query, count=count)
        songs = []

        for item in content["response"]["items"]:
            songs.append(Song(artist=item["artist"],
                              title=item["title"],
                              duration=item["duration"],
                              download_link=item["url"]))

        return songs

    async def playlist(self, playlist_url: str) -> Tuple[List[Song], int]:
        """Возвращает плейлист с трэками по url"""
        playlist_id, owner_id = parse_playlist_url(playlist_url)
        content = await self._playlist(owner_id, playlist_id)
        initial_tracks_count = content["response"]["count"]
        songs = []

        for item in content["response"]["items"]:
            if not item["url"]:
                continue

            songs.append(Song(artist=item["artist"],
                              title=item["title"],
                              duration=item["duration"],
                              download_link=item["url"]))

        return songs, initial_tracks_count

    async def _update_access_token(self) -> None:
        """Обновляет токен доступа"""
        content = await self._request_auth()
        if "error" in content.keys() and "Flood control" in content["error"]:
            raise aiohttp.web.HTTPException(text="Bruteforce error. "
                                                 "Слишком много запросов на верификацию, "
                                                 "лучше попробовать позже.")

        self._access_token = ["access_token"]

    async def _playlist(self, owner_id: str, playlist_id: str):
        """Запрашивает плейлист по id пользователя и id плейлиста"""
        if not self._access_token:
            await self._update_access_token()

        params = [
            ("access_token", self._access_token),
            ("https", 1),
            ("lang", "ru"),
            ("extended", 1),
            ("v", "5.131"),
            ("count", "1000"),
            ("owner_id", owner_id),
            ("album_id", playlist_id)
        ]

        async with self.session.post(f"https://api.vk.com/method/audio.get", data=params, ssl=False) as response:
            data = await response.json()
            if "error" in data.keys():
                raise HTTPNotFound()
            return data

    async def _search(self, query: str, count: int):
        """Запрашивает трэки"""
        if not self._access_token:
            await self._update_access_token()

        params = [
            ("access_token", self._access_token),
            ("https", 1),
            ("lang", "ru"),
            ("extended", 1),
            ("v", "5.131"),
            ("q", query),
            ("count", count),
            ("offset", 0),
            ("sort", 0),
            ("autocomplete", 1)
        ]

        async with self.session.post(f"https://api.vk.com/method/audio.search", data=params, ssl=False) as response:
            return await response.json()

    async def _request_auth(self):
        """Запрашивает OAuth ВКонтакте"""
        params = [
            ("grant_type", "password"),
            ("client_id", self._client.client_id),
            ("client_secret", self._client.client_secret),
            ("username", self._creds.login),
            ("password", self._creds.password),
            ("scope", "audio,offline"),
            ("v", 5.131),
        ]

        session = ClientSession(headers={"User-Agent": self._client.user_agent})

        async with session.post("https://oauth.vk.com/token", data=params, ssl=False) as response:
            return await response.json()


KateMobile = Client(
    user_agent="KateMobileAndroid/56 lite-460 (Android 4.4.2; SDK 19; x86; unknown Android SDK built for x86; en)",
    client_id="2685278",
    client_secret="lxhD8OD7dMsqtXIm5IUY",
)

AccessCredentials = Credentials(
    login=VK_LOGIN,
    password=VK_PASSWORD,
)
