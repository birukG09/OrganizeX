import os
import shutil
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import json
from collections import defaultdict

from models import FileInfo, DuplicateGroup, ScanResult, OrganizationRule, get_file_type, FileType

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.supported_extensions = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
            'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
            'Presentations': ['.ppt', '.pptx', '.odp', '.key'],
            'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'Code': ['.js', '.py', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go'],
            'Executables': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.app'],
        }
        
        # Common folder mappings for different OS
        self.common_folders = {
            'downloads': self._get_downloads_folder(),
            'desktop': self._get_desktop_folder(),
            'documents': self._get_documents_folder(),
            'pictures': self._get_pictures_folder()
        }
    
    def _get_downloads_folder(self) -> str:
        """Get the downloads folder path for the current OS"""
        home = Path.home()
        downloads = home / "Downloads"
        if downloads.exists():
            return str(downloads)
        return str(home)
    
    def _get_desktop_folder(self) -> str:
        """Get the desktop folder path for the current OS"""
        home = Path.home()
        desktop = home / "Desktop"
        if desktop.exists():
            return str(desktop)
        return str(home)
    
    def _get_documents_folder(self) -> str:
        """Get the documents folder path for the current OS"""
        home = Path.home()
        documents = home / "Documents"
        if documents.exists():
            return str(documents)
        return str(home)
    
    def _get_pictures_folder(self) -> str:
        """Get the pictures folder path for the current OS"""
        home = Path.home()
        pictures = home / "Pictures"
        if pictures.exists():
            return str(pictures)
        return str(home)
    
    def _get_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of a file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    def _get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """Get detailed information about a file"""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists() or not path_obj.is_file():
                return None
            
            stat = path_obj.stat()
            return FileInfo(
                path=str(path_obj),
                name=path_obj.name,
                size=stat.st_size,
                type=get_file_type(path_obj.suffix).value,
                extension=path_obj.suffix.lower(),
                modified=datetime.fromtimestamp(stat.st_mtime),
                created=datetime.fromtimestamp(stat.st_ctime),
                hash=self._get_file_hash(file_path)
            )
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    def scan_folder(self, folder_path: str) -> Dict[str, Any]:
        """Scan a folder and return detailed analysis"""
        try:
            path_obj = Path(folder_path)
            
            # Handle common folder shortcuts
            if folder_path.lower() in self.common_folders:
                path_obj = Path(self.common_folders[folder_path.lower()])
            
            if not path_obj.exists():
                return {
                    "success": False,
                    "error": f"Folder does not exist: {folder_path}"
                }
            
            if not path_obj.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {folder_path}"
                }
            
            files = []
            file_types = defaultdict(int)
            total_size = 0
            folder_count = 0
            
            # Scan directory recursively
            for item in path_obj.rglob("*"):
                try:
                    if item.is_file():
                        file_info = self._get_file_info(str(item))
                        if file_info:
                            files.append(file_info)
                            file_types[file_info.type] += 1
                            total_size += file_info.size
                    elif item.is_dir():
                        folder_count += 1
                except PermissionError:
                    logger.warning(f"Permission denied accessing: {item}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing {item}: {e}")
                    continue
            
            # Sort files by size for largest files list
            largest_files = sorted(files, key=lambda x: x.size, reverse=True)[:10]
            
            return ScanResult(
                path=str(path_obj),
                total_files=len(files),
                total_folders=folder_count,
                total_size=total_size,
                file_types=dict(file_types),
                largest_files=largest_files,
                oldest_files=sorted(files, key=lambda x: x.modified)[:10],
                success=True
            ).__dict__
            
        except Exception as e:
            logger.error(f"Failed to scan folder {folder_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def organize_files(self, folder_path: str, rules: Dict[str, bool]) -> Dict[str, Any]:
        """Organize files based on the provided rules"""
        try:
            path_obj = Path(folder_path)
            
            # Handle common folder shortcuts
            if folder_path.lower() in self.common_folders:
                path_obj = Path(self.common_folders[folder_path.lower()])
            
            if not path_obj.exists() or not path_obj.is_dir():
                return {
                    "success": False,
                    "error": "Invalid folder path"
                }
            
            files_organized = 0
            errors = []
            
            # Get all files in the directory
            for item in path_obj.iterdir():
                try:
                    if not item.is_file():
                        continue
                    
                    file_type = get_file_type(item.suffix).value
                    
                    # Check if this file type should be organized
                    if not rules.get(file_type, False):
                        continue
                    
                    # Create target folder if it doesn't exist
                    target_folder = path_obj / file_type
                    target_folder.mkdir(exist_ok=True)
                    
                    # Move file to target folder
                    target_path = target_folder / item.name
                    
                    # Handle name conflicts
                    counter = 1
                    original_target = target_path
                    while target_path.exists():
                        stem = original_target.stem
                        suffix = original_target.suffix
                        target_path = target_folder / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(item), str(target_path))
                    files_organized += 1
                    
                except Exception as e:
                    error_msg = f"Failed to organize {item.name}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return {
                "success": True,
                "filesOrganized": files_organized,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to organize files in {folder_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def quick_sort_folder(self, folder_type: str) -> Dict[str, Any]:
        """Quick sort common folders"""
        try:
            if folder_type.lower() not in self.common_folders:
                return {
                    "success": False,
                    "error": f"Unknown folder type: {folder_type}"
                }
            
            folder_path = self.common_folders[folder_type.lower()]
            
            # Enable organization for all file types
            rules = {file_type: True for file_type in self.supported_extensions.keys()}
            
            result = self.organize_files(folder_path, rules)
            
            if result.get("success"):
                # Calculate XP based on files organized
                xp_gained = result.get("filesOrganized", 0) * 5
                result["xpGained"] = xp_gained
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to quick sort {folder_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def find_duplicates(self, scan_path: str) -> List[Dict[str, Any]]:
        """Find duplicate files in the given path"""
        try:
            path_obj = Path(scan_path)
            
            # Handle common folder shortcuts and root path
            if scan_path == "/":
                path_obj = Path.home()
            elif scan_path.lower() in self.common_folders:
                path_obj = Path(self.common_folders[scan_path.lower()])
            
            if not path_obj.exists():
                logger.error(f"Path does not exist: {scan_path}")
                return []
            
            # Dictionary to group files by hash
            hash_groups = defaultdict(list)
            
            # Scan for files and calculate hashes
            for item in path_obj.rglob("*"):
                try:
                    if item.is_file() and item.stat().st_size > 0:  # Skip empty files
                        file_info = self._get_file_info(str(item))
                        if file_info and file_info.hash:
                            hash_groups[file_info.hash].append(file_info)
                except (PermissionError, OSError) as e:
                    logger.warning(f"Cannot access {item}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing {item}: {e}")
                    continue
            
            # Filter groups with more than one file (duplicates)
            duplicate_groups = []
            group_id = 1
            
            for file_hash, file_list in hash_groups.items():
                if len(file_list) > 1:
                    # Sort files by modification date (oldest first)
                    sorted_files = sorted(file_list, key=lambda x: x.modified)
                    
                    duplicate_group = {
                        "id": str(group_id),
                        "name": sorted_files[0].name,
                        "files": [
                            {
                                "id": str(i),
                                "path": file_info.path,
                                "size": file_info.size,
                                "modified": file_info.modified.isoformat()
                            }
                            for i, file_info in enumerate(sorted_files)
                        ]
                    }
                    duplicate_groups.append(duplicate_group)
                    group_id += 1
            
            logger.info(f"Found {len(duplicate_groups)} groups of duplicate files")
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Failed to find duplicates in {scan_path}: {e}")
            return []
    
    def delete_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Delete specified files"""
        try:
            deleted_count = 0
            errors = []
            total_size_freed = 0
            
            for file_path in file_paths:
                try:
                    path_obj = Path(file_path)
                    if path_obj.exists() and path_obj.is_file():
                        file_size = path_obj.stat().st_size
                        path_obj.unlink()
                        deleted_count += 1
                        total_size_freed += file_size
                        logger.info(f"Deleted file: {file_path}")
                    else:
                        errors.append(f"File not found: {file_path}")
                except Exception as e:
                    error_msg = f"Failed to delete {file_path}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return {
                "success": True,
                "deletedCount": deleted_count,
                "totalSizeFreed": total_size_freed,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to delete files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        size_index = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and size_index < len(size_names) - 1:
            size /= 1024.0
            size_index += 1
        
        return f"{size:.1f} {size_names[size_index]}"
    
    def get_folder_stats(self, folder_path: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a folder"""
        try:
            scan_result = self.scan_folder(folder_path)
            
            if not scan_result.get("success"):
                return scan_result
            
            stats = {
                "totalFiles": scan_result["total_files"],
                "totalFolders": scan_result["total_folders"],
                "totalSize": self.format_file_size(scan_result["total_size"]),
                "fileTypes": scan_result["file_types"],
                "largestFiles": [
                    {
                        "name": f.name,
                        "size": self.format_file_size(f.size),
                        "path": f.path
                    }
                    for f in scan_result["largest_files"][:5]
                ]
            }
            
            return {
                "success": True,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get folder stats for {folder_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
