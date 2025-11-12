import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Database helpers
from database import db, create_document, get_documents

app = FastAPI(title="Caption Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Caption Generator Backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# --------- Caption Generator Logic ---------
TONE_STYLES: Dict[str, Dict[str, Any]] = {
    "friendly": {
        "prefixes": ["Hey there!", "Fun fact:", "Guess what?", "PSA:"],
        "emojis": ["😊", "✨", "🎉", "🚀", "🙌"],
    },
    "professional": {
        "prefixes": ["Pro tip:", "Insight:", "Quick update:", "Heads up:"],
        "emojis": ["💼", "📈", "🧠", "✅"],
    },
    "witty": {
        "prefixes": ["Plot twist:", "Hot take:", "Low-key obsessed with:", "Unpopular opinion:"],
        "emojis": ["😏", "🔥", "🧩", "😉"],
    },
    "bold": {
        "prefixes": ["Say it louder:", "No fluff:", "Real talk:", "Let’s be honest:"],
        "emojis": ["⚡", "🔥", "💥", "🏆"],
    },
    "luxury": {
        "prefixes": ["Elevate:", "Curated:", "Crafted:", "Exquisite:"],
        "emojis": ["✨", "💫", "💎", "🖤"],
    },
    "educational": {
        "prefixes": ["Here’s the breakdown:", "Step-by-step:", "3 things to know:", "Learn this:"],
        "emojis": ["📚", "📝", "💡", "🔍"],
    },
    "casual": {
        "prefixes": ["Okay but listen:", "So...", "Not me doing:", "Mood:"],
        "emojis": ["😌", "🤙", "👌", "✨"],
    },
}

PLATFORM_HASHTAGS: Dict[str, List[str]] = {
    "instagram": ["#instadaily", "#trending", "#reels", "#explore", "#viral"],
    "tiktok": ["#fyp", "#foryou", "#tiktok", "#viral", "#trend"],
    "twitter": ["#NowPlaying", "#ICYMI", "#Thread", "#Vibes"],
    "linkedin": ["#leadership", "#growth", "#careers", "#marketing", "#business"],
    "youtube": ["#Shorts", "#Creator", "#HowTo", "#BehindTheScenes"],
}

GENERIC_HASHTAGS = ["#life", "#creative", "#goals", "#inspo", "#community", "#content"]


def suggest_hashtags(topic: str, platform: str, include_hashtags: bool, length: str) -> str:
    if not include_hashtags:
        return ""
    topic_tags = [f"#{w.lower()}" for w in topic.split() if w.isalpha()][:3]
    base = PLATFORM_HASHTAGS.get(platform, [])[:3]
    generic = GENERIC_HASHTAGS[:3 if length == "short" else 5]
    all_tags = topic_tags + base + generic
    # Unique and limit
    seen = set()
    unique = []
    for t in all_tags:
        if t not in seen:
            unique.append(t)
            seen.add(t)
        if len(unique) >= (4 if length == "short" else 7 if length == "medium" else 10):
            break
    return " ".join(unique)


def choose(arr: List[str]) -> str:
    import random
    return random.choice(arr) if arr else ""


def build_caption(topic: str, tone: str, platform: str, length: str, include_emojis: bool, include_hashtags: bool) -> str:
    tone_conf = TONE_STYLES.get(tone, TONE_STYLES["friendly"]) 
    prefix = choose(tone_conf["prefixes"]) if tone_conf else ""
    emojis = tone_conf.get("emojis", []) if include_emojis else []

    # Length control
    if length == "short":
        core = f"{topic} — let’s go!"
    elif length == "long":
        core = f"{topic}. Here’s why it matters and how you can make it work today. Save this for later!"
    else:
        core = f"{topic} done right. Screenshot this if you needed the nudge."

    emoji_str = f" {' '.join(emojis[:2])}" if emojis else ""
    ht = suggest_hashtags(topic, platform, include_hashtags, length)
    ht_str = f"\n\n{ht}" if ht else ""
    caption = f"{prefix} {core}{emoji_str}{ht_str}".strip()
    return caption


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    tone: str = Field("friendly")
    platform: str = Field("instagram")
    length: str = Field("medium")
    include_emojis: bool = True
    include_hashtags: bool = True
    variants: int = Field(3, ge=1, le=10)


class GenerateResponse(BaseModel):
    variants: List[str]
    saved_id: Optional[str] = None


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_captions(payload: GenerateRequest):
    try:
        topic = payload.topic.strip()
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")

        variants: List[str] = []
        for _ in range(payload.variants):
            cap = build_caption(
                topic=topic,
                tone=payload.tone.lower(),
                platform=payload.platform.lower(),
                length=payload.length.lower(),
                include_emojis=payload.include_emojis,
                include_hashtags=payload.include_hashtags,
            )
            variants.append(cap)

        # Save a record of this generation in DB
        try:
            doc = {
                "topic": topic,
                "tone": payload.tone,
                "platform": payload.platform,
                "length": payload.length,
                "include_emojis": payload.include_emojis,
                "include_hashtags": payload.include_hashtags,
                "variants": variants,
                "favorite": False,
                "generated_at": datetime.utcnow(),
            }
            saved_id = create_document("caption", doc)
        except Exception:
            saved_id = None

        return {"variants": variants, "saved_id": saved_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FavoriteRequest(BaseModel):
    id: str
    index: int = 0


@app.get("/api/captions")
async def list_captions(limit: int = 20):
    try:
        items = get_documents("caption", {}, limit)
        # Convert ObjectId to string if present
        for it in items:
            if "_id" in it:
                it["_id"] = str(it["_id"])
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/captions/{doc_id}/favorite")
async def favorite_caption(doc_id: str, index: int = 0):
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        from bson import ObjectId
        db["caption"].update_one({"_id": ObjectId(doc_id)}, {"$set": {"favorite": True, "favorite_index": index, "updated_at": datetime.utcnow()}})
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
