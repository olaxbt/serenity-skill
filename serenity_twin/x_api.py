"""X API v2 and optional syndication fetch helpers."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape

from serenity_twin.config import Settings
from serenity_twin.schema import to_canonical
from serenity_twin.tickers import extract_tickers
from serenity_twin.tweet_parse import tweet_kind

X_API = "https://api.x.com/2"
SYNDICATION_URL = "https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"


def _request(url: str, token: str | None = None, timeout: int = 30) -> dict | str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; serenity-twin/0.1)"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw


def fetch_from_x_api(settings: Settings, include_replies: bool, lookback_hours: int, max_tweets: int) -> dict:
    handle = settings.handle
    token = settings.x_bearer_token
    if not token:
        return {"status": "disabled", "message": settings.sync_status_message(), "tweets": []}

    user_payload = _request(
        f"{X_API}/users/by/username/{urllib.parse.quote(handle)}?user.fields=description,public_metrics",
        token,
    )
    if not isinstance(user_payload, dict):
        raise RuntimeError("X user lookup invalid response")
    user = user_payload.get("data") or {}
    user_id = user.get("id")
    if not user_id:
        raise RuntimeError(f"X user lookup returned no user for @{handle}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    params = {
        "max_results": str(min(100, max(5, max_tweets * 3))),
        "tweet.fields": "created_at,public_metrics,referenced_tweets,note_tweet,entities,conversation_id",
        "exclude": "retweets" if include_replies else "retweets,replies",
        "start_time": cutoff.isoformat().replace("+00:00", "Z"),
    }
    url = f"{X_API}/users/{user_id}/tweets?{urllib.parse.urlencode(params)}"
    tweets_payload = _request(url, token)
    if not isinstance(tweets_payload, dict):
        raise RuntimeError("X tweets lookup invalid response")

    tweets = []
    for t in tweets_payload.get("data") or []:
        text = (t.get("note_tweet") or {}).get("text") or t.get("text") or ""
        refs = t.get("referenced_tweets") or []
        tweets.append(
            to_canonical(
                {
                    "id": str(t["id"]),
                    "text": text,
                    "created_at": t.get("created_at"),
                    "kind": tweet_kind({"referenced_tweets": refs}),
                    "tickers": extract_tickers(text),
                    "metrics": {
                        "likes": (t.get("public_metrics") or {}).get("like_count", 0),
                        "retweets": (t.get("public_metrics") or {}).get("retweet_count", 0),
                        "replies": (t.get("public_metrics") or {}).get("reply_count", 0),
                    },
                    "conversationId": t.get("conversation_id"),
                    "referenced_tweets": refs,
                },
                handle,
            )
        )
    return {
        "status": "ok",
        "source": "x-api",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tweets": tweets,
    }


def fetch_from_syndication(settings: Settings, max_tweets: int) -> dict:
    handle = settings.handle
    html = _request(SYNDICATION_URL.format(handle=urllib.parse.quote(handle)))
    if not isinstance(html, str):
        raise RuntimeError("Syndication fetch did not return HTML")
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">([\s\S]*?)</script>', html)
    if not match:
        raise RuntimeError("Syndication response missing timeline JSON")
    data = json.loads(match.group(1))
    entries = data.get("props", {}).get("pageProps", {}).get("timeline", {}).get("entries") or []
    tweets = []
    for entry in entries:
        if entry.get("type") != "tweet":
            continue
        t = entry.get("content", {}).get("tweet") or {}
        text = unescape(t.get("full_text") or t.get("text") or "")
        tid = str(t.get("id_str") or t.get("id") or "")
        if not tid:
            continue
        created = datetime.fromtimestamp(int(t.get("created_at_ts") or 0), tz=timezone.utc).isoformat() if t.get("created_at_ts") else None
        if not created and t.get("created_at"):
            try:
                from email.utils import parsedate_to_datetime
                created = parsedate_to_datetime(t["created_at"]).astimezone(timezone.utc).isoformat()
            except (TypeError, ValueError):
                created = str(t.get("created_at"))
        tweets.append(
            to_canonical(
                {
                    "id": tid,
                    "text": text,
                    "created_at": created,
                    "kind": "quote" if t.get("quoted_status_id_str") else "post",
                    "tickers": extract_tickers(text),
                    "metrics": {
                        "likes": t.get("favorite_count", 0),
                        "retweets": t.get("retweet_count", 0),
                        "replies": t.get("reply_count", 0),
                    },
                },
                handle,
            )
        )
        if len(tweets) >= max_tweets:
            break
    return {
        "status": "ok",
        "source": "x-syndication",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tweets": tweets,
        "warning": "Syndication fallback may miss newest posts or truncate long posts.",
    }


def fetch_recent(settings: Settings, include_replies: bool, lookback_hours: int, max_tweets: int) -> dict:
    if settings.x_bearer_token and settings.twitter_sync_enabled:
        try:
            return fetch_from_x_api(settings, include_replies, lookback_hours, max_tweets)
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, TimeoutError) as exc:
            if settings.allow_syndication_fallback:
                result = fetch_from_syndication(settings, max_tweets)
                result["x_api_error"] = str(exc)
                return result
            raise
    if settings.allow_syndication_fallback and settings.twitter_sync_enabled:
        return fetch_from_syndication(settings, max_tweets)
    return {"status": "disabled", "message": settings.sync_status_message(), "tweets": []}
