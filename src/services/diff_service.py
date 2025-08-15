import asyncio
import difflib
from typing import Any, Dict, List


class DiffService:
    """Compute diffs between two blobs and return structured hunks."""

    async def compute_diff(self, before: str, after: str) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()

        def _compute() -> List[Dict[str, Any]]:
            before_lines = before.splitlines()
            after_lines = after.splitlines()
            diff_iter = difflib.unified_diff(before_lines, after_lines, lineterm="")

            hunks: List[Dict[str, Any]] = []
            hunk: Dict[str, Any] | None = None

            for line in diff_iter:
                if line.startswith("---") or line.startswith("+++"):
                    continue
                if line.startswith("@@"):
                    if hunk:
                        hunks.append(hunk)
                    header = line[3:-3]
                    old_range, new_range = header.split(" ")

                    def _parse(r: str) -> tuple[int, int]:
                        r = r[1:]  # drop +/-
                        if "," in r:
                            start, count = r.split(",")
                        else:
                            start, count = r, "1"
                        return int(start), int(count)

                    old_start, old_len = _parse(old_range)
                    new_start, new_len = _parse(new_range)
                    hunk = {
                        "old_start": old_start,
                        "old_lines": old_len,
                        "new_start": new_start,
                        "new_lines": new_len,
                        "lines": [],
                    }
                else:
                    if hunk is None:
                        continue
                    hunk["lines"].append(line)

            if hunk:
                hunks.append(hunk)
            return hunks

        return await loop.run_in_executor(None, _compute)

