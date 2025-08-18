from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn
import logging
from datetime import datetime, timedelta
import os
import json

from database import DatabaseManager
from file_operations import FileManager
from ai_classifier import AIClassifier
from quest_engine import QuestEngine
from rewards_system import RewardsSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="OrganizeX Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_manager = DatabaseManager()
file_manager = FileManager()
ai_classifier = AIClassifier()
quest_engine = QuestEngine(db_manager)
rewards_system = RewardsSystem(db_manager)

# Pydantic models for request/response
class UserData(BaseModel):
    level: int = 1
    xp: int = 0
    totalXp: int = 0
    streak: int = 0
    badges: List[str] = []
    completedQuests: int = 0

class ScanRequest(BaseModel):
    path: str

class OrganizeRequest(BaseModel):
    path: str
    rules: Dict[str, bool]

class DeleteDuplicatesRequest(BaseModel):
    files: List[str]

class Activity(BaseModel):
    type: str
    description: str
    xp: int
    timestamp: str

@app.on_event("startup")
async def startup_event():
    """Initialize database and components on startup"""
    try:
        db_manager.init_database()
        quest_engine.initialize_quests()
        logger.info("Backend started successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "OrganizeX Backend is running", "version": "1.0.0"}

# User endpoints
@app.get("/api/user")
async def get_user_data():
    """Get current user data"""
    try:
        user_data = db_manager.get_user_data()
        return user_data
    except Exception as e:
        logger.error(f"Failed to get user data: {e}")
        return UserData().dict()

@app.put("/api/user")
async def update_user_data(user_data: UserData):
    """Update user data"""
    try:
        db_manager.update_user_data(user_data.dict())
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to update user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user data")

@app.get("/api/user/stats")
async def get_user_stats():
    """Get user statistics"""
    try:
        stats = db_manager.get_user_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        return {
            "filesOrganized": 0,
            "duplicatesRemoved": 0,
            "questsCompleted": 0
        }

# Quest endpoints
@app.get("/api/quests")
async def get_quests():
    """Get all quests categorized by type"""
    try:
        quests = quest_engine.get_all_quests()
        return quests
    except Exception as e:
        logger.error(f"Failed to get quests: {e}")
        return {"daily": [], "weekly": [], "achievements": []}

@app.get("/api/quests/today")
async def get_todays_quests():
    """Get today's active quests"""
    try:
        quests = quest_engine.get_todays_quests()
        return quests
    except Exception as e:
        logger.error(f"Failed to get today's quests: {e}")
        return []

@app.post("/api/quests/{quest_id}/complete")
async def complete_quest(quest_id: str, background_tasks: BackgroundTasks):
    """Complete a quest and award rewards"""
    try:
        result = quest_engine.complete_quest(quest_id)
        
        if result["success"]:
            # Update user stats in background
            background_tasks.add_task(
                db_manager.update_user_stats,
                questsCompleted=1
            )
            
            # Check for new badges/achievements
            new_rewards = rewards_system.check_rewards(result["xpGained"])
            result.update(new_rewards)
        
        return result
    except Exception as e:
        logger.error(f"Failed to complete quest {quest_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete quest")

# File organization endpoints
@app.post("/api/files/scan")
async def scan_folder(request: ScanRequest):
    """Scan a folder and return file analysis"""
    try:
        results = file_manager.scan_folder(request.path)
        
        # Enhance results with AI classification
        if results.get("success"):
            classified_files = ai_classifier.classify_files(results["files"])
            results["fileTypes"] = ai_classifier.get_file_type_distribution(classified_files)
        
        return results
    except Exception as e:
        logger.error(f"Failed to scan folder {request.path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan folder")

@app.post("/api/files/organize")
async def organize_files(request: OrganizeRequest, background_tasks: BackgroundTasks):
    """Organize files based on rules"""
    try:
        result = file_manager.organize_files(request.path, request.rules)
        
        if result.get("success"):
            # Update user stats in background
            background_tasks.add_task(
                db_manager.update_user_stats,
                filesOrganized=result.get("filesOrganized", 0)
            )
            
            # Award XP for organization
            xp_gained = result.get("filesOrganized", 0) * 5
            background_tasks.add_task(
                db_manager.award_xp,
                xp_gained
            )
        
        return result
    except Exception as e:
        logger.error(f"Failed to organize files in {request.path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to organize files")

@app.post("/api/files/quick-sort/{folder_type}")
async def quick_sort_folder(folder_type: str, background_tasks: BackgroundTasks):
    """Quick sort common folders"""
    try:
        result = file_manager.quick_sort_folder(folder_type)
        
        if result.get("success"):
            # Update user stats and award XP
            background_tasks.add_task(
                db_manager.update_user_stats,
                filesOrganized=result.get("filesOrganized", 0)
            )
            background_tasks.add_task(
                db_manager.award_xp,
                result.get("xpGained", 0)
            )
        
        return result
    except Exception as e:
        logger.error(f"Failed to quick sort {folder_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to quick sort folder")

# Duplicate detection endpoints
@app.post("/api/duplicates/scan")
async def scan_duplicates(request: ScanRequest):
    """Scan for duplicate files"""
    try:
        duplicates = file_manager.find_duplicates(request.path)
        return {"duplicates": duplicates, "success": True}
    except Exception as e:
        logger.error(f"Failed to scan duplicates in {request.path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan for duplicates")

@app.delete("/api/duplicates/delete")
async def delete_duplicate_files(request: DeleteDuplicatesRequest, background_tasks: BackgroundTasks):
    """Delete duplicate files"""
    try:
        result = file_manager.delete_files(request.files)
        
        if result.get("success"):
            # Update user stats
            background_tasks.add_task(
                db_manager.update_user_stats,
                duplicatesRemoved=len(request.files)
            )
            
            # Award XP for cleaning duplicates
            xp_gained = len(request.files) * 10
            background_tasks.add_task(
                db_manager.award_xp,
                xp_gained
            )
        
        return result
    except Exception as e:
        logger.error(f"Failed to delete duplicate files: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete files")

# Rewards endpoints
@app.get("/api/rewards/badges")
async def get_badges():
    """Get all available badges"""
    try:
        badges = rewards_system.get_all_badges()
        return badges
    except Exception as e:
        logger.error(f"Failed to get badges: {e}")
        return []

@app.get("/api/rewards/achievements")
async def get_achievements():
    """Get all achievements with progress"""
    try:
        achievements = rewards_system.get_achievements()
        return achievements
    except Exception as e:
        logger.error(f"Failed to get achievements: {e}")
        return []

# Activity endpoints
@app.get("/api/activity/recent")
async def get_recent_activity():
    """Get recent user activity"""
    try:
        activity = db_manager.get_recent_activity()
        return activity
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        return []

@app.post("/api/activity")
async def add_activity(activity: Activity):
    """Add new activity entry"""
    try:
        db_manager.add_activity(activity.dict())
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to add activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to add activity")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
