import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def run(competitor_id: str):
    # Fetch competitor
    response = (
        supabase.table("competitors")
        .select("*")
        .eq("id", competitor_id)
        .execute()
    )

    if not response.data:
        return {"error": "Competitor not found"}

    competitor = response.data[0]
    website_url = competitor["website_url"]

    # Fetch website
    r = requests.get(website_url)
    soup = BeautifulSoup(r.text, "html.parser")

    # -------------------------
    # Extract Campaigns
    # -------------------------
    campaigns = []
    campaign_cards = soup.find_all(class_="campaign-card")

    for card in campaign_cards:
        title = card.find(class_="campaign-title")
        platform = card.find(class_="campaign-platform")
        ad_type = card.find(class_="campaign-type")
        cta = card.find(class_="campaign-cta")

        campaigns.append({
            "title": title.get_text(strip=True) if title else None,
            "platform": platform.get_text(strip=True) if platform else None,
            "type": ad_type.get_text(strip=True) if ad_type else None,
            "cta": cta.get_text(strip=True) if cta else None
        })

    # -------------------------
    # Extract Social Posts
    # -------------------------
    social_posts = []
    posts = soup.find_all(class_="social-post")

    for post in posts:
        text = post.find(class_="post-text")
        platform = post.find(class_="post-platform")
        likes = post.find(class_="post-likes")
        comments = post.find(class_="post-comments")

        social_posts.append({
            "text": text.get_text(strip=True) if text else None,
            "platform": platform.get_text(strip=True) if platform else None,
            "likes": likes.get_text(strip=True) if likes else None,
            "comments": comments.get_text(strip=True) if comments else None
        })

    # -------------------------
    # Extract Products
    # -------------------------
    products = []
    product_cards = soup.find_all(class_="product-card")

    for product in product_cards:
        name = product.find(class_="product-name")
        old_price = product.find(class_="old-price")
        new_price = product.find(class_="new-price")
        label = product.find(class_="discount-label")

        products.append({
            "name": name.get_text(strip=True) if name else None,
            "old_price": old_price.get_text(strip=True) if old_price else None,
            "new_price": new_price.get_text(strip=True) if new_price else None,
            "label": label.get_text(strip=True) if label else None
        })

    # -------------------------
    # Extract Launch
    # -------------------------
    launch_item = soup.find(class_="launch-item")

    launch = {}
    if launch_item:
        title = launch_item.find(class_="launch-title")
        date = launch_item.find(class_="launch-date")
        tag = launch_item.find(class_="launch-tag")

        launch = {
            "title": title.get_text(strip=True) if title else None,
            "launch_date": date.get_text(strip=True) if date else None,
            "tag": tag.get_text(strip=True) if tag else None
        }

    return {
        "competitor_name": competitor["name"],
        "website_url": website_url,
        "campaigns": campaigns,
        "social_posts": social_posts,
        "products": products,
        "launch": launch
    }