from typing import Protocol, Sequence

from ..domain.entities import AnimeExternal


class CatalogSourcePort(Protocol):
    def fetch_catalog(self) -> Sequence[AnimeExternal]:
        ...
