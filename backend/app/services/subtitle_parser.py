import re
import uuid
from io import BytesIO

import pysubs2

from ..models.schemas import SubtitleBlock


def _strip_ass_tags(text: str) -> str:
    """Remove ASS override tags like {\\b1}, {\\pos(x,y)}, etc."""
    return re.sub(r"\{[^}]*\}", "", text)


def _generate_block_id(subtitle_set_id: str, index: int) -> str:
    return f"{subtitle_set_id}-{index:06d}"


def parse_subtitle_file(
    file_content: bytes, filename: str, subtitle_set_id: str | None = None
) -> list[SubtitleBlock]:
    """Parse an ASS/SSA/SRT subtitle file into normalized SubtitleBlock list."""
    if subtitle_set_id is None:
        subtitle_set_id = uuid.uuid4().hex[:12]

    subs = pysubs2.SSAFile.from_string(file_content.decode("utf-8-sig"))

    raw_events = []
    for event in subs.events:
        if event.is_comment:
            continue
        raw_text = event.text
        display_text = _strip_ass_tags(raw_text).replace("\\N", "\n").replace("\\n", "\n").strip()
        if not display_text:
            continue
        raw_events.append(
            {
                "start_ms": event.start,
                "end_ms": event.end,
                "raw_text": raw_text,
                "display_text": display_text,
            }
        )

    # Sort by start time
    raw_events.sort(key=lambda e: e["start_ms"])

    # Merge adjacent events that likely form one utterance
    merged = _merge_events(raw_events)

    blocks = []
    for i, ev in enumerate(merged):
        block = SubtitleBlock(
            id=_generate_block_id(subtitle_set_id, i),
            start_ms=ev["start_ms"],
            end_ms=ev["end_ms"],
            raw_text=ev["raw_text"],
            display_text=ev["display_text"],
            normalized_text=ev["display_text"].replace("\n", ""),
        )
        blocks.append(block)

    return blocks


def _merge_events(events: list[dict], gap_threshold_ms: int = 100) -> list[dict]:
    """Merge adjacent subtitle events that are close together and short."""
    if not events:
        return []

    merged = [events[0].copy()]

    for ev in events[1:]:
        prev = merged[-1]
        gap = ev["start_ms"] - prev["end_ms"]
        combined_text = prev["display_text"] + ev["display_text"]

        # Merge if gap is small and combined text is reasonably short
        if gap <= gap_threshold_ms and len(combined_text) < 80:
            prev["end_ms"] = max(prev["end_ms"], ev["end_ms"])
            prev["raw_text"] += "\\N" + ev["raw_text"]
            prev["display_text"] += "\n" + ev["display_text"]
        else:
            merged.append(ev.copy())

    return merged
