"""Parse Heroku JSON (builds or releases) to find one matching a commit hash.

Reads /tmp/sdlc_builds.json and /tmp/sdlc_commit.txt.
Prints id|status if found, nothing if not.

Works with both:
- /apps/{app}/releases (has 'description' like 'Deploy abc123')
- /apps/{app}/builds (has 'source_blob.version')
"""
import json
import sys

try:
    with open("/tmp/sdlc_builds.json") as f:
        data = json.load(f)
    with open("/tmp/sdlc_commit.txt") as f:
        commit = f.read().strip()

    if not commit:
        sys.exit(0)

    # Sort by created_at descending
    data.sort(key=lambda b: b.get("created_at", ""), reverse=True)

    for item in data[:20]:
        # Check builds format: source_blob.version
        ver = (item.get("source_blob") or {}).get("version", "")
        if ver.startswith(commit):
            print(f"{item['id']}|{item['status']}")
            sys.exit(0)

        # Check releases format: description = "Deploy abc123..."
        desc = item.get("description", "")
        if desc.startswith("Deploy ") and desc[7:].startswith(commit):
            status = item.get("status", "unknown")
            print(f"{item.get('id', '')}|{status}")
            sys.exit(0)
except Exception:
    pass
