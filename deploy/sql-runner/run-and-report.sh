#!/usr/bin/env bash
set -euo pipefail
DIRECTORY=/home/davsean/Documents/git/omicidx-etl

cd $DIRECTORY

REPO="omicidx/omicidx-etl"
WORKFLOW="sql_runner_status.yaml"

start_time=$(date +%s)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Run the SQL job
exit_code=0
uv run oidx sql run || exit_code=$?

end_time=$(date +%s)
duration=$(( end_time - start_time ))

# Determine status
if [ "$exit_code" -eq 0 ]; then
    status="success"
else
    status="failure"
fi

# Report status to GitHub Actions
gh workflow run "$WORKFLOW" \
    --repo "$REPO" \
    -f status="$status" \
    -f duration="${duration}s" \
    -f timestamp="$timestamp" \
    -f details="Exit code: $exit_code" \
    || echo "Warning: failed to report status to GitHub Actions"

exit "$exit_code"
