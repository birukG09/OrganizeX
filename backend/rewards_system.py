import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from models import Badge, Achievement, User
from database import DatabaseManager

logger = logging.getLogger(__name__)

class RewardsSystem:
    """
    Rewards system for managing badges, achievements, and user progression
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.badge_requirements = self._initialize_badge_requirements()
        self.achievement_trackers = self._initialize_achievement_trackers()
    
    def _initialize_badge_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Initialize badge unlock requirements"""
        return {
            "clean_desk_novice": {
                "type": "quest_completion",
                "requirement": 1,
                "category": "organization"
            },
            "download_slayer": {
                "type": "folder_cleanups",
                "requirement": 5,
                "folder": "downloads"
            },
            "duplicate_destroyer": {
                "type": "duplicates_removed",
                "requirement": 100
            },
            "file_master": {
                "type": "files_organized",
                "requirement": 1000
            },
            "organization_guru": {
                "type": "level_reached",
                "requirement": 20
            },
            "speed_sorter": {
                "type": "daily_quests",
                "requirement": 10,
                "timeframe": "single_day"
            },
            "streak_master": {
                "type": "streak_days",
                "requirement": 30
            },
            "quest_completer": {
                "type": "total_quests",
                "requirement": 100
            }
        }
    
    def _initialize_achievement_trackers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize achievement tracking configuration"""
        return {
            "first_organization": {
                "trigger": "files_organized",
                "condition": lambda current, new: current == 0 and new > 0
            },
            "file_organizer": {
                "trigger": "files_organized",
                "condition": lambda current, new: new >= 100
            },
            "duplicate_hunter": {
                "trigger": "duplicates_removed", 
                "condition": lambda current, new: new >= 50
            },
            "quest_master": {
                "trigger": "quests_completed",
                "condition": lambda current, new: new >= 50
            },
            "storage_saver": {
                "trigger": "space_freed",
                "condition": lambda current, new: new >= 1024 * 1024 * 1024  # 1GB
            }
        }
    
    def check_rewards(self, xp_gained: int) -> Dict[str, Any]:
        """Check for new badges and achievements after XP gain"""
        try:
            rewards = {
                "newBadges": [],
                "newAchievements": [],
                "levelUp": False,
                "newLevel": None
            }
            
            # Get current user data
            user_data = self.db.get_user_data()
            user_stats = self.db.get_user_stats()
            
            # Check for level up
            old_level = user_data["level"]
            new_total_xp = user_data["totalXp"] + xp_gained
            new_level = max(1, int(new_total_xp / 100) + 1)
            
            if new_level > old_level:
                rewards["levelUp"] = True
                rewards["newLevel"] = new_level
                
                # Check for level-based badges
                level_badges = self._check_level_badges(new_level)
                rewards["newBadges"].extend(level_badges)
            
            # Check for stat-based badges
            stat_badges = self._check_stat_badges(user_stats)
            rewards["newBadges"].extend(stat_badges)
            
            # Check for achievements
            new_achievements = self._check_achievements(user_stats)
            rewards["newAchievements"].extend(new_achievements)
            
            # Update user badges if any new ones were earned
            if rewards["newBadges"]:
                current_badges = user_data.get("badges", [])
                updated_badges = current_badges + rewards["newBadges"]
                
                self.db.update_user_data({
                    **user_data,
                    "badges": updated_badges
                })
            
            return rewards
            
        except Exception as e:
            logger.error(f"Failed to check rewards: {e}")
            return {"newBadges": [], "newAchievements": [], "levelUp": False}
    
    def _check_level_badges(self, level: int) -> List[str]:
        """Check for badges unlocked by reaching certain levels"""
        try:
            new_badges = []
            
            for badge_id, requirements in self.badge_requirements.items():
                if requirements["type"] == "level_reached" and level >= requirements["requirement"]:
                    # Check if user already has this badge
                    user_data = self.db.get_user_data()
                    if badge_id not in user_data.get("badges", []):
                        new_badges.append(badge_id)
            
            return new_badges
            
        except Exception as e:
            logger.error(f"Failed to check level badges: {e}")
            return []
    
    def _check_stat_badges(self, user_stats: Dict[str, int]) -> List[str]:
        """Check for badges unlocked by user statistics"""
        try:
            new_badges = []
            user_data = self.db.get_user_data()
            current_badges = user_data.get("badges", [])
            
            for badge_id, requirements in self.badge_requirements.items():
                if badge_id in current_badges:
                    continue
                
                req_type = requirements["type"]
                req_value = requirements["requirement"]
                
                should_unlock = False
                
                if req_type == "files_organized":
                    should_unlock = user_stats.get("filesOrganized", 0) >= req_value
                elif req_type == "duplicates_removed":
                    should_unlock = user_stats.get("duplicatesRemoved", 0) >= req_value
                elif req_type == "total_quests":
                    should_unlock = user_stats.get("questsCompleted", 0) >= req_value
                elif req_type == "streak_days":
                    should_unlock = user_data.get("streak", 0) >= req_value
                elif req_type == "quest_completion":
                    should_unlock = user_stats.get("questsCompleted", 0) >= req_value
                
                if should_unlock:
                    new_badges.append(badge_id)
            
            return new_badges
            
        except Exception as e:
            logger.error(f"Failed to check stat badges: {e}")
            return []
    
    def _check_achievements(self, user_stats: Dict[str, int]) -> List[str]:
        """Check for completed achievements"""
        try:
            new_achievements = []
            achievements = self.db.get_achievements()
            
            for achievement in achievements:
                if achievement.get("completed"):
                    continue
                
                achievement_id = achievement["id"]
                current_progress = achievement.get("progress", 0)
                target = achievement.get("target", 1)
                
                # Update progress based on user stats
                new_progress = self._calculate_achievement_progress(achievement_id, user_stats)
                
                if new_progress > current_progress:
                    self.db.update_achievement_progress(achievement_id, new_progress)
                    
                    if new_progress >= target:
                        new_achievements.append(achievement_id)
                        # Award achievement XP
                        xp_reward = achievement.get("xpReward", 100)
                        self.db.award_xp(xp_reward)
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Failed to check achievements: {e}")
            return []
    
    def _calculate_achievement_progress(self, achievement_id: str, user_stats: Dict[str, int]) -> int:
        """Calculate current progress for an achievement"""
        try:
            progress_mapping = {
                "first_organization": user_stats.get("filesOrganized", 0),
                "file_organizer": user_stats.get("filesOrganized", 0),
                "duplicate_hunter": user_stats.get("duplicatesRemoved", 0),
                "quest_master": user_stats.get("questsCompleted", 0),
                "storage_saver": 0  # This would need space freed tracking
            }
            
            return progress_mapping.get(achievement_id, 0)
            
        except Exception as e:
            logger.error(f"Failed to calculate achievement progress for {achievement_id}: {e}")
            return 0
    
    def get_all_badges(self) -> List[Dict[str, Any]]:
        """Get all badges with their details"""
        try:
            return self.db.get_badges()
        except Exception as e:
            logger.error(f"Failed to get badges: {e}")
            return []
    
    def get_achievements(self) -> List[Dict[str, Any]]:
        """Get all achievements with current progress"""
        try:
            achievements = self.db.get_achievements()
            user_stats = self.db.get_user_stats()
            
            # Update progress for each achievement
            for achievement in achievements:
                achievement_id = achievement["id"]
                current_progress = self._calculate_achievement_progress(achievement_id, user_stats)
                achievement["progress"] = current_progress
            
            return achievements
        except Exception as e:
            logger.error(f"Failed to get achievements: {e}")
            return []
    
    def get_user_rewards_summary(self) -> Dict[str, Any]:
        """Get a summary of user's rewards and progress"""
        try:
            user_data = self.db.get_user_data()
            user_stats = self.db.get_user_stats()
            badges = self.get_all_badges()
            achievements = self.get_achievements()
            
            earned_badges = user_data.get("badges", [])
            completed_achievements = [a for a in achievements if a.get("completed")]
            
            # Calculate next milestones
            next_level_xp = (user_data["level"] * 100) - user_data["xp"]
            next_badges = self._get_next_badges(user_stats, earned_badges)
            
            return {
                "level": user_data["level"],
                "xp": user_data["xp"],
                "nextLevelXp": next_level_xp,
                "totalBadges": len(badges),
                "earnedBadges": len(earned_badges),
                "totalAchievements": len(achievements),
                "completedAchievements": len(completed_achievements),
                "streak": user_data.get("streak", 0),
                "nextBadges": next_badges[:3],  # Next 3 badges to unlock
                "completionPercentage": self._calculate_completion_percentage(user_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user rewards summary: {e}")
            return {}
    
    def _get_next_badges(self, user_stats: Dict[str, int], earned_badges: List[str]) -> List[Dict[str, Any]]:
        """Get the next badges user can unlock"""
        try:
            next_badges = []
            
            for badge_id, requirements in self.badge_requirements.items():
                if badge_id in earned_badges:
                    continue
                
                req_type = requirements["type"]
                req_value = requirements["requirement"]
                
                current_value = 0
                badge_name = badge_id.replace("_", " ").title()
                
                if req_type == "files_organized":
                    current_value = user_stats.get("filesOrganized", 0)
                elif req_type == "duplicates_removed":
                    current_value = user_stats.get("duplicatesRemoved", 0)
                elif req_type == "total_quests":
                    current_value = user_stats.get("questsCompleted", 0)
                
                if current_value < req_value:
                    progress = (current_value / req_value) * 100
                    remaining = req_value - current_value
                    
                    next_badges.append({
                        "id": badge_id,
                        "name": badge_name,
                        "progress": min(progress, 99),  # Cap at 99% until earned
                        "remaining": remaining,
                        "type": req_type
                    })
            
            # Sort by progress (closest to completion first)
            next_badges.sort(key=lambda x: x["progress"], reverse=True)
            return next_badges
            
        except Exception as e:
            logger.error(f"Failed to get next badges: {e}")
            return []
    
    def _calculate_completion_percentage(self, user_stats: Dict[str, int]) -> float:
        """Calculate overall completion percentage"""
        try:
            total_metrics = 4  # files organized, duplicates removed, quests completed, level
            completed_metrics = 0
            
            if user_stats.get("filesOrganized", 0) > 0:
                completed_metrics += 1
            if user_stats.get("duplicatesRemoved", 0) > 0:
                completed_metrics += 1
            if user_stats.get("questsCompleted", 0) > 0:
                completed_metrics += 1
            
            user_data = self.db.get_user_data()
            if user_data.get("level", 1) > 1:
                completed_metrics += 1
            
            return (completed_metrics / total_metrics) * 100
            
        except Exception as e:
            logger.error(f"Failed to calculate completion percentage: {e}")
            return 0.0
    
    def award_bonus_xp(self, reason: str, amount: int) -> bool:
        """Award bonus XP for special achievements"""
        try:
            self.db.award_xp(amount)
            
            # Log the bonus XP
            self.db.add_activity({
                "type": "bonus_xp",
                "description": f"Bonus XP: {reason}",
                "xp": amount,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to award bonus XP: {e}")
            return False
    
    def get_daily_bonus_eligibility(self) -> Dict[str, Any]:
        """Check if user is eligible for daily bonuses"""
        try:
            user_data = self.db.get_user_data()
            last_active = user_data.get("last_active")
            
            if not last_active:
                return {"eligible": True, "bonus_type": "welcome", "amount": 50}
            
            last_active_date = datetime.fromisoformat(last_active).date()
            today = datetime.now().date()
            
            if last_active_date < today:
                # Check for streak bonus
                streak = user_data.get("streak", 0)
                if streak >= 7:
                    return {"eligible": True, "bonus_type": "streak", "amount": 25}
                elif streak >= 3:
                    return {"eligible": True, "bonus_type": "consistency", "amount": 15}
                else:
                    return {"eligible": True, "bonus_type": "daily", "amount": 10}
            
            return {"eligible": False, "reason": "Already claimed today"}
            
        except Exception as e:
            logger.error(f"Failed to check daily bonus eligibility: {e}")
            return {"eligible": False, "reason": "Error checking eligibility"}
