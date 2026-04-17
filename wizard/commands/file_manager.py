"""
File Manager Module for Wizard Voice Assistant

This module provides comprehensive file management capabilities including:
- File search and indexing
- File operations (CRUD)
- File type recognition
- Recent files tracking
"""

import os
import sys
import json
import shutil
import sqlite3
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import hashlib
import threading
import time

from ..utils.logger import WizardLogger


class FileManager:
    """
    Manages file operations and search functionality for the Wizard assistant.
    
    Provides file search, CRUD operations, type recognition, and recent files tracking.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the FileManager with configuration.
        
        Args:
            config: Configuration dictionary containing file manager settings
        """
        self.logger = WizardLogger("FileManager")
        self.config = config
        
        # Check if database should be enabled
        self.enable_database = config.get('enable_file_database', True)
        
        # Database for file indexing and recent files
        self.db_path = config.get('file_db_path', 'wizard/data/files.db') if self.enable_database else None
        self.search_paths = config.get('search_paths', [
            str(Path.home() / 'Documents'),
            str(Path.home() / 'Desktop'),
            str(Path.home() / 'Downloads')
        ])
        
        # File type categories
        self.file_categories = {
            'document': ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'code': ['.py', '.js', '.html', '.css', '.cpp', '.java', '.c'],
            'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
            'presentation': ['.ppt', '.pptx', '.odp']
        }
        
        # Initialize database and start indexing only if enabled
        if self.enable_database:
            self._init_database()
            self._start_background_indexing()
        else:
            self.logger.info("File manager running without database")
        
    def _init_database(self):
        """Initialize the SQLite database for file indexing."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Use timeout and WAL mode to prevent locks
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                
                cursor = conn.cursor()
                
                # File index table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_index (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT UNIQUE,
                        file_name TEXT,
                        file_size INTEGER,
                        file_type TEXT,
                        category TEXT,
                        modified_time TIMESTAMP,
                        indexed_time TIMESTAMP,
                        content_hash TEXT
                    )
                ''')
                
                # Recent files table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recent_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT,
                        access_time TIMESTAMP,
                        access_count INTEGER DEFAULT 1
                    )
                ''')
                
                # File content search table (for text files)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_content (
                        file_id INTEGER,
                        content_snippet TEXT,
                        FOREIGN KEY (file_id) REFERENCES file_index (id)
                    )
                ''')
                
                conn.commit()
                self.logger.info("File database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize file database: {e}")
            # Create a simple fallback without database
            self.db_path = None
    
    def _start_background_indexing(self):
        """Start background thread for file indexing."""
        def index_worker():
            while True:
                try:
                    if self.db_path:  # Only index if database is available
                        self._update_file_index()
                    time.sleep(300)  # Re-index every 5 minutes
                except Exception as e:
                    self.logger.debug(f"Background indexing skipped: {e}")
                    time.sleep(60)  # Wait 1 minute before retry
        
        indexing_thread = threading.Thread(target=index_worker, daemon=True)
        indexing_thread.start()
        self.logger.info("Background file indexing started")
    
    def _update_file_index(self):
        """Update the file index by scanning configured directories."""
        if not self.db_path:
            return  # Skip if no database
            
        try:
            # Use timeout and immediate return if database is busy
            with sqlite3.connect(self.db_path, timeout=1.0) as conn:
                conn.execute("PRAGMA busy_timeout = 1000")  # 1 second timeout
                cursor = conn.cursor()
                
                for search_path in self.search_paths:
                    if not os.path.exists(search_path):
                        continue
                        
                    for root, dirs, files in os.walk(search_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            
                            try:
                                # Get file stats
                                stat = os.stat(file_path)
                                modified_time = datetime.fromtimestamp(stat.st_mtime)
                                file_size = stat.st_size
                                
                                # Check if file is already indexed and up to date
                                cursor.execute(
                                    'SELECT modified_time FROM file_index WHERE file_path = ?',
                                    (file_path,)
                                )
                                result = cursor.fetchone()
                                
                                if result and datetime.fromisoformat(result[0]) >= modified_time:
                                    continue  # File hasn't changed
                                
                                # Get file info
                                file_ext = os.path.splitext(file)[1].lower()
                                file_type = mimetypes.guess_type(file_path)[0] or 'unknown'
                                category = self._get_file_category(file_ext)
                                
                                # Calculate content hash for change detection
                                content_hash = self._calculate_file_hash(file_path)
                                
                                # Insert or update file index
                                cursor.execute('''
                                    INSERT OR REPLACE INTO file_index 
                                    (file_path, file_name, file_size, file_type, category, 
                                     modified_time, indexed_time, content_hash)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    file_path, file, file_size, file_type, category,
                                    modified_time, datetime.now(), content_hash
                                ))
                                
                                # Index text content for searchable files
                                if category in ['document', 'code'] and file_size < 1024 * 1024:  # < 1MB
                                    self._index_file_content(cursor, file_path, cursor.lastrowid)
                                
                            except (OSError, PermissionError):
                                continue  # Skip files we can't access
                
                conn.commit()
                self.logger.debug("File index updated successfully")
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                self.logger.debug("Database busy, skipping this indexing cycle")
            else:
                self.logger.error(f"Database error during indexing: {e}")
        except Exception as e:
            self.logger.debug(f"Indexing skipped: {e}")
    
    def _get_file_category(self, file_ext: str) -> str:
        """Determine file category based on extension."""
        for category, extensions in self.file_categories.items():
            if file_ext in extensions:
                return category
        return 'other'
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for change detection."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _index_file_content(self, cursor, file_path: str, file_id: int):
        """Index text content of files for content search."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # Read first 10KB
                
            # Delete existing content for this file
            cursor.execute('DELETE FROM file_content WHERE file_id = ?', (file_id,))
            
            # Store content snippet
            if content.strip():
                cursor.execute(
                    'INSERT INTO file_content (file_id, content_snippet) VALUES (?, ?)',
                    (file_id, content[:1000])  # Store first 1000 chars
                )
                
        except Exception:
            pass  # Skip files we can't read as text   
 
    # File Search Methods
    
    def search_files(self, query: str, file_type: str = None, category: str = None, 
                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for files by name, type, or category.
        
        Args:
            query: Search query (file name or partial name)
            file_type: Specific file type to filter by
            category: File category to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build search query
                sql = '''
                    SELECT file_path, file_name, file_size, file_type, category, 
                           modified_time, indexed_time
                    FROM file_index 
                    WHERE file_name LIKE ?
                '''
                params = [f'%{query}%']
                
                if file_type:
                    sql += ' AND file_type = ?'
                    params.append(file_type)
                
                if category:
                    sql += ' AND category = ?'
                    params.append(category)
                
                sql += ' ORDER BY modified_time DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                # Format results
                files = []
                for row in results:
                    files.append({
                        'path': row[0],
                        'name': row[1],
                        'size': row[2],
                        'type': row[3],
                        'category': row[4],
                        'modified': row[5],
                        'indexed': row[6]
                    })
                
                self.logger.info(f"Found {len(files)} files matching '{query}'")
                return files
                
        except Exception as e:
            self.logger.error(f"File search failed: {e}")
            return []
    
    def search_by_content(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for files by content.
        
        Args:
            query: Text to search for in file content
            limit: Maximum number of results to return
            
        Returns:
            List of file information dictionaries with content matches
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql = '''
                    SELECT fi.file_path, fi.file_name, fi.file_size, fi.file_type, 
                           fi.category, fi.modified_time, fc.content_snippet
                    FROM file_index fi
                    JOIN file_content fc ON fi.id = fc.file_id
                    WHERE fc.content_snippet LIKE ?
                    ORDER BY fi.modified_time DESC
                    LIMIT ?
                '''
                
                cursor.execute(sql, [f'%{query}%', limit])
                results = cursor.fetchall()
                
                files = []
                for row in results:
                    files.append({
                        'path': row[0],
                        'name': row[1],
                        'size': row[2],
                        'type': row[3],
                        'category': row[4],
                        'modified': row[5],
                        'content_snippet': row[6]
                    })
                
                self.logger.info(f"Found {len(files)} files with content matching '{query}'")
                return files
                
        except Exception as e:
            self.logger.error(f"Content search failed: {e}")
            return []
    
    def get_files_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get files by category.
        
        Args:
            category: File category (document, image, video, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT file_path, file_name, file_size, file_type, category, modified_time
                    FROM file_index 
                    WHERE category = ?
                    ORDER BY modified_time DESC
                    LIMIT ?
                ''', [category, limit])
                
                results = cursor.fetchall()
                
                files = []
                for row in results:
                    files.append({
                        'path': row[0],
                        'name': row[1],
                        'size': row[2],
                        'type': row[3],
                        'category': row[4],
                        'modified': row[5]
                    })
                
                self.logger.info(f"Found {len(files)} {category} files")
                return files
                
        except Exception as e:
            self.logger.error(f"Category search failed: {e}")
            return []
    
    def get_recent_files(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recently accessed files.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of recently accessed file information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT rf.file_path, rf.access_time, rf.access_count,
                           fi.file_name, fi.file_size, fi.file_type, fi.category
                    FROM recent_files rf
                    LEFT JOIN file_index fi ON rf.file_path = fi.file_path
                    ORDER BY rf.access_time DESC
                    LIMIT ?
                ''', [limit])
                
                results = cursor.fetchall()
                
                files = []
                for row in results:
                    if os.path.exists(row[0]):  # Only include existing files
                        files.append({
                            'path': row[0],
                            'access_time': row[1],
                            'access_count': row[2],
                            'name': row[3] or os.path.basename(row[0]),
                            'size': row[4] or 0,
                            'type': row[5] or 'unknown',
                            'category': row[6] or 'other'
                        })
                
                self.logger.info(f"Retrieved {len(files)} recent files")
                return files
                
        except Exception as e:
            self.logger.error(f"Recent files retrieval failed: {e}")
            return []
    
    def track_file_access(self, file_path: str):
        """
        Track file access for recent files functionality.
        
        Args:
            file_path: Path to the accessed file
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if file is already tracked
                cursor.execute(
                    'SELECT access_count FROM recent_files WHERE file_path = ?',
                    [file_path]
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing record
                    cursor.execute('''
                        UPDATE recent_files 
                        SET access_time = ?, access_count = access_count + 1
                        WHERE file_path = ?
                    ''', [datetime.now(), file_path])
                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO recent_files (file_path, access_time, access_count)
                        VALUES (?, ?, 1)
                    ''', [file_path, datetime.now()])
                
                conn.commit()
                
                # Clean up old entries (keep only last 100)
                cursor.execute('''
                    DELETE FROM recent_files 
                    WHERE id NOT IN (
                        SELECT id FROM recent_files 
                        ORDER BY access_time DESC 
                        LIMIT 100
                    )
                ''')
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to track file access: {e}")
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File information dictionary or None if not found
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            # Get file stats
            stat = os.stat(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'type': mimetypes.guess_type(file_path)[0] or 'unknown',
                'category': self._get_file_category(file_ext),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'extension': file_ext,
                'is_hidden': os.path.basename(file_path).startswith('.'),
                'is_readonly': not os.access(file_path, os.W_OK)
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get file info for {file_path}: {e}")
            return None 
   
    # File Operation Methods
    
    def create_file(self, file_path: str, content: str = "", overwrite: bool = False) -> bool:
        """
        Create a new file with optional content.
        
        Args:
            file_path: Path where the file should be created
            content: Initial content for the file
            overwrite: Whether to overwrite existing files
            
        Returns:
            True if file was created successfully, False otherwise
        """
        try:
            # Check if file already exists
            if os.path.exists(file_path) and not overwrite:
                self.logger.warning(f"File already exists: {file_path}")
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"File created successfully: {file_path}")
            self.track_file_access(file_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create file {file_path}: {e}")
            return False
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        Read content from a file.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string or None if failed
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.info(f"File read successfully: {file_path}")
            self.track_file_access(file_path)
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def update_file(self, file_path: str, content: str, backup: bool = True) -> bool:
        """
        Update an existing file with new content.
        
        Args:
            file_path: Path to the file to update
            content: New content for the file
            backup: Whether to create a backup before updating
            
        Returns:
            True if file was updated successfully, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found for update: {file_path}")
                return False
            
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.backup_{int(datetime.now().timestamp())}"
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"Backup created: {backup_path}")
            
            # Update the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"File updated successfully: {file_path}")
            self.track_file_access(file_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update file {file_path}: {e}")
            return False
    
    def delete_file(self, file_path: str, confirm: bool = True, 
                   move_to_trash: bool = True) -> bool:
        """
        Delete a file with safety checks.
        
        Args:
            file_path: Path to the file to delete
            confirm: Whether confirmation is required (for safety)
            move_to_trash: Whether to move to trash instead of permanent deletion
            
        Returns:
            True if file was deleted successfully, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found for deletion: {file_path}")
                return False
            
            # Safety check for important files
            if self._is_important_file(file_path) and confirm:
                self.logger.warning(f"Attempted to delete important file: {file_path}")
                return False
            
            if move_to_trash:
                # Move to trash/recycle bin (simplified implementation)
                trash_dir = os.path.join(os.path.expanduser("~"), ".trash")
                os.makedirs(trash_dir, exist_ok=True)
                
                trash_path = os.path.join(trash_dir, 
                                        f"{os.path.basename(file_path)}.{int(datetime.now().timestamp())}")
                shutil.move(file_path, trash_path)
                self.logger.info(f"File moved to trash: {file_path} -> {trash_path}")
            else:
                # Permanent deletion
                os.remove(file_path)
                self.logger.info(f"File permanently deleted: {file_path}")
            
            # Remove from recent files
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM recent_files WHERE file_path = ?', [file_path])
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def copy_file(self, source_path: str, destination_path: str, 
                 overwrite: bool = False, confirm: bool = True) -> bool:
        """
        Copy a file to a new location.
        
        Args:
            source_path: Path to the source file
            destination_path: Path where the file should be copied
            overwrite: Whether to overwrite existing files
            confirm: Whether confirmation is required for overwriting
            
        Returns:
            True if file was copied successfully, False otherwise
        """
        try:
            if not os.path.exists(source_path):
                self.logger.warning(f"Source file not found: {source_path}")
                return False
            
            # Check if destination exists and handle confirmation
            if os.path.exists(destination_path):
                if not overwrite:
                    self.logger.warning(f"Destination file already exists: {destination_path}")
                    return False
                if confirm and self._is_important_file(destination_path):
                    self.logger.warning(f"Attempted to overwrite important file without confirmation: {destination_path}")
                    return False
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, destination_path)
            
            self.logger.info(f"File copied: {source_path} -> {destination_path}")
            self.track_file_access(destination_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy file {source_path} to {destination_path}: {e}")
            return False
    
    def move_file(self, source_path: str, destination_path: str, 
                 overwrite: bool = False, confirm: bool = True) -> bool:
        """
        Move a file to a new location.
        
        Args:
            source_path: Path to the source file
            destination_path: Path where the file should be moved
            overwrite: Whether to overwrite existing files
            confirm: Whether confirmation is required for overwriting
            
        Returns:
            True if file was moved successfully, False otherwise
        """
        try:
            if not os.path.exists(source_path):
                self.logger.warning(f"Source file not found: {source_path}")
                return False
            
            # Check if destination exists and handle confirmation
            if os.path.exists(destination_path):
                if not overwrite:
                    self.logger.warning(f"Destination file already exists: {destination_path}")
                    return False
                if confirm and self._is_important_file(destination_path):
                    self.logger.warning(f"Attempted to overwrite important file without confirmation: {destination_path}")
                    return False
            
            # Safety check for moving important files
            if confirm and self._is_important_file(source_path):
                self.logger.warning(f"Attempted to move important file without confirmation: {source_path}")
                return False
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            # Move the file
            shutil.move(source_path, destination_path)
            
            self.logger.info(f"File moved: {source_path} -> {destination_path}")
            
            # Update recent files tracking
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE recent_files 
                    SET file_path = ? 
                    WHERE file_path = ?
                ''', [destination_path, source_path])
                conn.commit()
            
            self.track_file_access(destination_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move file {source_path} to {destination_path}: {e}")
            return False
    
    def rename_file(self, file_path: str, new_name: str, confirm: bool = True) -> bool:
        """
        Rename a file.
        
        Args:
            file_path: Path to the file to rename
            new_name: New name for the file
            confirm: Whether confirmation is required for important files
            
        Returns:
            True if file was renamed successfully, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found for rename: {file_path}")
                return False
            
            # Safety check for renaming important files
            if confirm and self._is_important_file(file_path):
                self.logger.warning(f"Attempted to rename important file without confirmation: {file_path}")
                return False
            
            directory = os.path.dirname(file_path)
            new_path = os.path.join(directory, new_name)
            
            # Check if destination exists
            if os.path.exists(new_path):
                if confirm and self._is_important_file(new_path):
                    self.logger.warning(f"Attempted to overwrite important file without confirmation: {new_path}")
                    return False
                self.logger.warning(f"File with new name already exists: {new_path}")
                return False
            
            # Rename the file
            os.rename(file_path, new_path)
            
            self.logger.info(f"File renamed: {file_path} -> {new_path}")
            
            # Update recent files tracking
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE recent_files 
                    SET file_path = ? 
                    WHERE file_path = ?
                ''', [new_path, file_path])
                conn.commit()
            
            self.track_file_access(new_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rename file {file_path} to {new_name}: {e}")
            return False
    
    def create_folder(self, folder_path: str, parents: bool = True) -> bool:
        """
        Create a new folder.
        
        Args:
            folder_path: Path where the folder should be created
            parents: Whether to create parent directories if they don't exist
            
        Returns:
            True if folder was created successfully, False otherwise
        """
        try:
            if os.path.exists(folder_path):
                self.logger.warning(f"Folder already exists: {folder_path}")
                return False
            
            if parents:
                os.makedirs(folder_path, exist_ok=True)
            else:
                os.mkdir(folder_path)
            
            self.logger.info(f"Folder created successfully: {folder_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create folder {folder_path}: {e}")
            return False
    
    def delete_folder(self, folder_path: str, confirm: bool = True, 
                     recursive: bool = False) -> bool:
        """
        Delete a folder with safety checks.
        
        Args:
            folder_path: Path to the folder to delete
            confirm: Whether confirmation is required (for safety)
            recursive: Whether to delete folder contents recursively
            
        Returns:
            True if folder was deleted successfully, False otherwise
        """
        try:
            if not os.path.exists(folder_path):
                self.logger.warning(f"Folder not found for deletion: {folder_path}")
                return False
            
            if not os.path.isdir(folder_path):
                self.logger.warning(f"Path is not a folder: {folder_path}")
                return False
            
            # Safety check for important folders
            if self._is_important_folder(folder_path) and confirm:
                self.logger.warning(f"Attempted to delete important folder: {folder_path}")
                return False
            
            if recursive:
                shutil.rmtree(folder_path)
                self.logger.info(f"Folder and contents deleted: {folder_path}")
            else:
                os.rmdir(folder_path)  # Only works if folder is empty
                self.logger.info(f"Empty folder deleted: {folder_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete folder {folder_path}: {e}")
            return False
    
    def open_file(self, file_path: str) -> bool:
        """
        Open a file with the default system application.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            True if file was opened successfully, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return False
            
            # Track file access
            self.track_file_access(file_path)
            
            # Open with default application
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                import subprocess
                subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', file_path])
            
            self.logger.info(f"File opened: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open file {file_path}: {e}")
            return False
    
    def _is_important_file(self, file_path: str) -> bool:
        """
        Check if a file is considered important and should be protected.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is important, False otherwise
        """
        important_patterns = [
            '*.exe', '*.dll', '*.sys', '*.ini',  # System files
            'config.*', 'settings.*',  # Configuration files
            '*.key', '*.pem', '*.cert',  # Security files
        ]
        
        file_name = os.path.basename(file_path).lower()
        
        for pattern in important_patterns:
            if file_name.endswith(pattern.replace('*', '')):
                return True
        
        return False
    
    def _is_important_folder(self, folder_path: str) -> bool:
        """
        Check if a folder is considered important and should be protected.
        
        Args:
            folder_path: Path to check
            
        Returns:
            True if folder is important, False otherwise
        """
        important_folders = [
            'system32', 'windows', 'program files', 'program files (x86)',
            'users', 'documents', 'desktop', 'downloads'
        ]
        
        folder_name = os.path.basename(folder_path).lower()
        
        return folder_name in important_folders or folder_path in [
            os.path.expanduser("~"),  # Home directory
            "C:\\",  # Root drive
            "/",  # Unix root
        ]
    
    def batch_file_operation(self, operation: str, file_paths: List[str], 
                           destination: str = None, confirm: bool = True) -> Dict[str, bool]:
        """
        Perform batch file operations on multiple files.
        
        Args:
            operation: Operation to perform ('copy', 'move', 'delete')
            file_paths: List of file paths to operate on
            destination: Destination directory for copy/move operations
            confirm: Whether confirmation is required for destructive operations
            
        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        
        for file_path in file_paths:
            try:
                if operation == 'delete':
                    results[file_path] = self.delete_file(file_path, confirm=confirm)
                elif operation == 'copy' and destination:
                    dest_path = os.path.join(destination, os.path.basename(file_path))
                    results[file_path] = self.copy_file(file_path, dest_path, confirm=confirm)
                elif operation == 'move' and destination:
                    dest_path = os.path.join(destination, os.path.basename(file_path))
                    results[file_path] = self.move_file(file_path, dest_path, confirm=confirm)
                else:
                    results[file_path] = False
                    self.logger.warning(f"Invalid batch operation: {operation}")
                    
            except Exception as e:
                self.logger.error(f"Batch operation {operation} failed for {file_path}: {e}")
                results[file_path] = False
        
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"Batch {operation} completed: {successful}/{len(file_paths)} successful")
        
        return results
    
    def get_folder_contents(self, folder_path: str, recursive: bool = False, 
                          file_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get contents of a folder with optional filtering.
        
        Args:
            folder_path: Path to the folder
            recursive: Whether to include subdirectories recursively
            file_types: List of file extensions to filter by
            
        Returns:
            List of file and folder information dictionaries
        """
        try:
            if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
                self.logger.warning(f"Folder not found or not a directory: {folder_path}")
                return []
            
            contents = []
            
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    # Add directories
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        contents.append({
                            'path': dir_path,
                            'name': dir_name,
                            'type': 'directory',
                            'size': 0,
                            'modified': datetime.fromtimestamp(os.path.getmtime(dir_path))
                        })
                    
                    # Add files
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        file_ext = os.path.splitext(file_name)[1].lower()
                        
                        # Filter by file types if specified
                        if file_types and file_ext not in file_types:
                            continue
                        
                        try:
                            stat = os.stat(file_path)
                            contents.append({
                                'path': file_path,
                                'name': file_name,
                                'type': 'file',
                                'size': stat.st_size,
                                'extension': file_ext,
                                'category': self._get_file_category(file_ext),
                                'modified': datetime.fromtimestamp(stat.st_mtime)
                            })
                        except OSError:
                            continue  # Skip files we can't access
            else:
                # Non-recursive listing
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    
                    try:
                        if os.path.isdir(item_path):
                            contents.append({
                                'path': item_path,
                                'name': item,
                                'type': 'directory',
                                'size': 0,
                                'modified': datetime.fromtimestamp(os.path.getmtime(item_path))
                            })
                        else:
                            file_ext = os.path.splitext(item)[1].lower()
                            
                            # Filter by file types if specified
                            if file_types and file_ext not in file_types:
                                continue
                            
                            stat = os.stat(item_path)
                            contents.append({
                                'path': item_path,
                                'name': item,
                                'type': 'file',
                                'size': stat.st_size,
                                'extension': file_ext,
                                'category': self._get_file_category(file_ext),
                                'modified': datetime.fromtimestamp(stat.st_mtime)
                            })
                    except OSError:
                        continue  # Skip items we can't access
            
            # Sort by name
            contents.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
            
            self.logger.info(f"Retrieved {len(contents)} items from {folder_path}")
            return contents
            
        except Exception as e:
            self.logger.error(f"Failed to get folder contents for {folder_path}: {e}")
            return []