from typing import Protocol, Sequence

from ..domain.entities import ScheduleItem


class ScheduleSourcePort(Protocol):
    def fetch_schedule(self) -> Sequence[ScheduleItem]:
        ...
