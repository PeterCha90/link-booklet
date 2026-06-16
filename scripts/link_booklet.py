#!/usr/bin/env python3
"""Manage Link Booklet JSON files for Hermes skills."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_booklet(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "channel_id": path.stem,
            "source": "unknown",
            "items": [],
            "read_items": [],
            "updated_at": now_iso(),
            "notes": "Created by link-booklet helper.",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_booklet(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now_iso()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def broad_category(raw: str | None, locale: str = "en") -> str:
    if not raw:
        return "기타" if locale == "ko" else "Other"
    text = str(raw).strip()
    for sep in ("·", "/", "|", ":", "-", "—"):
        if sep in text:
            text = text.split(sep, 1)[0].strip()
    return text or ("기타" if locale == "ko" else "Other")


def unread_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    read_ids = {int(x) for x in data.get("read_items", []) if str(x).isdigit()}
    result: list[dict[str, Any]] = []
    for item in data.get("items", []):
        try:
            item_id = int(item.get("id"))
        except (TypeError, ValueError):
            item_id = None
        if item.get("status", "unread") == "unread" and item_id not in read_ids:
            result.append(item)
    return result


def display_date(item: dict[str, Any]) -> str:
    raw = str(item.get("date") or "").strip()
    return raw[:10] if len(raw) >= 10 else raw


def render_markdown(data: dict[str, Any], locale: str = "en") -> str:
    items = unread_items(data)
    header = ":bookmark_tabs: *읽지 않은 책갈피*" if locale == "ko" else ":bookmark_tabs: *Unread Link Booklet*"
    empty = "읽지 않은 책갈피가 없습니다." if locale == "ko" else "No unread links."
    date_label = "등록일" if locale == "ko" else "Added"

    lines: list[str] = [header, ""]
    if not items:
        lines.append(empty)
        return "\n".join(lines)

    display_no_by_id: dict[int, int] = {}
    for display_no, item in enumerate(items, start=1):
        try:
            display_no_by_id[int(item.get("id"))] = display_no
        except (TypeError, ValueError):
            continue

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(broad_category(item.get("category"), locale), []).append(item)

    for category, group in grouped.items():
        lines.append(f"`{category}`")
        lines.append("")
        for item in group:
            title = item.get("title") or "Untitled"
            try:
                display_no = display_no_by_id[int(item.get("id"))]
            except (TypeError, ValueError, KeyError):
                display_no = "?"
            summary = item.get("summary") or ("요약 없음." if locale == "ko" else "No summary.")
            url = item.get("url") or ""
            date = display_date(item)
            lines.append(f"**{display_no}. {title}**  ")
            if date:
                lines.append(f"{date_label}: {date}  ")
            lines.append(f"{summary}  ")
            if url:
                lines.append(f"[Link]({url})")
            lines.append("")
    return "\n".join(lines).rstrip()


def cmd_show(args: argparse.Namespace) -> None:
    data = load_booklet(Path(args.path).expanduser())
    print(render_markdown(data, args.locale))


def cmd_mark_read(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    data = load_booklet(path)
    requested = [int(x) for x in args.ids]

    if args.by_id:
        stable_ids = set(requested)
    else:
        current_unread = unread_items(data)
        stable_ids = set()
        for display_no in requested:
            if 1 <= display_no <= len(current_unread):
                try:
                    stable_ids.add(int(current_unread[display_no - 1].get("id")))
                except (TypeError, ValueError):
                    continue

    read_items = {int(x) for x in data.get("read_items", []) if str(x).isdigit()}
    read_items.update(stable_ids)
    data["read_items"] = sorted(read_items)
    for item in data.get("items", []):
        try:
            if int(item.get("id")) in stable_ids:
                item["status"] = "read"
        except (TypeError, ValueError):
            continue
    save_booklet(path, data)
    print("Marked read: " + ", ".join(map(str, requested)))


def cmd_add(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    data = load_booklet(path)
    items = data.setdefault("items", [])
    existing_ids = [int(x.get("id", 0)) for x in items if str(x.get("id", "")).isdigit()]
    next_id = max(existing_ids or [0]) + 1
    item = {
        "id": next_id,
        "status": "unread",
        "category": args.category,
        "title": args.title,
        "url": args.url,
        "source_type": args.source_type,
        "date": args.date or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": args.summary or "",
        "key_points": args.key_points or [],
    }
    items.append(item)
    save_booklet(path, data)
    print(f"Added: {next_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Link Booklet JSON files")
    sub = parser.add_subparsers(required=True)

    show = sub.add_parser("show", help="Render unread markdown booklet")
    show.add_argument("path")
    show.add_argument("--locale", choices=["en", "ko"], default="en")
    show.set_defaults(func=cmd_show)

    mark = sub.add_parser("mark-read", help="Mark displayed unread bookmark numbers as read")
    mark.add_argument("path")
    mark.add_argument("ids", nargs="+")
    mark.add_argument("--by-id", action="store_true", help="Treat numbers as stable JSON item IDs instead of display numbers")
    mark.set_defaults(func=cmd_mark_read)

    add = sub.add_parser("add", help="Add a new unread link item")
    add.add_argument("path")
    add.add_argument("--title", required=True)
    add.add_argument("--url", required=True)
    add.add_argument("--category", default="Other")
    add.add_argument("--summary", default="")
    add.add_argument("--source-type", default="web")
    add.add_argument("--date", default="")
    add.add_argument("--key-points", nargs="*")
    add.set_defaults(func=cmd_add)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
