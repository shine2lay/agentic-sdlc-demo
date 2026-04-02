"""Extract build log lines from Heroku build result JSON.

Reads /tmp/sdlc_build_result.json, prints the last N lines of the build log.
If the result has 'lines', uses those. If it has 'output_stream_url', prints that.
"""
import json
import sys

try:
    with open("/tmp/sdlc_build_result.json") as f:
        data = json.load(f)

    lines = data.get("lines", [])
    if lines:
        for line in lines[-25:]:
            print(line.get("line", "").rstrip())
    else:
        # No lines — might have output_stream_url
        url = data.get("output_stream_url", "")
        if url:
            print(f"Build log URL: {url}")
        else:
            print("No build log available")
except Exception as e:
    print(f"Error reading build log: {e}")
