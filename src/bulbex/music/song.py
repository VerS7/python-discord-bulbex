"""
Всё про трэки
"""

from typing import List
from random import shuffle
from abc import ABC, abstractmethod


class Song:
    """Обычный трэк"""

    def __init__(
        self,
        artist: str,
        title: str,
        duration: int,
        download_link: str,
        image: str | None = None,
    ) -> None:
        self.artist: str = artist
        self.title: str = title
        self.duration: int = duration
        self.link: str = download_link
        self.image: str | None = image

    def __repr__(self):
        return f"{self.artist} - {self.title}. Duration: {self.duration}s. Download: {self.link}"


class Playlist:
    """Плейлист трэков"""

    def __init__(
        self,
        from_songs: List[Song],
        name: str | None = None,
        image: str | None = None,
    ) -> None:
        self.image: str | None = image
        self.name: str | None = name
        self._songs: List[Song] = from_songs

    def __repr__(self):
        return str(self._songs)

    def __getitem__(self, index) -> Song:
        if index > len(self._songs):
            raise IndexError("Индекс больше длины плейлиста.")
        return self._songs[index]

    def __iter__(self):
        for song in self._songs:
            yield song

    @property
    def duration(self) -> int:
        """Возвращает суммарную длительность трэков в секундах"""
        return sum((d.duration for d in self._songs))

    def shuffle(self) -> "Playlist":
        """Возвращает перемешанный плейлист"""
        shuffle(self._songs)
        return self


class Search(ABC):
    """Абстрактный класс поисковика музыки"""

    @abstractmethod
    def first_match(self, query: str) -> Song:
        pass

    @abstractmethod
    def all(self, query: str, count: int) -> Playlist:
        pass

    @abstractmethod
    def playlist(self, url: str) -> Playlist:
        pass
