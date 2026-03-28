from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, TypeVar

import fcntl

from .models import UsersState


T = TypeVar("T")


class JsonStorage:
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.lock_path = self.file_path.with_name(self.file_path.name + ".lock")

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_path, "a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load_unlocked(self) -> UsersState:
        if not self.file_path.exists():
            return UsersState()
        with open(self.file_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return UsersState.from_dict(payload)

    def load_state(self) -> UsersState:
        with self._lock():
            return self._load_unlocked()

    def _write_unlocked(self, state: UsersState) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = state.to_dict()
        fd, temp_path = tempfile.mkstemp(
            prefix=f".{self.file_path.name}.",
            suffix=".tmp",
            dir=str(self.file_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temp_path, self.file_path)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def save_state(self, state: UsersState) -> None:
        with self._lock():
            self._write_unlocked(state)

    def update(self, callback: Callable[[UsersState], T]) -> T:
        with self._lock():
            state = self._load_unlocked()
            result = callback(state)
            state.touch()
            self._write_unlocked(state)
            return result
