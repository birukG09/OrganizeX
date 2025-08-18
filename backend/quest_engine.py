import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import random

from models import Quest, QuestType, QuestStatus, Difficulty
from database import DatabaseManager

logger = logging.getLogger(__name__)

class QuestEngine:
    """
    Quest engine for managing daily/weekly quests and achievements
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.quest_templates = self._initialize_quest_templates()
    
    def _initialize_quest_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quest templates for different categories"""
        return {
            "daily": [
                {
                    "title": "Clean Your Downloads",
                    "description": "Organize files in your Downloads folder",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.EASY,
                    "xp_reward": 50,
                    "icon": "fas fa-download",
                    "requirements": {"folder": "downloads", "min_files": 5}
                },
                {
                    "title": "Desktop Declutter",
                    "description": "Clear and organize your Desktop",
                    "type": QuestType.CLEAN,
                    "difficulty": Difficulty.EASY,
                    "xp_reward": 40,
                    "icon": "fas fa-desktop",
                    "requirements": {"folder": "desktop", "min_files": 3}
                },
                {
                    "title": "Duplicate Hunter",
                    "description": "Find and remove duplicate files",
                    "type": QuestType.DUPLICATE,
                    "difficulty": Difficulty.MEDIUM,
                    "xp_reward": 75,
                    "icon": "fas fa-search",
                    "requirements": {"min_duplicates": 3}
                },
                {
                    "title": "Photo Organizer",
                    "description": "Sort images into proper folders",
                    "type": QuestType.SORT,
                    "difficulty": Difficulty.EASY,
                    "xp_reward": 45,
                    "icon": "fas fa-image",
                    "requirements": {"file_type": "Images", "min_files": 10}
                },
                {
                    "title": "Document Sorter",
                    "description": "Organize scattered documents",
                    "type": QuestType.SORT,
                    "difficulty": Difficulty.MEDIUM,
                    "xp_reward": 60,
                    "icon": "fas fa-file-text",
                    "requirements": {"file_type": "Documents", "min_files": 5}
                },
                {
                    "title": "Music Library Cleanup",
                    "description": "Organize your audio files",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.MEDIUM,
                    "xp_reward": 55,
                    "icon": "fas fa-music",
                    "requirements": {"file_type": "Audio", "min_files": 8}
                },
                {
                    "title": "Video Collection Sort",
                    "description": "Organize video files properly",
                    "type": QuestType.SORT,
                    "difficulty": Difficulty.HARD,
                    "xp_reward": 80,
                    "icon": "fas fa-video",
                    "requirements": {"file_type": "Videos", "min_files": 5}
                },
                {
                    "title": "Archive Explorer",
                    "description": "Review and organize compressed files",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.MEDIUM,
                    "xp_reward": 65,
                    "icon": "fas fa-file-archive",
                    "requirements": {"file_type": "Archives", "min_files": 3}
                }
            ],
            "weekly": [
                {
                    "title": "Master Organizer",
                    "description": "Organize 100 files this week",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.HARD,
                    "xp_reward": 200,
                    "icon": "fas fa-crown",
                    "requirements": {"files_organized": 100},
                    "target": 100
                },
                {
                    "title": "Duplicate Destroyer",
                    "description": "Remove 25 duplicate files",
                    "type": QuestType.DUPLICATE,
                    "difficulty": Difficulty.HARD,
                    "xp_reward": 150,
                    "icon": "fas fa-trash",
                    "requirements": {"duplicates_removed": 25},
                    "target": 25
                },
                {
                    "title": "Space Saver",
                    "description": "Free up 1GB of storage space",
                    "type": QuestType.CLEAN,
                    "difficulty": Difficulty.HARD,
                    "xp_reward": 250,
                    "icon": "fas fa-hdd",
                    "requirements": {"space_freed": 1024 * 1024 * 1024},  # 1GB
                    "target": 1
                },
                {
                    "title": "Quest Completionist",
                    "description": "Complete 10 daily quests this week",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.MEDIUM,
                    "xp_reward": 180,
                    "icon": "fas fa-tasks",
                    "requirements": {"daily_quests": 10},
                    "target": 10
                },
                {
                    "title": "Folder Master",
                    "description": "Organize 5 different folders",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.MEDIUM,
                    "xp_reward": 160,
                    "icon": "fas fa-folder-open",
                    "requirements": {"folders_organized": 5},
                    "target": 5
                }
            ],
            "achievements": [
                {
                    "title": "First Steps",
                    "description": "Complete your first organization task",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.EASY,
                    "xp_reward": 100,
                    "icon": "fas fa-baby",
                    "requirements": {"first_organization": True}
                },
                {
                    "title": "Streak Keeper",
                    "description": "Maintain a 7-day organization streak",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.MEDIUM,
                    "xp_reward": 300,
                    "icon": "fas fa-fire",
                    "requirements": {"streak_days": 7}
                },
                {
                    "title": "File Management Expert",
                    "description": "Organize 1000 files total",
                    "type": QuestType.ORGANIZE,
                    "difficulty": Difficulty.HARD,
                    "xp_reward": 500,
                    "icon": "fas fa-graduation-cap",
                    "requirements": {"total_files_organized": 1000}
                },
                {
                    "title": "Duplicate Detective",
                    "description": "Remove 100 duplicate files",
                    "type": QuestType.DUPLICATE,
                    "difficulty": Difficulty.HARD,
                    "xp_reward": 400,
                    "icon": "fas fa-search-plus",
                    "requirements": {"total_duplicates_removed": 100}
                },
                {
                    "title": "Storage Optimizer",
                    "description": "Free up 10GB of storage space",
                    "type": QuestType.CLEAN,
                    "difficulty": Difficulty.HARD,
                    "xp_reward": 750,
                    "icon": "fas fa-chart-line",
                    "requirements": {"total_space_freed": 10 * 1024 * 1024 * 1024}  # 10GB
                }
            ]
        }
    
    def initialize_quests(self):
        """Initialize daily quests for today if none exist"""
        try:
            today = datetime.now().date()
            existing_quests = self.db.get_quests_by_category("daily")
            
            # Check if we have quests for today
            today_quests = [
                q for q in existing_quests 
                if q.get("deadline") and datetime.fromisoformat(q["deadline"]).date() == today
            ]
            
            if not today_quests:
                self._generate_daily_quests()
                logger.info("Generated new daily quests")
            
            # Generate weekly quests if it's Monday and none exist
            if datetime.now().weekday() == 0:  # Monday
                weekly_quests = self.db.get_quests_by_category("weekly")
                this_week_start = today - timedelta(days=today.weekday())
                
                current_week_quests = [
                    q for q in weekly_quests
                    if q.get("deadline") and 
                    datetime.fromisoformat(q["deadline"]).date() >= this_week_start
                ]
                
                if not current_week_quests:
                    self._generate_weekly_quests()
                    logger.info("Generated new weekly quests")
            
            # Initialize achievement quests if none exist
            achievement_quests = self.db.get_quests_by_category("achievements")
            if not achievement_quests:
                self._generate_achievement_quests()
                logger.info("Generated achievement quests")
                
        except Exception as e:
            logger.error(f"Failed to initialize quests: {e}")
    
    def _generate_daily_quests(self):
        """Generate 3-5 random daily quests"""
        try:
            daily_templates = self.quest_templates["daily"]
            selected_templates = random.sample(daily_templates, min(4, len(daily_templates)))
            
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59)
            
            for template in selected_templates:
                quest = Quest(
                    id=f"daily_{uuid.uuid4().hex[:8]}",
                    title=template["title"],
                    description=template["description"],
                    type=template["type"],
                    difficulty=template["difficulty"],
                    xp_reward=template["xp_reward"],
                    category="daily",
                    deadline=tomorrow_end,
                    icon=template["icon"],
                    requirements=template.get("requirements", {}),
                    target=template.get("target", 1)
                )
                
                self.db.save_quest(quest)
                
        except Exception as e:
            logger.error(f"Failed to generate daily quests: {e}")
    
    def _generate_weekly_quests(self):
        """Generate 2-3 weekly quests"""
        try:
            weekly_templates = self.quest_templates["weekly"]
            selected_templates = random.sample(weekly_templates, min(3, len(weekly_templates)))
            
            next_sunday = datetime.now() + timedelta(days=(6 - datetime.now().weekday()))
            next_sunday_end = next_sunday.replace(hour=23, minute=59, second=59)
            
            for template in selected_templates:
                quest = Quest(
                    id=f"weekly_{uuid.uuid4().hex[:8]}",
                    title=template["title"],
                    description=template["description"],
                    type=template["type"],
                    difficulty=template["difficulty"],
                    xp_reward=template["xp_reward"],
                    category="weekly",
                    deadline=next_sunday_end,
                    icon=template["icon"],
                    requirements=template.get("requirements", {}),
                    target=template.get("target", 1)
                )
                
                self.db.save_quest(quest)
                
        except Exception as e:
            logger.error(f"Failed to generate weekly quests: {e}")
    
    def _generate_achievement_quests(self):
        """Generate persistent achievement quests"""
        try:
            achievement_templates = self.quest_templates["achievements"]
            
            for template in achievement_templates:
                quest = Quest(
                    id=f"achievement_{template['title'].lower().replace(' ', '_')}",
                    title=template["title"],
                    description=template["description"],
                    type=template["type"],
                    difficulty=template["difficulty"],
                    xp_reward=template["xp_reward"],
                    category="achievements",
                    icon=template["icon"],
                    requirements=template.get("requirements", {}),
                    target=template.get("target", 1)
                )
                
                self.db.save_quest(quest)
                
        except Exception as e:
            logger.error(f"Failed to generate achievement quests: {e}")
    
    def get_all_quests(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all quests organized by category"""
        try:
            return {
                "daily": self.db.get_quests_by_category("daily"),
                "weekly": self.db.get_quests_by_category("weekly"),
                "achievements": self.db.get_quests_by_category("achievements")
            }
        except Exception as e:
            logger.error(f"Failed to get all quests: {e}")
            return {"daily": [], "weekly": [], "achievements": []}
    
    def get_todays_quests(self) -> List[Dict[str, Any]]:
        """Get today's active quests"""
        try:
            daily_quests = self.db.get_quests_by_category("daily")
            today = datetime.now().date()
            
            today_quests = [
                quest for quest in daily_quests
                if quest.get("deadline") and 
                datetime.fromisoformat(quest["deadline"]).date() >= today and
                quest.get("status") != "completed"
            ]
            
            return today_quests[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Failed to get today's quests: {e}")
            return []
    
    def complete_quest(self, quest_id: str) -> Dict[str, Any]:
        """Complete a quest and return results"""
        try:
            # Mark quest as completed in database
            success = self.db.complete_quest(quest_id)
            
            if not success:
                return {
                    "success": False,
                    "error": "Quest not found or already completed"
                }
            
            # Get quest details to determine XP reward
            all_quests = self.get_all_quests()
            completed_quest = None
            
            for category_quests in all_quests.values():
                for quest in category_quests:
                    if quest["id"] == quest_id:
                        completed_quest = quest
                        break
                if completed_quest:
                    break
            
            if not completed_quest:
                return {
                    "success": False,
                    "error": "Quest details not found"
                }
            
            xp_gained = completed_quest.get("xpReward", 50)
            
            # Award XP to user
            self.db.award_xp(xp_gained)
            
            # Update user quest completion count
            self.db.update_user_stats(questsCompleted=1)
            
            # Check if user leveled up
            user_data = self.db.get_user_data()
            new_level = max(1, int(user_data["totalXp"] / 100) + 1)
            leveled_up = new_level > user_data["level"]
            
            # Add activity log
            self.db.add_activity({
                "type": "quest_completed",
                "description": f"Completed quest: {completed_quest['title']}",
                "xp": xp_gained,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "xpGained": xp_gained,
                "newLevel": new_level if leveled_up else None,
                "questTitle": completed_quest["title"]
            }
            
        except Exception as e:
            logger.error(f"Failed to complete quest {quest_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_quest_progress(self, action_type: str, **kwargs) -> List[str]:
        """Check and update quest progress based on user actions"""
        try:
            updated_quests = []
            all_quests = self.get_all_quests()
            
            for category, quests in all_quests.items():
                for quest in quests:
                    if quest.get("status") == "completed":
                        continue
                    
                    requirements = quest.get("requirements", {})
                    should_update = False
                    
                    # Check different action types
                    if action_type == "files_organized":
                        files_count = kwargs.get("count", 0)
                        folder_type = kwargs.get("folder_type", "")
                        file_types = kwargs.get("file_types", [])
                        
                        # Check folder-specific quests
                        if requirements.get("folder") == folder_type and files_count >= requirements.get("min_files", 1):
                            should_update = True
                        
                        # Check file-type specific quests
                        if requirements.get("file_type") in file_types and files_count >= requirements.get("min_files", 1):
                            should_update = True
                        
                        # Check general organization quests
                        if requirements.get("files_organized") and files_count > 0:
                            current_progress = quest.get("progress", 0)
                            new_progress = min(current_progress + files_count, quest.get("target", 1))
                            if new_progress > current_progress:
                                # Update quest progress
                                # Note: This would need to be implemented in the database
                                should_update = True
                    
                    elif action_type == "duplicates_removed":
                        duplicates_count = kwargs.get("count", 0)
                        
                        if requirements.get("min_duplicates") and duplicates_count >= requirements["min_duplicates"]:
                            should_update = True
                        
                        if requirements.get("duplicates_removed"):
                            current_progress = quest.get("progress", 0)
                            new_progress = min(current_progress + duplicates_count, quest.get("target", 1))
                            if new_progress > current_progress:
                                should_update = True
                    
                    if should_update:
                        updated_quests.append(quest["id"])
            
            return updated_quests
            
        except Exception as e:
            logger.error(f"Failed to check quest progress: {e}")
            return []
    
    def get_quest_suggestions(self, user_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get personalized quest suggestions based on user activity"""
        try:
            suggestions = []
            
            files_organized = user_stats.get("filesOrganized", 0)
            duplicates_removed = user_stats.get("duplicatesRemoved", 0)
            
            # Suggest based on user's weakest areas
            if files_organized < 10:
                suggestions.append({
                    "type": "beginner",
                    "title": "Getting Started",
                    "description": "Try organizing your Downloads folder first",
                    "priority": "high"
                })
            
            if duplicates_removed == 0:
                suggestions.append({
                    "type": "duplicate_detection",
                    "title": "Find Duplicates",
                    "description": "Scan for duplicate files to free up space",
                    "priority": "medium"
                })
            
            # Suggest based on completion patterns
            completed_quests = self.db.get_quests_by_category("daily")
            completed_count = len([q for q in completed_quests if q.get("status") == "completed"])
            
            if completed_count > 5:
                suggestions.append({
                    "type": "advanced",
                    "title": "Take on Weekly Challenges",
                    "description": "You're ready for bigger organization projects",
                    "priority": "medium"
                })
            
            return suggestions[:3]  # Top 3 suggestions
            
        except Exception as e:
            logger.error(f"Failed to get quest suggestions: {e}")
            return []
    
    def cleanup_expired_quests(self):
        """Clean up expired quests (run this periodically)"""
        try:
            # This would need to be implemented to mark expired quests
            # and generate new ones as needed
            logger.info("Cleaned up expired quests")
        except Exception as e:
            logger.error(f"Failed to cleanup expired quests: {e}")
