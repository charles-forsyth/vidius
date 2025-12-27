import json
from typing import Any, Optional, cast

import pandas as pd

from vidius.config import settings


class HistoryManager:
    def __init__(self) -> None:
        self.file_path = settings.history_file

    def load(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path) as f:
                data = json.load(f)
                return cast(list[dict[str, Any]], data)
        except json.JSONDecodeError:
            return []

    def save(self, entry: dict[str, Any]) -> None:
        history = self.load()
        history.append(entry)
        with open(self.file_path, "w") as f:
            json.dump(history, f, indent=4)

    def display(self) -> None:
        history = self.load()
        if not history:
            print("No history found.")
            return

        try:
            df = pd.DataFrame(history)
            cols = ["prompt", "output_file", "duration"]
            if not df.empty:
                df.index = df.index + 1
                print(df[cols].to_markdown())
            else:
                print("History is empty.")
        except ImportError:
            for i, entry in enumerate(history):
                print(f"{i + 1}: {entry.get('prompt')} (File: {entry.get('output_file')})")

    def get_entry(self, index: int) -> Optional[dict[str, Any]]:
        history = self.load()
        if 1 <= index <= len(history):
            return history[index - 1]
        return None
