# link-bookmark

A portable Hermes Agent skill for keeping an unread link bookmark from Slack, Discord, Telegram, or any chat channel.

It stores links in a small JSON file, renders a clean unread digest, and marks items read only when the user explicitly asks.

## What it does

- Collects links into a channel-specific JSON file
- Shows only unread links
- Groups links by broad category
- Re-numbers unread items from `1..N` every time
- Keeps stable internal JSON IDs so read state is safe
- Supports Korean `책갈피` and English bookmark workflows
- Requires no Slack/Discord history API

Example output:

```md
:bookmark_tabs: *Unread Link Bookmark*

`AI`

**1. Example AI Tool**  
Added: 2026-06-16  
A concise summary of the link.  
[Link](https://example.com)
```

Korean output:

```md
:bookmark_tabs: *읽지 않은 책갈피*

`AI`

**1. Example AI Tool**  
등록일: 2026-06-16  
A concise summary of the link.  
[Link](https://example.com)
```

## Install

### Option A — clone directly into Hermes skills

```bash
mkdir -p ~/.hermes/skills/productivity
git clone https://github.com/PeterCha90/link-bookmark.git ~/.hermes/skills/productivity/link-bookmark
```

Restart Hermes or start a new Hermes session so the skill loader sees the new skill.

### Option B — download ZIP

```bash
mkdir -p ~/.hermes/skills/productivity/link-bookmark
curl -L https://github.com/PeterCha90/link-bookmark/archive/refs/heads/main.zip -o /tmp/link-bookmark.zip
python3 - <<'PY'
import zipfile
from pathlib import Path
src = Path('/tmp/link-bookmark.zip')
dst = Path.home() / '.hermes' / 'skills' / 'productivity' / 'link-bookmark'
dst.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(src) as z:
    prefix = 'link-bookmark-main/'
    for item in z.infolist():
        if item.is_dir():
            continue
        rel = item.filename.removeprefix(prefix)
        if not rel or rel.startswith('.git'):
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(z.read(item))
PY
```

Restart Hermes or start a new Hermes session.

## Verify installation

In Hermes, ask:

```text
What skills are available for bookmarks?
```

Or from a terminal, check that the skill file exists:

```bash
test -f ~/.hermes/skills/productivity/link-bookmark/SKILL.md && echo "installed"
```

## Set up your first bookmark JSON

Create a channel/context JSON file. The filename can be a Slack channel ID, Discord channel ID, project name, or any stable context key.

```bash
mkdir -p ~/.hermes/link_bookmarks
cp ~/.hermes/skills/productivity/link-bookmark/templates/link_bookmark.example.json ~/.hermes/link_bookmarks/my-channel.json
```

Edit the file:

```bash
python3 -m json.tool ~/.hermes/link_bookmarks/my-channel.json >/tmp/link-bookmark-check.json
```

For Slack, a practical filename is the Slack channel ID:

```text
~/.hermes/link_bookmarks/C0123456789.json
```

## Ask Hermes to use it

Examples:

```text
Show my bookmarks for this channel.
```

```text
책갈피 보여줘
```

```text
Add this link to the bookmark: https://example.com
```

```text
Mark 1 and 3 as read.
```

```text
1번 읽음 처리해줘
```

Hermes should treat displayed numbers as the current unread list positions. It should not treat them as stable JSON IDs unless you explicitly say `by id`.

## Helper script usage

The included script is optional but useful for deterministic operations.

Show unread links:

```bash
python ~/.hermes/skills/productivity/link-bookmark/scripts/link_bookmark.py show ~/.hermes/link_bookmarks/my-channel.json
```

Show Korean output:

```bash
python ~/.hermes/skills/productivity/link-bookmark/scripts/link_bookmark.py show ~/.hermes/link_bookmarks/my-channel.json --locale ko
```

Add a link:

```bash
python ~/.hermes/skills/productivity/link-bookmark/scripts/link_bookmark.py add ~/.hermes/link_bookmarks/my-channel.json \
  --title "Example AI Tool" \
  --url "https://example.com" \
  --category "AI·Tools" \
  --summary "A concise summary of the link."
```

Mark displayed items read:

```bash
python ~/.hermes/skills/productivity/link-bookmark/scripts/link_bookmark.py mark-read ~/.hermes/link_bookmarks/my-channel.json 1 3
```

Mark stable JSON IDs read explicitly:

```bash
python ~/.hermes/skills/productivity/link-bookmark/scripts/link_bookmark.py mark-read ~/.hermes/link_bookmarks/my-channel.json --by-id 42
```

## JSON format

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
      "key_points": ["First point", "Second point"]
    }
  ],
  "read_items": [],
  "updated_at": "2026-06-16T09:00:00+09:00",
  "notes": "Optional notes."
}
```

## Migrating from `link-report`

If you previously used `~/.hermes/link_reports/<channel-id>.json`, copy it into the new default location:

```bash
mkdir -p ~/.hermes/link_bookmarks
cp ~/.hermes/link_reports/<channel-id>.json ~/.hermes/link_bookmarks/<channel-id>.json
```

The schema is compatible.

## Important behavior

- Showing a bookmark does **not** mark items read.
- Read marking happens only after explicit user instruction.
- Display numbers are temporary and change after items are read.
- Stable JSON IDs must never be renumbered.
- The skill does not magically read historical Slack/Discord messages unless your Hermes gateway exposes them. It works best with messages delivered to Hermes or links explicitly given to Hermes.

## Repository layout

```text
SKILL.md
README.md
README.en.md
LICENSE
templates/link_bookmark.example.json
scripts/link_bookmark.py
```

## License

MIT
