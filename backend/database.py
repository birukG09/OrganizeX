import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import os

from models import User, Quest, Badge, Achievement, Activity, UserStats

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "organizex.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    total_xp INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    badges TEXT DEFAULT '[]',
                    completed_quests INTEGER DEFAULT 0,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Quests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quests (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    xp_reward INTEGER NOT NULL,
                    status TEXT DEFAULT 'available',
                    category TEXT DEFAULT 'daily',
                    progress INTEGER DEFAULT 0,
                    target INTEGER DEFAULT 1,
                    deadline TIMESTAMP,
                    icon TEXT DEFAULT 'fas fa-tasks',
                    requirements TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # Badges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS badges (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    requirements TEXT,
                    icon TEXT DEFAULT 'fas fa-medal',
                    category TEXT DEFAULT 'achievement',
                    xp_requirement INTEGER DEFAULT 0,
                    quest_requirement INTEGER DEFAULT 0,
                    special_requirement TEXT
                )
            """)
            
            # Achievements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT 'fas fa-trophy',
                    progress INTEGER DEFAULT 0,
                    target INTEGER DEFAULT 1,
                    xp_reward INTEGER DEFAULT 100,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP
                )
            """)
            
            # Activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    description TEXT,
                    xp INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    id INTEGER PRIMARY KEY,
                    files_organized INTEGER DEFAULT 0,
                    duplicates_removed INTEGER DEFAULT 0,
                    quests_completed INTEGER DEFAULT 0,
                    total_xp_earned INTEGER DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    folders_cleaned INTEGER DEFAULT 0,
                    space_freed INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
            
            # Initialize default user if not exists
            self._init_default_user(cursor)
            self._init_default_badges(cursor)
            self._init_default_achievements(cursor)
            conn.commit()
            
            logger.info("Database initialized successfully")
    
    def _init_default_user(self, cursor):
        """Initialize default user if none exists"""
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO users (id, level, xp, total_xp, streak, badges, completed_quests)
                VALUES (1, 1, 0, 0, 0, '[]', 0)
            """)
            
            cursor.execute("""
                INSERT INTO user_stats (id) VALUES (1)
            """)
    
    def _init_default_badges(self, cursor):
        """Initialize default badges"""
        badges = [
            ("clean_desk_novice", "Clean Desk Novice", "Organize your first folder", "Complete 1 organization quest"),
            ("download_slayer", "Download Slayer", "Master of the Downloads folder", "Clean Downloads folder 5 times"),
            ("duplicate_destroyer", "Duplicate Destroyer", "Remove 100 duplicate files", "Delete 100 duplicate files"),
            ("file_master", "File Master", "Organize 1000 files", "Organize 1000 files total"),
            ("organization_guru", "Organization Guru", "Reach level 20", "Achieve level 20"),
            ("speed_sorter", "Speed Sorter", "Complete 10 quests in one day", "Complete 10 quests in a single day"),
            ("streak_master", "Streak Master", "Maintain a 30-day streak", "Keep organizing for 30 days straight"),
            ("quest_completer", "Quest Completer", "Complete 100 quests", "Finish 100 quests total")
        ]
        
        for badge_id, name, description, requirements in badges:
            cursor.execute("""
                INSERT OR IGNORE INTO badges (id, name, description, requirements)
                VALUES (?, ?, ?, ?)
            """, (badge_id, name, description, requirements))
    
    def _init_default_achievements(self, cursor):
        """Initialize default achievements"""
        achievements = [
            ("first_organization", "First Steps", "Complete your first file organization", "fas fa-baby", 1, 100),
            ("file_organizer", "File Organizer", "Organize 100 files", "fas fa-folder", 100, 500),
            ("duplicate_hunter", "Duplicate Hunter", "Find and remove 50 duplicate files", "fas fa-search", 50, 300),
            ("quest_master", "Quest Master", "Complete 50 quests", "fas fa-crown", 50, 1000),
            ("storage_saver", "Storage Saver", "Free up 1GB of space", "fas fa-hdd", 1024, 750)
        ]
        
        for achievement_id, name, description, icon, target, xp_reward in achievements:
            cursor.execute("""
                INSERT OR IGNORE INTO achievements (id, name, description, icon, target, xp_reward)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (achievement_id, name, description, icon, target, xp_reward))
    
    def get_user_data(self) -> Dict[str, Any]:
        """Get current user data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = 1")
            row = cursor.fetchone()
            
            if row:
                return {
                    "level": row["level"],
                    "xp": row["xp"],
                    "totalXp": row["total_xp"],
                    "streak": row["streak"],
                    "badges": json.loads(row["badges"]),
                    "completedQuests": row["completed_quests"]
                }
            else:
                return {
                    "level": 1,
                    "xp": 0,
                    "totalXp": 0,
                    "streak": 0,
                    "badges": [],
                    "completedQuests": 0
                }
    
    def update_user_data(self, user_data: Dict[str, Any]):
        """Update user data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate level based on total XP
            total_xp = user_data.get("totalXp", 0)
            level = max(1, int(total_xp / 100) + 1)
            xp_for_current_level = total_xp % 100
            
            cursor.execute("""
                UPDATE users SET 
                    level = ?, 
                    xp = ?, 
                    total_xp = ?, 
                    streak = ?, 
                    badges = ?, 
                    completed_quests = ?,
                    last_active = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (
                level,
                xp_for_current_level,
                total_xp,
                user_data.get("streak", 0),
                json.dumps(user_data.get("badges", [])),
                user_data.get("completedQuests", 0)
            ))
            
            conn.commit()
    
    def award_xp(self, xp_amount: int):
        """Award XP to user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET 
                    xp = xp + ?,
                    total_xp = total_xp + ?
                WHERE id = 1
            """, (xp_amount, xp_amount))
            
            # Update level based on new total XP
            cursor.execute("SELECT total_xp FROM users WHERE id = 1")
            total_xp = cursor.fetchone()["total_xp"]
            new_level = max(1, int(total_xp / 100) + 1)
            xp_for_current_level = total_xp % 100
            
            cursor.execute("""
                UPDATE users SET level = ?, xp = ? WHERE id = 1
            """, (new_level, xp_for_current_level))
            
            conn.commit()
    
    def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_stats WHERE id = 1")
            row = cursor.fetchone()
            
            if row:
                return {
                    "filesOrganized": row["files_organized"],
                    "duplicatesRemoved": row["duplicates_removed"],
                    "questsCompleted": row["quests_completed"]
                }
            else:
                return {
                    "filesOrganized": 0,
                    "duplicatesRemoved": 0,
                    "questsCompleted": 0
                }
    
    def update_user_stats(self, **kwargs):
        """Update user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for key, value in kwargs.items():
                if key in ["filesOrganized", "duplicatesRemoved", "questsCompleted"]:
                    db_key = key.replace("O", "_o").replace("R", "_r").replace("C", "_c").lower()
                    cursor.execute(f"""
                        UPDATE user_stats SET {db_key} = {db_key} + ? WHERE id = 1
                    """, (value,))
            
            conn.commit()
    
    def add_activity(self, activity: Dict[str, Any]):
        """Add activity entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity (type, description, xp, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                activity["type"],
                activity["description"],
                activity["xp"],
                activity.get("timestamp", datetime.now().isoformat())
            ))
            conn.commit()
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity entries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM activity 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    "type": row["type"],
                    "description": row["description"],
                    "xp": row["xp"],
                    "timestamp": row["timestamp"]
                })
            
            return activities
    
    def save_quest(self, quest: Quest):
        """Save or update a quest"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO quests 
                (id, title, description, type, difficulty, xp_reward, status, category, 
                 progress, target, deadline, icon, requirements, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quest.id, quest.title, quest.description, quest.type.value,
                quest.difficulty.value, quest.xp_reward, quest.status.value,
                quest.category, quest.progress, quest.target,
                quest.deadline.isoformat() if quest.deadline else None,
                quest.icon, json.dumps(quest.requirements),
                quest.created_at.isoformat(), 
                quest.completed_at.isoformat() if quest.completed_at else None
            ))
            conn.commit()
    
    def get_quests_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get quests by category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM quests WHERE category = ? ORDER BY created_at DESC
            """, (category,))
            
            quests = []
            for row in cursor.fetchall():
                quests.append({
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "type": row["type"],
                    "difficulty": row["difficulty"],
                    "xpReward": row["xp_reward"],
                    "status": row["status"],
                    "progress": row["progress"],
                    "target": row["target"],
                    "deadline": row["deadline"],
                    "icon": row["icon"]
                })
            
            return quests
    
    def complete_quest(self, quest_id: str) -> bool:
        """Mark quest as completed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE quests SET 
                    status = 'completed',
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (quest_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_badges(self) -> List[Dict[str, Any]]:
        """Get all badges"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM badges")
            
            badges = []
            for row in cursor.fetchall():
                badges.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "requirements": row["requirements"],
                    "icon": row["icon"]
                })
            
            return badges
    
    def get_achievements(self) -> List[Dict[str, Any]]:
        """Get all achievements with progress"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM achievements")
            
            achievements = []
            for row in cursor.fetchall():
                achievements.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "icon": row["icon"],
                    "progress": row["progress"],
                    "target": row["target"],
                    "xpReward": row["xp_reward"],
                    "completed": bool(row["completed"])
                })
            
            return achievements
    
    def update_achievement_progress(self, achievement_id: str, progress: int):
        """Update achievement progress"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE achievements 
                SET progress = ?, completed = CASE WHEN progress >= target THEN TRUE ELSE FALSE END
                WHERE id = ?
            """, (progress, achievement_id))
            conn.commit()
