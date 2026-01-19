from typing import Protocol, Sequence

from ..domain.entities import EpisodeExternal


class EpisodeSourcePort(Protocol):
    def fetch_episodes(self) -> Sequence[EpisodeExternal]:
        ...
