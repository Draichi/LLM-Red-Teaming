#!/bin/bash
# notify_telegram.sh "<text>" — direct Telegram send via bot API (no gateway,
# no cron). Reads TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from the repo .env.
set -a
source "$(dirname "$0")/../.env" 2>/dev/null || source "$(dirname "$0")/.env" 2>/dev/null
set +a
curl -s --max-time 20 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=$1" \
  -d disable_web_page_preview=true >/dev/null 2>&1
