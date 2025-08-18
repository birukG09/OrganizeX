import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter, defaultdict
from pathlib import Path
import mimetypes
import re

from models import FileInfo, FileType, get_file_type, FILE_TYPE_EXTENSIONS

logger = logging.getLogger(__name__)

class AIClassifier:
    """
    AI-powered file classifier for smart organization
    Uses rule-based classification with pattern matching and content analysis
    """
    
    def __init__(self):
        # Initialize MIME type database
        mimetypes.init()
        
        # Pattern-based classification rules
        self.filename_patterns = {
            FileType.IMAGE: [
                r'screenshot.*\.(png|jpg|jpeg)$',
                r'.*_photo\.(jpg|jpeg|png)$',
                r'IMG_\d+\.(jpg|jpeg|png)$',
                r'.*_wallpaper\.(jpg|jpeg|png)$'
            ],
            FileType.DOCUMENT: [
                r'.*_resume\.(pdf|doc|docx)$',
                r'.*_cv\.(pdf|doc|docx)$',
                r'.*_report\.(pdf|doc|docx)$',
                r'.*_proposal\.(pdf|doc|docx)$'
            ],
            FileType.CODE: [
                r'.*\.(js|ts|jsx|tsx|py|java|cpp|c|h|hpp)$',
                r'.*\.(html|css|scss|sass|less)$',
                r'.*\.(php|rb|go|rs|kt|swift)$'
            ],
            FileType.ARCHIVE: [
                r'.*_backup\.(zip|rar|tar|gz)$',
                r'.*_archive\.(zip|rar|tar|gz)$'
            ]
        }
        
        # Content-based keywords for classification
        self.content_keywords = {
            FileType.DOCUMENT: [
                'invoice', 'receipt', 'contract', 'agreement',
                'resume', 'cv', 'cover_letter', 'report'
            ],
            FileType.IMAGE: [
                'photo', 'picture', 'image', 'screenshot',
                'wallpaper', 'avatar', 'profile', 'thumbnail'
            ],
            FileType.AUDIO: [
                'music', 'song', 'audio', 'sound',
                'podcast', 'recording', 'voice'
            ],
            FileType.VIDEO: [
                'movie', 'video', 'clip', 'recording',
                'tutorial', 'presentation', 'webinar'
            ]
        }
        
        # Size-based heuristics (in bytes)
        self.size_heuristics = {
            FileType.IMAGE: (1024, 50 * 1024 * 1024),  # 1KB to 50MB
            FileType.AUDIO: (100 * 1024, 500 * 1024 * 1024),  # 100KB to 500MB
            FileType.VIDEO: (1024 * 1024, 10 * 1024 * 1024 * 1024),  # 1MB to 10GB
            FileType.DOCUMENT: (1024, 100 * 1024 * 1024)  # 1KB to 100MB
        }
    
    def classify_file(self, file_info: FileInfo) -> Tuple[FileType, float]:
        """
        Classify a single file and return the predicted type with confidence
        """
        try:
            # Start with extension-based classification
            base_type = get_file_type(file_info.extension)
            confidence = 0.7  # Base confidence for extension matching
            
            # Apply pattern matching for filename
            pattern_type, pattern_confidence = self._classify_by_pattern(file_info.name)
            if pattern_confidence > confidence:
                base_type = pattern_type
                confidence = pattern_confidence
            
            # Apply content-based classification (filename keywords)
            content_type, content_confidence = self._classify_by_content_keywords(file_info.name)
            if content_confidence > confidence:
                base_type = content_type
                confidence = content_confidence
            
            # Apply size-based heuristics
            size_adjustment = self._get_size_confidence_adjustment(file_info, base_type)
            confidence = min(1.0, confidence + size_adjustment)
            
            # Apply MIME type validation
            mime_adjustment = self._get_mime_confidence_adjustment(file_info, base_type)
            confidence = min(1.0, confidence + mime_adjustment)
            
            return base_type, confidence
            
        except Exception as e:
            logger.error(f"Failed to classify file {file_info.name}: {e}")
            return FileType.OTHER, 0.5
    
    def _classify_by_pattern(self, filename: str) -> Tuple[FileType, float]:
        """Classify file based on filename patterns"""
        filename_lower = filename.lower()
        
        for file_type, patterns in self.filename_patterns.items():
            for pattern in patterns:
                if re.match(pattern, filename_lower):
                    return file_type, 0.9
        
        return FileType.OTHER, 0.0
    
    def _classify_by_content_keywords(self, filename: str) -> Tuple[FileType, float]:
        """Classify file based on content keywords in filename"""
        filename_lower = filename.lower()
        
        best_type = FileType.OTHER
        best_score = 0.0
        
        for file_type, keywords in self.content_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in filename_lower:
                    score += 0.3
            
            if score > best_score:
                best_type = file_type
                best_score = score
        
        return best_type, min(best_score, 0.8)
    
    def _get_size_confidence_adjustment(self, file_info: FileInfo, predicted_type: FileType) -> float:
        """Adjust confidence based on file size appropriateness"""
        if predicted_type not in self.size_heuristics:
            return 0.0
        
        min_size, max_size = self.size_heuristics[predicted_type]
        
        if min_size <= file_info.size <= max_size:
            return 0.1  # Boost confidence if size is appropriate
        elif file_info.size < min_size or file_info.size > max_size * 2:
            return -0.2  # Reduce confidence if size is very inappropriate
        else:
            return -0.1  # Slightly reduce confidence if size is somewhat inappropriate
    
    def _get_mime_confidence_adjustment(self, file_info: FileInfo, predicted_type: FileType) -> float:
        """Adjust confidence based on MIME type validation"""
        try:
            mime_type, _ = mimetypes.guess_type(file_info.name)
            if not mime_type:
                return 0.0
            
            # Map MIME types to our FileType enum
            mime_category = mime_type.split('/')[0]
            
            type_mime_mapping = {
                FileType.IMAGE: 'image',
                FileType.AUDIO: 'audio',
                FileType.VIDEO: 'video',
                FileType.DOCUMENT: ['application', 'text'],
                FileType.CODE: 'text'
            }
            
            expected_mime = type_mime_mapping.get(predicted_type)
            
            if isinstance(expected_mime, list):
                if mime_category in expected_mime:
                    return 0.1
            elif mime_category == expected_mime:
                return 0.1
            elif mime_category in ['application', 'text'] and predicted_type == FileType.OTHER:
                return 0.05
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Failed to get MIME type for {file_info.name}: {e}")
            return 0.0
    
    def classify_files(self, files: List[FileInfo]) -> List[Tuple[FileInfo, FileType, float]]:
        """
        Classify a list of files
        """
        classified_files = []
        
        for file_info in files:
            file_type, confidence = self.classify_file(file_info)
            classified_files.append((file_info, file_type, confidence))
        
        return classified_files
    
    def get_file_type_distribution(self, classified_files: List[Tuple[FileInfo, FileType, float]]) -> Dict[str, int]:
        """
        Get the distribution of file types from classified files
        """
        type_counts = Counter()
        
        for file_info, file_type, confidence in classified_files:
            if confidence >= 0.5:  # Only count confident classifications
                type_counts[file_type.value] += 1
        
        return dict(type_counts)
    
    def get_organization_suggestions(self, classified_files: List[Tuple[FileInfo, FileType, float]]) -> Dict[str, List[str]]:
        """
        Generate organization suggestions based on classified files
        """
        suggestions = defaultdict(list)
        
        for file_info, file_type, confidence in classified_files:
            if confidence >= 0.7:  # High confidence suggestions
                suggestions[file_type.value].append(file_info.name)
        
        return dict(suggestions)
    
    def analyze_folder_health(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze folder organization health and provide recommendations
        """
        try:
            file_types = scan_result.get("file_types", {})
            total_files = scan_result.get("total_files", 0)
            
            if total_files == 0:
                return {
                    "health_score": 100,
                    "recommendations": [],
                    "issues": []
                }
            
            # Calculate organization score
            health_score = 100
            recommendations = []
            issues = []
            
            # Check for too many different file types in root
            unique_types = len(file_types)
            if unique_types > 5:
                health_score -= 20
                issues.append(f"Too many file types ({unique_types}) in one folder")
                recommendations.append("Consider organizing files into subfolders by type")
            
            # Check for dominant file types that should be organized
            for file_type, count in file_types.items():
                percentage = (count / total_files) * 100
                if percentage > 30 and count > 10:
                    health_score -= 15
                    issues.append(f"Many {file_type.lower()} files ({count}) not organized")
                    recommendations.append(f"Create a dedicated folder for {file_type.lower()}")
            
            # Check for mixed content
            if len(file_types) > 3 and total_files > 20:
                health_score -= 10
                issues.append("Mixed file types indicate poor organization")
                recommendations.append("Use the auto-organize feature to sort files by type")
            
            health_score = max(0, health_score)
            
            return {
                "health_score": health_score,
                "recommendations": recommendations[:3],  # Top 3 recommendations
                "issues": issues,
                "total_files_analyzed": total_files,
                "file_type_diversity": unique_types
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze folder health: {e}")
            return {
                "health_score": 50,
                "recommendations": ["Unable to analyze folder health"],
                "issues": ["Analysis failed"],
                "error": str(e)
            }
    
    def suggest_cleanup_actions(self, scan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest specific cleanup actions based on folder analysis
        """
        try:
            actions = []
            file_types = scan_result.get("file_types", {})
            largest_files = scan_result.get("largest_files", [])
            
            # Suggest organizing large file type groups
            for file_type, count in file_types.items():
                if count >= 10:
                    actions.append({
                        "type": "organize",
                        "description": f"Organize {count} {file_type.lower()} files into a dedicated folder",
                        "file_type": file_type,
                        "file_count": count,
                        "estimated_xp": count * 2
                    })
            
            # Suggest reviewing large files
            if largest_files:
                large_file_count = len([f for f in largest_files if f.size > 100 * 1024 * 1024])  # > 100MB
                if large_file_count > 0:
                    actions.append({
                        "type": "review_large_files",
                        "description": f"Review {large_file_count} large files to free up space",
                        "file_count": large_file_count,
                        "estimated_xp": large_file_count * 5
                    })
            
            return actions[:5]  # Return top 5 actions
            
        except Exception as e:
            logger.error(f"Failed to suggest cleanup actions: {e}")
            return []
    
    def get_smart_folder_names(self, file_type: FileType, files: List[FileInfo]) -> List[str]:
        """
        Generate smart folder names based on file analysis
        """
        try:
            if file_type == FileType.IMAGE:
                # Analyze image filenames for smart categorization
                if any('screenshot' in f.name.lower() for f in files):
                    return ['Screenshots', 'Photos', 'Images']
                elif any('wallpaper' in f.name.lower() for f in files):
                    return ['Wallpapers', 'Images', 'Pictures']
                else:
                    return ['Photos', 'Images', 'Pictures']
            
            elif file_type == FileType.DOCUMENT:
                if any('invoice' in f.name.lower() or 'receipt' in f.name.lower() for f in files):
                    return ['Financial Documents', 'Receipts', 'Documents']
                elif any('resume' in f.name.lower() or 'cv' in f.name.lower() for f in files):
                    return ['Career Documents', 'Resumes', 'Documents']
                else:
                    return ['Documents', 'Files', 'Papers']
            
            elif file_type == FileType.AUDIO:
                return ['Music', 'Audio', 'Sound Files']
            
            elif file_type == FileType.VIDEO:
                return ['Videos', 'Movies', 'Media']
            
            elif file_type == FileType.ARCHIVE:
                return ['Archives', 'Compressed Files', 'Backups']
            
            elif file_type == FileType.CODE:
                return ['Code', 'Development', 'Projects']
            
            else:
                return [file_type.value, 'Files']
                
        except Exception as e:
            logger.error(f"Failed to generate smart folder names: {e}")
            return [file_type.value]
