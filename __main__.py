from __future__ import annotations

import datetime as dt
import json
import sys
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, NewType, NoReturn, TypedDict, cast

import requests
from dahlia import dahlia, dprint

if TYPE_CHECKING:
    from typing_extensions import Self


__version__ = "0.1.0"


class Status(str, Enum):
    def _generate_next_value_(  # type: ignore
        name: str, start: int, count: int, last_values: list[str]
    ) -> str:
        # https://github.com/python/mypy/issues/7591
        return name.title().replace("_", " ")

    ACCEPTED = auto()
    ACTIVE = auto()
    DEFERRED = auto()
    DRAFT = auto()
    FINAL = auto()
    PROVISIONAL = auto()
    REJECTED = auto()
    REPLACED = auto()
    WITHDRAWN = auto()
    SUPERSEDED = auto()


COLOR_CODES = {
    Status.ACCEPTED: "&2",
    Status.ACTIVE: "&a",
    Status.DEFERRED: "&6",
    Status.DRAFT: "&8",
    Status.FINAL: "&1",
    Status.PROVISIONAL: "&5",
    Status.REJECTED: "&4",
    Status.REPLACED: "&e",
    Status.WITHDRAWN: "&d",
    Status.SUPERSEDED: "",  # FIXME Pick color
}

LATEST = Path(__file__).parent.resolve() / "latest.json"
URL = "https://peps.python.org/api/peps.json"
PEP = NewType("PEP", str)


def now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


class StateDict(TypedDict):
    version: str
    data: dict[str, str]
    datetime: str


class State:
    version: ClassVar[str] = __version__

    def __init__(
        self, data: dict[PEP, Status], datetime: dt.datetime | None = None
    ) -> None:
        self._data = data
        self.datetime = datetime or now()

    def __getitem__(self, key: PEP) -> Status:
        return self._data[key]

    def __xor__(self, other: State) -> dict[PEP, tuple[Status, Status]]:
        # FIXME Handle PEPs that have been newly added, and are only on `other`
        return {k: (self[k], other[k]) for k in self._data if self[k] is not other[k]}

    @classmethod
    def from_api(cls, data: dict[str, dict[str, str]]) -> Self:
        return cls(data={PEP(k): Status(v["status"]) for k, v in data.items()})

    @classmethod
    def _migrate(cls, old: dict[str, Any] | StateDict) -> StateDict:
        out = StateDict(version=cls.version, data={}, datetime=now().isoformat())
        old_version = old.get("version")
        if old_version is None:
            data = cast("dict[str, str]", old.copy())
            out["data"] = data
        else:
            out = cast(StateDict, old)
        return out

    @classmethod
    def from_dict(cls, state: StateDict | dict[str, Any]) -> Self:
        state_dict = cls._migrate(state)
        data_raw = state_dict["data"]
        data = {PEP(k): Status(v) for k, v in data_raw.items()}
        datetime = dt.datetime.fromisoformat(state_dict["datetime"])
        return cls(data=data, datetime=datetime)

    def to_dict(self) -> StateDict:
        return StateDict(
            version=self.version,
            data={str(k): v.value for k, v in self._data.items()},
            datetime=self.datetime.isoformat(),
        )


def write_latest(state: State) -> None:
    LATEST.write_text(json.dumps(state.to_dict(), indent=2))


def get_last_state() -> State:
    if not LATEST.exists():
        dprint(f"&4{LATEST.name} not found.", file=sys.stderr)
        write_latest(get_current_state())
        dexit(f"&2{LATEST.name} created. Run the program again.")
    with LATEST.open() as f:
        return State.from_dict(json.loads(f.read()))


def get_current_state() -> State:
    try:
        req = requests.get(URL, timeout=15)
        req.raise_for_status()
    except requests.ReadTimeout:
        dexit("&4Connection timed out.")
    except requests.exceptions.HTTPError:
        dexit(f"API response code: {req.status_code}")
    return State.from_api(json.loads(req.text))


def pretty_delta(delta: dt.timedelta) -> str:
    seconds = round(delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days:
        return f"{days} days" if days > 1 else "day"
    if hours:
        return f"{hours} hours" if hours > 1 else "hour"
    if minutes:
        return f"{minutes} minutes" if minutes > 1 else "minute"
    return f"{seconds} seconds" if seconds > 1 else "second"


def fmt(statuses: tuple[Status, Status]) -> str:
    return "&r -> ".join(COLOR_CODES[status] + status for status in statuses)


def dexit(message: str) -> NoReturn:
    sys.exit(dahlia(message))


def main() -> None:
    old = get_last_state()
    new = get_current_state()

    diff = old ^ new
    delta = pretty_delta(new.datetime - old.datetime)

    if not diff:
        dprint(f"&cNo updates detected in the last {delta}.")
        return

    dprint(f"Updates detected in the last {delta}:")
    for k, v in diff.items():
        dprint(f"&lPEP {k}:&r {fmt(v)}")

    write_latest(new)

    return


if __name__ == "__main__":
    main()
