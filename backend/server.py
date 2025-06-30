from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    xp: int = 0
    total_polls_created: int = 0
    total_votes_cast: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    xp: int
    total_polls_created: int
    total_votes_cast: int
    created_at: datetime

class PollOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    votes: int = 0
    voter_ids: List[str] = []

class Poll(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    options: List[PollOption]
    creator_id: str
    creator_username: str
    total_votes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    is_active: bool = True

class PollCreate(BaseModel):
    title: str
    description: str
    options: List[str]
    tags: List[str] = []

class VoteRequest(BaseModel):
    poll_id: str
    option_id: str
    user_id: str

class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    badge_icon: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    xp_bonus: int = 0

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

async def get_user_by_email(email: str):
    user_data = await db.users.find_one({"email": email})
    return User(**user_data) if user_data else None

async def get_user_by_id(user_id: str):
    user_data = await db.users.find_one({"id": user_id})
    return User(**user_data) if user_data else None

async def calculate_poll_bonus_xp(poll_id: str) -> int:
    """Calculate bonus XP based on poll popularity"""
    poll_data = await db.polls.find_one({"id": poll_id})
    if not poll_data:
        return 0
    
    total_votes = poll_data.get("total_votes", 0)
    if total_votes >= 100:
        return 100
    elif total_votes >= 50:
        return 50
    elif total_votes >= 25:
        return 25
    elif total_votes >= 10:
        return 10
    return 0

async def award_achievement(user_id: str, achievement_type: str):
    """Award achievement to user"""
    user = await get_user_by_id(user_id)
    if not user:
        return
    
    achievements = {
        "first_poll": {"title": "First Poll Creator", "description": "Created your first poll!", "badge_icon": "🎯", "xp_bonus": 10},
        "vote_master": {"title": "Vote Master", "description": "Cast 10 votes!", "badge_icon": "🗳️", "xp_bonus": 20},
        "popular_creator": {"title": "Popular Creator", "description": "Poll reached 50 votes!", "badge_icon": "🔥", "xp_bonus": 50},
        "viral_creator": {"title": "Viral Creator", "description": "Poll reached 100 votes!", "badge_icon": "🚀", "xp_bonus": 100},
        "prolific_creator": {"title": "Prolific Creator", "description": "Created 10 polls!", "badge_icon": "📊", "xp_bonus": 75}
    }
    
    if achievement_type in achievements:
        # Check if user already has this achievement
        existing = await db.achievements.find_one({"user_id": user_id, "title": achievements[achievement_type]["title"]})
        if not existing:
            achievement_data = achievements[achievement_type]
            achievement = Achievement(
                user_id=user_id,
                title=achievement_data["title"],
                description=achievement_data["description"],
                badge_icon=achievement_data["badge_icon"],
                xp_bonus=achievement_data["xp_bonus"]
            )
            await db.achievements.insert_one(achievement.dict())
            
            # Award bonus XP
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"xp": achievement_data["xp_bonus"]}}
            )

# API Routes
@api_router.post("/register", response_model=UserProfile)
async def register_user(user_data: UserCreate):
    # Check if user exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    
    await db.users.insert_one(user.dict())
    
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        xp=user.xp,
        total_polls_created=user.total_polls_created,
        total_votes_cast=user.total_votes_cast,
        created_at=user.created_at
    )

@api_router.post("/login", response_model=UserProfile)
async def login_user(login_data: UserLogin):
    user = await get_user_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last activity
    await db.users.update_one(
        {"id": user.id},
        {"$set": {"last_activity": datetime.utcnow()}}
    )
    
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        xp=user.xp,
        total_polls_created=user.total_polls_created,
        total_votes_cast=user.total_votes_cast,
        created_at=user.created_at
    )

