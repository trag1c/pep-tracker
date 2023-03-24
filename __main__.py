from __future__ import annotations

import datetime as dt
import json
import requests
import sys
from pathlib import Path
from typing import NoReturn

from dahlia import dahlia, dprint


COLOR_CODES = {
    "Accepted": "&2",
    "Active": "&a",
    "Deferred": "&c",
    "Draft": "&8",
    "Final": "&1",
    "Provisional": "&5",
    "Rejected": "&4",
    "Replaced": "&e",
    "Withdrawn": "&d",
}
LATEST = Path("pep-tracker/latest.json")
URL = "https://peps.python.org/api/peps.json"


class State:
    def __init__(
        self,
        data: dict[str, str],
        registered_at: dt.datetime | None = None
    ) -> None:
        self._data = data
        self.date = registered_at or dt.datetime.now(tz=dt.timezone.utc)

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __xor__(self, other: State) -> dict[str, tuple[str, str]]:
        return {k: (self[k], other[k]) for k in self._data if self[k] != other[k]}

    def dump(self) -> str:
        return json.dumps(self._data, indent=2)


def get_last_state() -> State:
    if not LATEST.exists():
        dprint("&4latest.json not found.", file=sys.stderr)
        LATEST.write_text(get_current_state().dump())
        dexit("&2latest.json created. Run the program again.")
    with LATEST.open() as f:
        return State(
            json.load(f),
            dt.datetime.fromtimestamp(LATEST.stat().st_mtime, tz=dt.timezone.utc)
        )


def get_current_state() -> State:
    try:
        req = requests.get(URL, timeout=15)
    except (requests.ReadTimeout):
        dexit("&4Connection timed out.")
    if req.status_code != 200:
        dexit(f"API response code: {req.status_code}")
    return State({k: v["status"] for k, v in json.loads(req.text).items()})


def pretty_delta(a: dt.datetime, b: dt.datetime) -> str:
    days, seconds = divmod(round((b - a).total_seconds()), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return f"{days} days" if days != 1 else "day"
    if hours > 0:
        return f"{hours} hours" if hours != 1 else "hour"
    if minutes > 0:
        return f"{minutes} minutes" if minutes != 1 else "minute"
    return f"{seconds} seconds" if seconds != 1 else "second"


def fmt(statuses: tuple[str, str]) -> str:
    return "&r -> ".join(COLOR_CODES[status] + status for status in statuses)


def dexit(message: str) -> NoReturn:
    sys.exit(dahlia(message))


def main() -> None:
    old = get_last_state()
    new = get_current_state()

    diff = old ^ new
    delta = pretty_delta(old.date, new.date)

    if not diff:
        dexit(f"&cNo updates detected in the last {delta}.")

    dprint(f"Updates detected in the last {pretty_delta(old.date, new.date)}:")
    for k, v in diff.items():
        dprint(f"&lPEP {k}:&r {fmt(v)}")


    with LATEST.open("w") as f:
        f.write(new.dump())


if __name__ == "__main__":
    main()
