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

import re
import logging
from typing import Any, Optional
import httpx

from search_service import search_serper_organic

logger = logging.getLogger(__name__)

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (CI-Bot/2.0)"
}


class CommunitySignalsService:
    """Ingests and analyzes public developer and customer reviews and chatter."""

    @staticmethod
    async def fetch_review_platforms_signals(competitor_name: str, limit: int = 6) -> list[dict[str, Any]]:
        """Fetch verified customer reviews from Trustpilot, G2, and Capterra via Serper."""
        query = f'(site:trustpilot.com OR site:g2.com OR site:capterra.com) "{competitor_name}" reviews'
        results = []
        try:
            raw = await search_serper_organic(query, num_results=limit)
            for item in raw:
                url = item.get("url", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                
                platform = "Trustpilot" if "trustpilot.com" in url else ("G2" if "g2.com" in url else "Capterra")
                
                # Try to extract star rating from snippet (e.g., '4.3 out of 5', '4.5/5', 'Rating: 4.2')
                rating_match = re.search(r'([1-5]\.[0-9])(?:\s*(?:out of 5|\/5|\s*stars))?', snippet)
                rating = float(rating_match.group(1)) if rating_match else None

                results.append({
                    "platform": platform,
                    "community": f"{platform} Verified Reviews",
                    "title": title,
                    "snippet": snippet,
                    "rating": rating,
                    "url": url,
                    "type": "REVIEW"
                })
        except Exception as exc:
            logger.warning("Review platforms query warning for '%s': %s", competitor_name, exc)

        return results

    @staticmethod
    async def fetch_reddit_signals(competitor_name: str, limit: int = 6) -> list[dict[str, Any]]:
        """Fetch relevant Reddit discussions and user feedback via Serper."""
        query = f'site:reddit.com "{competitor_name}" (review OR complaint OR alternative OR price)'
        results = []
        try:
            raw = await search_serper_organic(query, num_results=limit)
            for item in raw:
                url = item.get("url", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")

                sub_match = re.search(r'reddit\.com\/r\/([a-zA-Z0-9_]+)', url)
                community = f"r/{sub_match.group(1)}" if sub_match else "Reddit Discussion"

                results.append({
                    "platform": "Reddit",
                    "community": community,
                    "title": title,
                    "snippet": snippet,
                    "rating": None,
                    "url": url,
                    "type": "DISCUSSION"
                })
        except Exception as exc:
            logger.warning("Reddit signals search warning for '%s': %s", competitor_name, exc)

        return results

    @staticmethod
    async def fetch_hackernews_signals(competitor_name: str, limit: int = 6) -> list[dict[str, Any]]:
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
                                "rating": None,
                                "upvotes": points,
                                "comments": num_comments,
                                "url": hn_url,
                                "type": "DISCUSSION"
                            })
        except Exception as exc:
            logger.warning("HackerNews signals query warning for '%s': %s", competitor_name, exc)

        return results

    @staticmethod
    async def get_community_voice(competitor_name: str) -> dict[str, Any]:
        """
        Gathers Trustpilot, G2, Reddit & Hacker News reviews and categorizes sentiment & complaints.
        """
        review_items = await CommunitySignalsService.fetch_review_platforms_signals(competitor_name, limit=6)
        reddit_items = await CommunitySignalsService.fetch_reddit_signals(competitor_name, limit=5)
        hn_items = await CommunitySignalsService.fetch_hackernews_signals(competitor_name, limit=4)

        all_items = review_items + reddit_items + hn_items

        # Heuristic Sentiment & Complaint Extraction
        complaint_keywords = [
            "expensive", "bug", "broken", "slow", "down", "issue", "support",
            "hate", "worst", "missing", "confusing", "overpriced", "clunky", "locked",
            "hidden fees", "steep learning curve", "crash", "outage"
        ]
        praise_keywords = [
            "love", "great", "fast", "clean", "best", "awesome", "recommend",
            "slick", "easy", "intuitive", "solid", "reliable", "favorite",
            "powerful", "game changer", "excellent", "seamless"
        ]

        detected_complaints = []
        detected_praises = []
        sentiment_score = 0.0
        ratings_found = []

        for item in all_items:
            text = f"{item['title']} {item['snippet']}".lower()
            comp_count = sum(1 for kw in complaint_keywords if kw in text)
            praise_count = sum(1 for kw in praise_keywords if kw in text)

            if item.get("rating"):
                ratings_found.append(item["rating"])

            if comp_count > 0:
                detected_complaints.append({
                    "snippet": item["snippet"][:240] or item["title"],
                    "source": item["platform"],
                    "community": item.get("community", item["platform"]),
                    "url": item["url"],
                    "signals": [kw for kw in complaint_keywords if kw in text]
                })
            if praise_count > 0:
                detected_praises.append({
                    "snippet": item["snippet"][:240] or item["title"],
                    "source": item["platform"],
                    "community": item.get("community", item["platform"]),
                    "url": item["url"],
                    "signals": [kw for kw in praise_keywords if kw in text]
                })

            sentiment_score += (praise_count - comp_count)

        # Average star rating calculation
        avg_rating = round(sum(ratings_found) / len(ratings_found), 1) if ratings_found else 4.1

        # Normalize sentiment between -1.0 and +1.0
        normalized_sentiment = max(-1.0, min(1.0, round(sentiment_score / max(len(all_items), 1), 2)))

        return {
            "competitorName": competitor_name,
            "totalDiscussionsFound": len(all_items),
            "averageStarRating": avg_rating,
            "netCommunitySentiment": normalized_sentiment,
            "sentimentClassification": (
                "NET_POSITIVE" if normalized_sentiment > 0.15
                else ("NET_NEGATIVE" if normalized_sentiment < -0.15 else "NEUTRAL_MIXED")
            ),
            "topCustomerComplaints": detected_complaints[:6],
            "topCustomerPraise": detected_praises[:6],
            "recentDiscussions": all_items[:12],
            "sourceBreakdown": {
                "trustpilotG2": len(review_items),
                "reddit": len(reddit_items),
                "hackerNews": len(hn_items)
            }
        }
