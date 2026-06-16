---
name: link-bookmark
description: Use when collecting, maintaining, or showing unread link bookmarks from chat channels. Stores link metadata in channel-specific JSON files, renders clean unread digests, and supports explicit read marking.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [links, bookmarks, slack, productivity, json, summaries]
    related_skills: []
---

# Link Bookmark

## Overview

Link Bookmark is a lightweight Hermes skill for turning links shared in chat into a clean unread bookmark digest. It is useful for Slack, Discord, Telegram, or any other channel where people drop links that should be collected, summarized, and reviewed later.

The skill uses a simple JSON file as the source of truth. Each channel gets its own bookmark file under `~/.hermes/link_bookmarks/` by default. Hermes reads the file, filters unread items, groups them by broad category, re-numbers them for display, and renders a concise report. Items are marked read only when the user explicitly asks.

This skill intentionally does not require Slack/Discord history APIs. If Hermes cannot search channel history, add links from messages that are delivered to Hermes, from URLs supplied by the user, or from manually edited JSON.

## When to Use

Use this skill when the user asks for things like:

- "show bookmarks" / "bookmarks"
- "책갈피 보여줘" / "책갈피"
- "show unread links"
- "summarize unread links"
- "add this link to the bookmark list"
- "mark 1 and 3 as read"
- "1번 읽음 처리해줘"
- "전부 읽음 처리해줘"

Do not use this skill for:

- Browser bookmark synchronization
- Full RSS/news monitoring from external feeds
- Tasks that require live Slack/Discord history access when the gateway does not expose those APIs

## Data Location

Recommended default path:

```text
~/.hermes/link_bookmarks/<channel-or-context-id>.json
```

For backward compatibility with older link-report setups, you may also read from:

```text
~/.hermes/link_reports/<channel-or-context-id>.json
```

Use one JSON file per channel/context so read state is independent.

## JSON Schema

```json
{
  "channel_id": "example-channel",
  "source": "slack",
  "items": [
    {
      "id": 1,
      "status": "unread",
      "category": "AI·Tools",
      "title": "Example AI Tool",
      "url": "https://example.com",
      "source_type": "web",
      "date": "2026-06-16 09:00",
      "summary": "A concise summary of the link.",
      "key_points": ["Point 1", "Point 2"]
    }
  ],
  "read_items": [],
  "updated_at": "2026-06-16T09:00:00+09:00",
  "notes": "Optional operating notes."
}
```

Required item fields are `id`, `url`, and `title`. The other fields improve rendering and organization. Keep `id` stable forever; display numbers are temporary and are re-created on every report.

## Report Formatting

Default report format:

```md
:bookmark_tabs: *Unread Link Bookmark*

`AI`

**1. Example AI Tool**  
Added: 2026-06-16  
A concise summary of the link.  
[Link](https://example.com)
```

Korean report format when the user is using Korean or says `책갈피`:

```md
:bookmark_tabs: *읽지 않은 책갈피*

`AI`

**1. Example AI Tool**  
등록일: 2026-06-16  
A concise summary of the link.  
[Link](https://example.com)
```

Formatting rules:

- Show only unread items.
- Re-number unread items from 1 to N every time, even if underlying stable JSON IDs have gaps.
- Group by broad category.
- Render categories as code labels, e.g. `` `AI` ``.
- Render titles in bold.
- Use `[Link](url)` labels instead of raw URLs.
- Show the original registration date as `Added: YYYY-MM-DD` or `등록일: YYYY-MM-DD` when available.
- Keep output concise.

## Category Normalization

Normalize detailed categories to broad scan-friendly labels by splitting on common separators and keeping the first segment.

Examples:

| Raw category | Display category |
| --- | --- |
| `AI·Tools` | `AI` |
| `AI·Research/Industry` | `AI` |
| `Development·Workflow` | `Development` |
| `Business·Strategy` | `Business` |
| `생산성·노트` | `생산성` |

If no category exists, use `Other` for English output or `기타` for Korean output.

## Operating Procedure

### Show unread bookmarks

1. Identify the current channel/context ID.
2. Read `~/.hermes/link_bookmarks/<channel-id>.json`. If absent and a legacy file exists, read `~/.hermes/link_reports/<channel-id>.json`.
3. Filter items where `status == "unread"` and the stable `id` is not in `read_items`.
4. Normalize categories.
5. Group items by category while preserving item order.
6. Re-number displayed items from 1 to N across the whole unread list.
7. Render the clean Markdown report.
8. Do not mark anything read unless the user explicitly asks.

### Add a link

1. Extract URL, title, source type, and date from the user message or channel metadata.
2. If web access is available, fetch the URL and write a concise summary.
3. Assign the next stable integer ID: `max(existing ids) + 1`.
4. Set `status` to `unread`.
5. Store a useful category. It can be more detailed than the display category.
6. Update `updated_at`.
7. Save the JSON with UTF-8 and two-space indentation.

### Mark items read

Only mark read when the user explicitly requests it.

1. Treat user-facing numbers as the current displayed unread positions, not stable JSON IDs, unless the user explicitly says `by id` or `raw id`.
2. Map display positions back to stable JSON IDs.
3. Add those stable IDs to `read_items`.
4. Set matching item `status` to `read`.
5. Update `updated_at`.
6. Confirm briefly.

## Helper Script

This repository includes `scripts/link_bookmark.py` for deterministic operations:

```bash
python scripts/link_bookmark.py show ~/.hermes/link_bookmarks/my-channel.json
python scripts/link_bookmark.py show ~/.hermes/link_bookmarks/my-channel.json --locale ko
python scripts/link_bookmark.py add ~/.hermes/link_bookmarks/my-channel.json --title "Example" --url "https://example.com" --category "AI·Tools" --summary "Short summary"
python scripts/link_bookmark.py mark-read ~/.hermes/link_bookmarks/my-channel.json 1 3 5
python scripts/link_bookmark.py mark-read ~/.hermes/link_bookmarks/my-channel.json --by-id 42
```

## Common Pitfalls

1. **Marking items read just because a report was shown.** Showing a report does not mean the user read the links. Mark read only after explicit instruction.

2. **Confusing display numbers with stable IDs.** User-facing numbers are temporary unread-list positions. Stable IDs stay inside JSON.

3. **Depending on Slack history APIs.** Hermes gateway sessions may not expose channel history. Use delivered messages, user-provided URLs, or the JSON store.

4. **Raw URL spam.** Use `[Link](url)` labels so chat output stays clean.

5. **Overly narrow display categories.** Store detailed categories if useful, but display broad categories for scanning.

6. **Renumbering JSON IDs.** Never rewrite stable IDs when items become read. Only display numbers should change.

## Verification Checklist

- [ ] JSON file exists for the channel/context or is created on first add
- [ ] Every item has a stable integer `id`
- [ ] Report includes only unread items
- [ ] Display numbers are sequential from 1 to N
- [ ] Mark-read maps display numbers back to stable IDs
- [ ] Each item shows an added/registration date when available
- [ ] Categories are broad and rendered as code labels
- [ ] Titles are bold and links use `[Link](url)` labels
- [ ] No item is marked read unless explicitly requested
