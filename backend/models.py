from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class QuestType(Enum):
    ORGANIZE = "organize"
    CLEAN = "clean"
    DUPLICATE = "duplicate"
    SORT = "sort"
    BACKUP = "backup"
    RENAME = "rename"

class QuestStatus(Enum):
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class User:
    id: int = 1
    level: int = 1
    xp: int = 0
    total_xp: int = 0
    streak: int = 0
    badges: List[str] = None
    completed_quests: int = 0
    last_active: datetime = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []
        if self.last_active is None:
            self.last_active = datetime.now()
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Quest:
    id: str
    title: str
    description: str
    type: QuestType
    difficulty: Difficulty
    xp_reward: int
    status: QuestStatus = QuestStatus.AVAILABLE
    category: str = "daily"  # daily, weekly, achievement
    progress: int = 0
    target: int = 1
    deadline: Optional[datetime] = None
    icon: str = "fas fa-tasks"
    requirements: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.requirements is None:
            self.requirements = {}

@dataclass
class Badge:
    id: str
    name: str
    description: str
    requirements: str
    icon: str = "fas fa-medal"
    category: str = "achievement"
    xp_requirement: int = 0
    quest_requirement: int = 0
    special_requirement: Optional[str] = None

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str
    progress: int = 0
    target: int = 1
    xp_reward: int = 100
    completed: bool = False
    completed_at: Optional[datetime] = None

@dataclass
class FileInfo:
    path: str
    name: str
    size: int
    type: str
    extension: str
    modified: datetime
    created: datetime
    hash: Optional[str] = None

@dataclass
class DuplicateGroup:
    id: str
    name: str
    files: List[FileInfo]
    total_size: int
    duplicate_count: int

@dataclass
class OrganizationRule:
    file_type: str
    enabled: bool
    target_folder: str
    pattern: Optional[str] = None

@dataclass
class ScanResult:
    path: str
    total_files: int
    total_folders: int
    total_size: int
    file_types: Dict[str, int]
    largest_files: List[FileInfo]
    oldest_files: List[FileInfo]
    success: bool = True
    error: Optional[str] = None

@dataclass
class Activity:
    id: Optional[int] = None
    type: str = ""
    description: str = ""
    xp: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class UserStats:
    files_organized: int = 0
    duplicates_removed: int = 0
    quests_completed: int = 0
    total_xp_earned: int = 0
    streak_days: int = 0
    folders_cleaned: int = 0
    space_freed: int = 0  # in bytes
    
class FileType(Enum):
    IMAGE = "Images"
    DOCUMENT = "Documents"
    SPREADSHEET = "Spreadsheets" 
    PRESENTATION = "Presentations"
    VIDEO = "Videos"
    AUDIO = "Audio"
    ARCHIVE = "Archives"
    CODE = "Code"
    EXECUTABLE = "Executables"
    OTHER = "Other"

FILE_TYPE_EXTENSIONS = {
    FileType.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'],
    FileType.DOCUMENT: ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
    FileType.SPREADSHEET: ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
    FileType.PRESENTATION: ['.ppt', '.pptx', '.odp', '.key'],
    FileType.VIDEO: ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
    FileType.AUDIO: ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    FileType.ARCHIVE: ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
    FileType.CODE: ['.js', '.py', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go'],
    FileType.EXECUTABLE: ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.app'],
}

def get_file_type(extension: str) -> FileType:
    """Determine file type based on extension"""
    extension = extension.lower()
    for file_type, extensions in FILE_TYPE_EXTENSIONS.items():
        if extension in extensions:
            return file_type
    return FileType.OTHER
