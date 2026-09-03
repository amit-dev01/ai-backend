"""
Community Signals & Customer Voice Ingestion Service.

Pulls unfiltered discussions, complaints, and reviews from public community platforms:
  1. Reddit API (public search JSON across /r/saas, /r/startups, /r/technology)
  2. Hacker News Algolia Search API (public developer discussions and launch comments)

Extracts:
  - Top community praise & strengths
  - Top customer complaints & churn triggers (weaknesses to exploit in sales battlecards)
  - Net Community Sentiment Score (-1.0 to +1.0)
"""

import logging
from typing import Any, Optional
import httpx

logger = logging.getLogger(__name__)

REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (CI-Bot/2.0)"
}


class CommunitySignalsService:
    """Ingests and analyzes public developer and customer chatter."""

    @staticmethod
    async def fetch_reddit_signals(competitor_name: str, limit: int = 8) -> list[dict[str, Any]]:
        """Fetch relevant Reddit discussions and user sentiment."""
        query = f'"{competitor_name}"'
        params = {
            "q": query,
            "sort": "relevance",
            "t": "year",
            "limit": limit
        }
        results = []
        try:
            async with httpx.AsyncClient(timeout=12, headers=REQUEST_HEADERS) as client:
                resp = await client.get(REDDIT_SEARCH_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post = child.get("data", {})
                        title = post.get("title", "")
                        selftext = post.get("selftext", "")[:400]
                        subreddit = post.get("subreddit", "")
                        score = post.get("score", 0)
                        num_comments = post.get("num_comments", 0)
                        permalink = f"https://reddit.com{post.get('permalink', '')}"

                        if competitor_name.lower() in title.lower() or competitor_name.lower() in selftext.lower():
                            results.append({
                                "platform": "Reddit",
                                "community": f"r/{subreddit}",
                                "title": title,
                                "snippet": selftext or title,
                                "upvotes": score,
                                "comments": num_comments,
                                "url": permalink
                            })
        except Exception as exc:
            logger.warning("Reddit signals query warning for '%s': %s", competitor_name, exc)

        return results

    @staticmethod
    async def fetch_hackernews_signals(competitor_name: str, limit: int = 8) -> list[dict[str, Any]]:
        """Fetch Hacker News stories and launch discussions."""
        params = {
            "query": competitor_name,
            "tags": "story",
            "hitsPerPage": limit
        }
        results = []
        try:
            async with httpx.AsyncClient(timeout=12, headers=REQUEST_HEADERS) as client:
                resp = await client.get(HN_SEARCH_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", [])
                    for hit in hits:
                        title = hit.get("title", "")
                        story_text = (hit.get("story_text") or "")[:400]
                        points = hit.get("points") or 0
                        num_comments = hit.get("num_comments") or 0
                        object_id = hit.get("objectID")
                        hn_url = f"https://news.ycombinator.com/item?id={object_id}"

                        if competitor_name.lower() in title.lower():
                            results.append({
                                "platform": "HackerNews",
                                "community": "Y Combinator HN",
                                "title": title,
                                "snippet": story_text or title,
                                "upvotes": points,
                                "comments": num_comments,
                                "url": hn_url
                            })
        except Exception as exc:
            logger.warning("HackerNews signals query warning for '%s': %s", competitor_name, exc)

        return results

    @staticmethod
    async def get_community_voice(competitor_name: str) -> dict[str, Any]:
        """
        Gathers Reddit & Hacker News discussions and categorizes sentiment & complaints.
        """
        reddit_items = await CommunitySignalsService.fetch_reddit_signals(competitor_name)
        hn_items = await CommunitySignalsService.fetch_hackernews_signals(competitor_name)

        all_items = reddit_items + hn_items

        # Heuristic Sentiment & Complaint Extraction
        complaint_keywords = [
            "expensive", "bug", "broken", "slow", "down", "issue", "support",
            "hate", "worst", "missing", "confusing", "overpriced", "clunky", "locked"
        ]
        praise_keywords = [
            "love", "great", "fast", "clean", "best", "awesome", "recommend",
            "slick", "easy", "intuitive", "solid", "reliable", "favorite"
        ]

        detected_complaints = []
        detected_praises = []
        sentiment_score = 0.0

        for item in all_items:
            text = f"{item['title']} {item['snippet']}".lower()
            comp_count = sum(1 for kw in complaint_keywords if kw in text)
            praise_count = sum(1 for kw in praise_keywords if kw in text)

            if comp_count > 0:
                detected_complaints.append({
                    "snippet": item["title"],
                    "source": item["platform"],
                    "url": item["url"],
                    "signals": [kw for kw in complaint_keywords if kw in text]
                })
            if praise_count > 0:
                detected_praises.append({
                    "snippet": item["title"],
                    "source": item["platform"],
                    "url": item["url"],
                    "signals": [kw for kw in praise_keywords if kw in text]
                })

            sentiment_score += (praise_count - comp_count)

        # Normalize sentiment between -1.0 and +1.0
        normalized_sentiment = max(-1.0, min(1.0, round(sentiment_score / max(len(all_items), 1), 2)))

        return {
            "competitorName": competitor_name,
            "totalDiscussionsFound": len(all_items),
            "netCommunitySentiment": normalized_sentiment,
            "sentimentClassification": (
                "NET_POSITIVE" if normalized_sentiment > 0.15
                else ("NET_NEGATIVE" if normalized_sentiment < -0.15 else "NEUTRAL_MIXED")
            ),
            "topCustomerComplaints": detected_complaints[:4],
            "topCustomerPraise": detected_praises[:4],
            "recentDiscussions": all_items[:6],
        }