@api_router.post("/polls", response_model=Poll)
async def create_poll(poll_data: PollCreate, user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create poll options
    options = [PollOption(text=option_text) for option_text in poll_data.options]
    
    poll = Poll(
        title=poll_data.title,
        description=poll_data.description,
        options=options,
        creator_id=user.id,
        creator_username=user.username,
        tags=poll_data.tags
    )
    
    await db.polls.insert_one(poll.dict())
    
    # Award XP for creating poll (20 XP)
    await db.users.update_one(
        {"id": user.id},
        {"$inc": {"xp": 20, "total_polls_created": 1}}
    )
    
    # Check for achievements
    updated_user = await get_user_by_id(user.id)
    if updated_user.total_polls_created == 1:
        await award_achievement(user.id, "first_poll")
    elif updated_user.total_polls_created == 10:
        await award_achievement(user.id, "prolific_creator")
    
    return poll

@api_router.get("/polls", response_model=List[Poll])
async def get_polls(limit: int = 20, skip: int = 0):
    polls_data = await db.polls.find({"is_active": True}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [Poll(**poll) for poll in polls_data]

@api_router.get("/polls/{poll_id}", response_model=Poll)
async def get_poll(poll_id: str):
    poll_data = await db.polls.find_one({"id": poll_id})
    if not poll_data:
        raise HTTPException(status_code=404, detail="Poll not found")
    return Poll(**poll_data)

@api_router.post("/vote")
async def vote_on_poll(vote_data: VoteRequest):
    # Get poll
    poll_data = await db.polls.find_one({"id": vote_data.poll_id})
    if not poll_data:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    poll = Poll(**poll_data)
    
    # Check if user already voted
    user_already_voted = False
    for option in poll.options:
        if vote_data.user_id in option.voter_ids:
            user_already_voted = True
            break
    
    if user_already_voted:
        raise HTTPException(status_code=400, detail="User has already voted on this poll")
    
    # Find the option to vote for
    option_found = False
    for option in poll.options:
        if option.id == vote_data.option_id:
            option.votes += 1
            option.voter_ids.append(vote_data.user_id)
            option_found = True
            break
    
    if not option_found:
        raise HTTPException(status_code=404, detail="Option not found")
    
    # Update total votes
    poll.total_votes += 1
    
    # Update poll in database
    await db.polls.update_one(
        {"id": vote_data.poll_id},
        {"$set": poll.dict()}
    )
    
    # Award XP for voting (5 XP)
    await db.users.update_one(
        {"id": vote_data.user_id},
        {"$inc": {"xp": 5, "total_votes_cast": 1}}
    )
    
    # Check achievements for voter
    updated_user = await get_user_by_id(vote_data.user_id)
    if updated_user.total_votes_cast == 10:
        await award_achievement(vote_data.user_id, "vote_master")
    
    # Check for poll creator achievements based on vote milestones
    if poll.total_votes == 50:
        await award_achievement(poll.creator_id, "popular_creator")
    elif poll.total_votes == 100:
        await award_achievement(poll.creator_id, "viral_creator")
        # Award bonus XP to poll creator
        bonus_xp = await calculate_poll_bonus_xp(vote_data.poll_id)
        await db.users.update_one(
            {"id": poll.creator_id},
            {"$inc": {"xp": bonus_xp}}
        )
    
    return {"message": "Vote recorded successfully", "total_votes": poll.total_votes}

@api_router.get("/leaderboard", response_model=List[UserProfile])
async def get_leaderboard(limit: int = 10):
    users_data = await db.users.find().sort("xp", -1).limit(limit).to_list(limit)
    return [UserProfile(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        xp=user["xp"],
        total_polls_created=user["total_polls_created"],
        total_votes_cast=user["total_votes_cast"],
        created_at=user["created_at"]
    ) for user in users_data]

@api_router.get("/users/{user_id}/achievements", response_model=List[Achievement])
async def get_user_achievements(user_id: str):
    achievements_data = await db.achievements.find({"user_id": user_id}).sort("earned_at", -1).to_list(100)
    return [Achievement(**achievement) for achievement in achievements_data]

@api_router.get("/users/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        xp=user.xp,
        total_polls_created=user.total_polls_created,
        total_votes_cast=user.total_votes_cast,
        created_at=user.created_at
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()