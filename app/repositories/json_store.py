import json
import os
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_storage_lock = Lock() # All JSON reads and updates take turns using this lock


def data_path(filename: str) -> Path:
    folder = Path(os.environ.get("DATA_DIR", "data"))
    if not folder.is_absolute():
        folder = PROJECT_ROOT / folder
    return folder / filename


def _read(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected a JSON list of records")

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each record must be a JSON object")

    return records


def _save(path: Path, records: list[dict]) -> None:
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(records, file, ensure_ascii=False, indent=2)
            file.write("\n")

        os.replace(temporary_path, path) # Close the temp file before replacing the original
    finally:
        if temporary_path is not None: # Remove the temp file if saving failed
            temporary_path.unlink(missing_ok=True)


def read_records(path: str | Path) -> list[dict]:
    path = Path(path).resolve()
    with _storage_lock:
        return _read(path)


def update_records(
    path: str | Path,
    change: Callable[[list[dict]], Any],
) -> Any:
    """Run a repository's change function and save before returning its result."""
    path = Path(path).resolve()

    with _storage_lock:
        records = _read(path)
        result = change(records) # The repository changes this list while the storage lock is held
        _save(path, records)
        return result
