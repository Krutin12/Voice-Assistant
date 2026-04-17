"""
Productivity Manager Module

This module handles timers, reminders, alarms, notes, and task management
for the Wizard AI Voice Assistant.
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Timer:
    """Represents a countdown timer"""
    id: str
    label: str
    duration_seconds: int
    start_time: datetime
    end_time: datetime
    is_active: bool = True
    is_completed: bool = False


@dataclass
class Reminder:
    """Represents a scheduled reminder"""
    id: str
    content: str
    scheduled_time: datetime
    created_time: datetime
    is_active: bool = True
    is_completed: bool = False
    repeat_interval: Optional[str] = None  # daily, weekly, monthly


@dataclass
class Alarm:
    """Represents an alarm"""
    id: str
    label: str
    time: str  # HH:MM format
    days: List[str]  # ['monday', 'tuesday', etc.]
    sound_file: Optional[str] = None
    snooze_duration: int = 5  # minutes
    is_active: bool = True


@dataclass
class Note:
    """Represents a note"""
    id: str
    title: str
    content: str
    created_time: datetime
    modified_time: datetime
    tags: List[str] = None
    file_path: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TodoItem:
    """Represents a todo list item"""
    id: str
    content: str
    created_time: datetime
    due_date: Optional[datetime] = None
    priority: str = "normal"  # low, normal, high
    is_completed: bool = False
    completed_time: Optional[datetime] = None


class ProductivityManager:
    """
    Manages timers, reminders, alarms, notes, and todo lists
    """

    def __init__(self, data_dir: str = "wizard/data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "productivity.db")
        self.notes_dir = os.path.join(data_dir, "notes")
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.notes_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Active timers and reminders
        self.active_timers: Dict[str, Timer] = {}
        self.active_reminders: Dict[str, Reminder] = {}
        self.active_alarms: Dict[str, Alarm] = {}
        
        # Background threads
        self.timer_thread = None
        self.reminder_thread = None
        self.alarm_thread = None
        self.running = False
        
        # ID counter for unique IDs
        self._id_counter = int(time.time() * 1000)  # Use milliseconds for uniqueness
        
        # Load existing data
        self._load_active_items()
        
        # Start background monitoring
        self.start_monitoring()

    def _get_unique_id(self, prefix: str) -> str:
        """Generate a unique ID with the given prefix"""
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    def _close_db_connections(self):
        """Close any open database connections"""
        # This helps with cleanup on Windows
        pass

    def _init_database(self):
        """Initialize SQLite database for productivity data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Timers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timers (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    is_completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Reminders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    created_time TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    is_completed BOOLEAN DEFAULT 0,
                    repeat_interval TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Alarms table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alarms (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    time TEXT NOT NULL,
                    days TEXT NOT NULL,
                    sound_file TEXT,
                    snooze_duration INTEGER DEFAULT 5,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Notes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_time TEXT NOT NULL,
                    modified_time TEXT NOT NULL,
                    tags TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Todo items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS todo_items (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_time TEXT NOT NULL,
                    due_date TEXT,
                    priority TEXT DEFAULT 'normal',
                    is_completed BOOLEAN DEFAULT 0,
                    completed_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def _load_active_items(self):
        """Load active timers, reminders, and alarms from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Load active timers
            cursor.execute('''
                SELECT * FROM timers 
                WHERE is_active = 1 AND is_completed = 0
            ''')
            for row in cursor.fetchall():
                timer = Timer(
                    id=row[0],
                    label=row[1],
                    duration_seconds=row[2],
                    start_time=datetime.fromisoformat(row[3]),
                    end_time=datetime.fromisoformat(row[4]),
                    is_active=bool(row[5]),
                    is_completed=bool(row[6])
                )
                self.active_timers[timer.id] = timer
            
            # Load active reminders
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE is_active = 1 AND is_completed = 0
            ''')
            for row in cursor.fetchall():
                reminder = Reminder(
                    id=row[0],
                    content=row[1],
                    scheduled_time=datetime.fromisoformat(row[2]),
                    created_time=datetime.fromisoformat(row[3]),
                    is_active=bool(row[4]),
                    is_completed=bool(row[5]),
                    repeat_interval=row[6]
                )
                self.active_reminders[reminder.id] = reminder
            
            # Load active alarms
            cursor.execute('''
                SELECT * FROM alarms 
                WHERE is_active = 1
            ''')
            for row in cursor.fetchall():
                alarm = Alarm(
                    id=row[0],
                    label=row[1],
                    time=row[2],
                    days=json.loads(row[3]),
                    sound_file=row[4],
                    snooze_duration=row[5],
                    is_active=bool(row[6])
                )
                self.active_alarms[alarm.id] = alarm

    def start_monitoring(self):
        """Start background threads for monitoring timers, reminders, and alarms"""
        if self.running:
            return
        
        self.running = True
        
        # Start timer monitoring thread
        self.timer_thread = threading.Thread(target=self._monitor_timers, daemon=True)
        self.timer_thread.start()
        
        # Start reminder monitoring thread
        self.reminder_thread = threading.Thread(target=self._monitor_reminders, daemon=True)
        self.reminder_thread.start()
        
        # Start alarm monitoring thread
        self.alarm_thread = threading.Thread(target=self._monitor_alarms, daemon=True)
        self.alarm_thread.start()
        
        logger.info("Started productivity monitoring threads")

    def stop_monitoring(self):
        """Stop background monitoring threads"""
        self.running = False
        self._close_db_connections()
        logger.info("Stopped productivity monitoring threads")

    def _monitor_timers(self):
        """Background thread to monitor active timers"""
        while self.running:
            try:
                current_time = datetime.now()
                completed_timers = []
                
                for timer_id, timer in self.active_timers.items():
                    if current_time >= timer.end_time and timer.is_active:
                        # Timer completed
                        timer.is_completed = True
                        timer.is_active = False
                        completed_timers.append(timer_id)
                        
                        # Update database
                        self._update_timer_status(timer_id, is_completed=True, is_active=False)
                        
                        # Trigger notification (this would integrate with TTS)
                        self._trigger_timer_notification(timer)
                
                # Remove completed timers from active list
                for timer_id in completed_timers:
                    del self.active_timers[timer_id]
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in timer monitoring: {e}")
                time.sleep(5)

    def _monitor_reminders(self):
        """Background thread to monitor active reminders"""
        while self.running:
            try:
                current_time = datetime.now()
                triggered_reminders = []
                
                for reminder_id, reminder in self.active_reminders.items():
                    if current_time >= reminder.scheduled_time and reminder.is_active:
                        # Reminder triggered
                        triggered_reminders.append(reminder_id)
                        
                        # Trigger notification
                        self._trigger_reminder_notification(reminder)
                        
                        # Handle repeat intervals
                        if reminder.repeat_interval:
                            self._schedule_repeat_reminder(reminder)
                        else:
                            reminder.is_completed = True
                            reminder.is_active = False
                            self._update_reminder_status(reminder_id, is_completed=True, is_active=False)
                
                # Remove non-repeating completed reminders
                for reminder_id in triggered_reminders:
                    reminder = self.active_reminders[reminder_id]
                    if not reminder.repeat_interval:
                        del self.active_reminders[reminder_id]
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in reminder monitoring: {e}")
                time.sleep(60)

    def _monitor_alarms(self):
        """Background thread to monitor active alarms"""
        while self.running:
            try:
                current_time = datetime.now()
                current_day = current_time.strftime('%A').lower()
                current_time_str = current_time.strftime('%H:%M')
                
                for alarm in self.active_alarms.values():
                    if (alarm.is_active and 
                        current_day in [day.lower() for day in alarm.days] and
                        current_time_str == alarm.time):
                        
                        # Trigger alarm
                        self._trigger_alarm_notification(alarm)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in alarm monitoring: {e}")
                time.sleep(60)

    def set_timer(self, duration: int, unit: str, label: str = "") -> str:
        """
        Set a countdown timer
        
        Args:
            duration: Timer duration
            unit: Time unit (seconds, minutes, hours)
            label: Optional label for the timer
            
        Returns:
            Timer ID
        """
        # Convert to seconds
        if unit.lower() in ['second', 'seconds']:
            duration_seconds = duration
        elif unit.lower() in ['minute', 'minutes']:
            duration_seconds = duration * 60
        elif unit.lower() in ['hour', 'hours']:
            duration_seconds = duration * 3600
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
        
        # Create timer
        timer_id = self._get_unique_id("timer")
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        timer = Timer(
            id=timer_id,
            label=label or f"{duration} {unit} timer",
            duration_seconds=duration_seconds,
            start_time=start_time,
            end_time=end_time
        )
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO timers (id, label, duration_seconds, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                timer.id,
                timer.label,
                timer.duration_seconds,
                timer.start_time.isoformat(),
                timer.end_time.isoformat()
            ))
            conn.commit()
        
        # Add to active timers
        self.active_timers[timer_id] = timer
        
        logger.info(f"Set timer: {timer.label} for {duration} {unit}")
        return timer_id

    def create_reminder(self, content: str, scheduled_time: datetime, repeat_interval: Optional[str] = None) -> str:
        """
        Create a reminder
        
        Args:
            content: Reminder content
            scheduled_time: When to trigger the reminder
            repeat_interval: Optional repeat interval (daily, weekly, monthly)
            
        Returns:
            Reminder ID
        """
        reminder_id = self._get_unique_id("reminder")
        created_time = datetime.now()
        
        reminder = Reminder(
            id=reminder_id,
            content=content,
            scheduled_time=scheduled_time,
            created_time=created_time,
            repeat_interval=repeat_interval
        )
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (id, content, scheduled_time, created_time, repeat_interval)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                reminder.id,
                reminder.content,
                reminder.scheduled_time.isoformat(),
                reminder.created_time.isoformat(),
                reminder.repeat_interval
            ))
            conn.commit()
        
        # Add to active reminders
        self.active_reminders[reminder_id] = reminder
        
        logger.info(f"Created reminder: {content} for {scheduled_time}")
        return reminder_id

    def create_alarm(self, label: str, time_str: str, days: List[str], sound_file: Optional[str] = None) -> str:
        """
        Create an alarm
        
        Args:
            label: Alarm label
            time_str: Time in HH:MM format
            days: List of days (monday, tuesday, etc.)
            sound_file: Optional custom sound file
            
        Returns:
            Alarm ID
        """
        alarm_id = self._get_unique_id("alarm")
        
        alarm = Alarm(
            id=alarm_id,
            label=label,
            time=time_str,
            days=days,
            sound_file=sound_file
        )
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alarms (id, label, time, days, sound_file)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                alarm.id,
                alarm.label,
                alarm.time,
                json.dumps(alarm.days),
                alarm.sound_file
            ))
            conn.commit()
        
        # Add to active alarms
        self.active_alarms[alarm_id] = alarm
        
        logger.info(f"Created alarm: {label} for {time_str} on {', '.join(days)}")
        return alarm_id

    def _trigger_timer_notification(self, timer: Timer):
        """Trigger notification when timer completes"""
        message = f"Timer completed: {timer.label}"
        logger.info(message)
        # This would integrate with the TTS system to speak the notification
        # For now, we'll just log it

    def _trigger_reminder_notification(self, reminder: Reminder):
        """Trigger notification for reminder"""
        message = f"Reminder: {reminder.content}"
        logger.info(message)
        # This would integrate with the TTS system to speak the notification

    def _trigger_alarm_notification(self, alarm: Alarm):
        """Trigger notification for alarm"""
        message = f"Alarm: {alarm.label}"
        logger.info(message)
        # This would integrate with the TTS system and play alarm sound

    def _update_timer_status(self, timer_id: str, is_completed: bool = None, is_active: bool = None):
        """Update timer status in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            updates = []
            values = []
            
            if is_completed is not None:
                updates.append("is_completed = ?")
                values.append(is_completed)
            
            if is_active is not None:
                updates.append("is_active = ?")
                values.append(is_active)
            
            if updates:
                values.append(timer_id)
                cursor.execute(f'''
                    UPDATE timers SET {', '.join(updates)}
                    WHERE id = ?
                ''', values)
                conn.commit()

    def _update_reminder_status(self, reminder_id: str, is_completed: bool = None, is_active: bool = None):
        """Update reminder status in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            updates = []
            values = []
            
            if is_completed is not None:
                updates.append("is_completed = ?")
                values.append(is_completed)
            
            if is_active is not None:
                updates.append("is_active = ?")
                values.append(is_active)
            
            if updates:
                values.append(reminder_id)
                cursor.execute(f'''
                    UPDATE reminders SET {', '.join(updates)}
                    WHERE id = ?
                ''', values)
                conn.commit()

    def _schedule_repeat_reminder(self, reminder: Reminder):
        """Schedule the next occurrence of a repeating reminder"""
        if reminder.repeat_interval == "daily":
            next_time = reminder.scheduled_time + timedelta(days=1)
        elif reminder.repeat_interval == "weekly":
            next_time = reminder.scheduled_time + timedelta(weeks=1)
        elif reminder.repeat_interval == "monthly":
            next_time = reminder.scheduled_time + timedelta(days=30)  # Approximate
        else:
            return
        
        # Update the reminder's scheduled time
        reminder.scheduled_time = next_time
        
        # Update in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reminders SET scheduled_time = ?
                WHERE id = ?
            ''', (next_time.isoformat(), reminder.id))
            conn.commit()

    def get_active_timers(self) -> List[Dict[str, Any]]:
        """Get list of active timers"""
        timers = []
        for timer in self.active_timers.values():
            remaining_seconds = (timer.end_time - datetime.now()).total_seconds()
            timers.append({
                "id": timer.id,
                "label": timer.label,
                "remaining_seconds": max(0, int(remaining_seconds)),
                "end_time": timer.end_time.isoformat()
            })
        return timers

    def get_active_reminders(self) -> List[Dict[str, Any]]:
        """Get list of active reminders"""
        reminders = []
        for reminder in self.active_reminders.values():
            reminders.append({
                "id": reminder.id,
                "content": reminder.content,
                "scheduled_time": reminder.scheduled_time.isoformat(),
                "repeat_interval": reminder.repeat_interval
            })
        return reminders

    def cancel_timer(self, timer_id: str) -> bool:
        """Cancel an active timer"""
        if timer_id in self.active_timers:
            self._update_timer_status(timer_id, is_active=False)
            del self.active_timers[timer_id]
            logger.info(f"Cancelled timer: {timer_id}")
            return True
        return False

    def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel an active reminder"""
        if reminder_id in self.active_reminders:
            self._update_reminder_status(reminder_id, is_active=False)
            del self.active_reminders[reminder_id]
            logger.info(f"Cancelled reminder: {reminder_id}")
            return True
        return False

    # Note-taking and task management methods

    def save_note(self, title: str, content: str, tags: List[str] = None) -> str:
        """
        Save a note with voice-to-text content
        
        Args:
            title: Note title
            content: Note content
            tags: Optional tags for categorization
            
        Returns:
            Note ID
        """
        note_id = self._get_unique_id("note")
        created_time = datetime.now()
        
        # Create file path
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        file_name = f"{safe_title}_{note_id}.txt"
        file_path = os.path.join(self.notes_dir, file_name)
        
        note = Note(
            id=note_id,
            title=title,
            content=content,
            created_time=created_time,
            modified_time=created_time,
            tags=tags or [],
            file_path=file_path
        )
        
        # Save note to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if tags:
                    f.write(f"Tags: {', '.join(tags)}\n")
                f.write("\n" + content)
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notes (id, title, content, created_time, modified_time, tags, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    note.id,
                    note.title,
                    note.content,
                    note.created_time.isoformat(),
                    note.modified_time.isoformat(),
                    json.dumps(note.tags),
                    note.file_path
                ))
                conn.commit()
            
            logger.info(f"Saved note: {title}")
            return note_id
            
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            raise

    def get_notes(self, search_query: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve notes with optional search and tag filtering
        
        Args:
            search_query: Optional search query for title/content
            tags: Optional list of tags to filter by
            
        Returns:
            List of note dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM notes"
            conditions = []
            params = []
            
            if search_query:
                conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([f"%{search_query}%", f"%{search_query}%"])
            
            if tags:
                # Simple tag matching - could be improved
                for tag in tags:
                    conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_time DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            notes = []
            for row in rows:
                notes.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "created_time": row[3],
                    "modified_time": row[4],
                    "tags": json.loads(row[5]) if row[5] else [],
                    "file_path": row[6]
                })
            
            return notes

    def update_note(self, note_id: str, title: str = None, content: str = None, tags: List[str] = None) -> bool:
        """
        Update an existing note
        
        Args:
            note_id: Note ID to update
            title: New title (optional)
            content: New content (optional)
            tags: New tags (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current note
                cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                # Update fields
                new_title = title if title is not None else row[1]
                new_content = content if content is not None else row[2]
                new_tags = tags if tags is not None else json.loads(row[5]) if row[5] else []
                modified_time = datetime.now()
                
                # Update database
                cursor.execute('''
                    UPDATE notes 
                    SET title = ?, content = ?, modified_time = ?, tags = ?
                    WHERE id = ?
                ''', (
                    new_title,
                    new_content,
                    modified_time.isoformat(),
                    json.dumps(new_tags),
                    note_id
                ))
                
                # Update file if it exists
                file_path = row[6]
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {new_title}\n")
                        f.write(f"Created: {row[3]}\n")
                        f.write(f"Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        if new_tags:
                            f.write(f"Tags: {', '.join(new_tags)}\n")
                        f.write("\n" + new_content)
                
                conn.commit()
                logger.info(f"Updated note: {note_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating note: {e}")
            return False

    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note
        
        Args:
            note_id: Note ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get note file path
                cursor.execute("SELECT file_path FROM notes WHERE id = ?", (note_id,))
                row = cursor.fetchone()
                if row and row[0] and os.path.exists(row[0]):
                    os.remove(row[0])
                
                # Delete from database
                cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                conn.commit()
                
                logger.info(f"Deleted note: {note_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            return False

    def add_todo_item(self, content: str, due_date: Optional[datetime] = None, priority: str = "normal") -> str:
        """
        Add a new todo item
        
        Args:
            content: Todo item content
            due_date: Optional due date
            priority: Priority level (low, normal, high)
            
        Returns:
            Todo item ID
        """
        todo_id = self._get_unique_id("todo")
        created_time = datetime.now()
        
        todo_item = TodoItem(
            id=todo_id,
            content=content,
            created_time=created_time,
            due_date=due_date,
            priority=priority
        )
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO todo_items (id, content, created_time, due_date, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                todo_item.id,
                todo_item.content,
                todo_item.created_time.isoformat(),
                todo_item.due_date.isoformat() if todo_item.due_date else None,
                todo_item.priority
            ))
            conn.commit()
        
        logger.info(f"Added todo item: {content}")
        return todo_id

    def get_todo_items(self, include_completed: bool = False, priority: str = None) -> List[Dict[str, Any]]:
        """
        Get todo items with optional filtering
        
        Args:
            include_completed: Whether to include completed items
            priority: Optional priority filter
            
        Returns:
            List of todo item dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM todo_items"
            conditions = []
            params = []
            
            if not include_completed:
                conditions.append("is_completed = 0")
            
            if priority:
                conditions.append("priority = ?")
                params.append(priority)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY priority DESC, created_time ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            todo_items = []
            for row in rows:
                todo_items.append({
                    "id": row[0],
                    "content": row[1],
                    "created_time": row[2],
                    "due_date": row[3],
                    "priority": row[4],
                    "is_completed": bool(row[5]),
                    "completed_time": row[6]
                })
            
            return todo_items

    def complete_todo_item(self, todo_id: str) -> bool:
        """
        Mark a todo item as completed
        
        Args:
            todo_id: Todo item ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            completed_time = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE todo_items 
                    SET is_completed = 1, completed_time = ?
                    WHERE id = ?
                ''', (completed_time.isoformat(), todo_id))
                conn.commit()
            
            logger.info(f"Completed todo item: {todo_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing todo item: {e}")
            return False

    def delete_todo_item(self, todo_id: str) -> bool:
        """
        Delete a todo item
        
        Args:
            todo_id: Todo item ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM todo_items WHERE id = ?", (todo_id,))
                conn.commit()
            
            logger.info(f"Deleted todo item: {todo_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting todo item: {e}")
            return False

    def get_productivity_summary(self) -> Dict[str, Any]:
        """
        Get a summary of productivity items
        
        Returns:
            Dictionary with counts and recent items
        """
        summary = {
            "active_timers": len(self.active_timers),
            "active_reminders": len(self.active_reminders),
            "active_alarms": len(self.active_alarms),
            "total_notes": 0,
            "pending_todos": 0,
            "completed_todos": 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count notes
            cursor.execute("SELECT COUNT(*) FROM notes")
            summary["total_notes"] = cursor.fetchone()[0]
            
            # Count todos
            cursor.execute("SELECT COUNT(*) FROM todo_items WHERE is_completed = 0")
            summary["pending_todos"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM todo_items WHERE is_completed = 1")
            summary["completed_todos"] = cursor.fetchone()[0]
        
        return summary

    def cleanup_old_data(self, days_old: int = 30):
        """
        Clean up old completed items
        
        Args:
            days_old: Remove items older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clean up old completed timers
            cursor.execute('''
                DELETE FROM timers 
                WHERE is_completed = 1 AND created_at < ?
            ''', (cutoff_date.isoformat(),))
            
            # Clean up old completed reminders
            cursor.execute('''
                DELETE FROM reminders 
                WHERE is_completed = 1 AND created_at < ?
            ''', (cutoff_date.isoformat(),))
            
            # Clean up old completed todos
            cursor.execute('''
                DELETE FROM todo_items 
                WHERE is_completed = 1 AND completed_time < ?
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()
        
        logger.info(f"Cleaned up productivity data older than {days_old} days")
 
   # Calendar event management methods

    def create_calendar_event(self, title: str, start_time: datetime, end_time: datetime = None, 
                            description: str = "", location: str = "") -> str:
        """
        Create a calendar event
        
        Args:
            title: Event title
            start_time: Event start time
            end_time: Event end time (optional, defaults to 1 hour after start)
            description: Event description
            location: Event location
            
        Returns:
            Event ID
        """
        event_id = self._get_unique_id("event")
        created_time = datetime.now()
        
        # Default end time to 1 hour after start if not provided
        if end_time is None:
            end_time = start_time + timedelta(hours=1)
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create calendar events table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    description TEXT,
                    location TEXT,
                    created_time TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO calendar_events (id, title, start_time, end_time, description, location, created_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                title,
                start_time.isoformat(),
                end_time.isoformat(),
                description,
                location,
                created_time.isoformat()
            ))
            conn.commit()
        
        logger.info(f"Created calendar event: {title} at {start_time}")
        return event_id

    def get_calendar_events(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get calendar events within a date range
        
        Args:
            start_date: Start of date range (optional, defaults to today)
            end_date: End of date range (optional, defaults to 7 days from start)
            
        Returns:
            List of event dictionaries
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Ensure table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    description TEXT,
                    location TEXT,
                    created_time TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                SELECT * FROM calendar_events 
                WHERE is_active = 1 
                AND start_time >= ? 
                AND start_time <= ?
                ORDER BY start_time ASC
            ''', (start_date.isoformat(), end_date.isoformat()))
            
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    "id": row[0],
                    "title": row[1],
                    "start_time": row[2],
                    "end_time": row[3],
                    "description": row[4],
                    "location": row[5],
                    "created_time": row[6],
                    "is_active": bool(row[7])
                })
            
            return events

    def update_calendar_event(self, event_id: str, title: str = None, start_time: datetime = None,
                            end_time: datetime = None, description: str = None, location: str = None) -> bool:
        """
        Update a calendar event
        
        Args:
            event_id: Event ID to update
            title: New title (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            description: New description (optional)
            location: New location (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current event
                cursor.execute("SELECT * FROM calendar_events WHERE id = ?", (event_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                # Update fields
                new_title = title if title is not None else row[1]
                new_start_time = start_time.isoformat() if start_time is not None else row[2]
                new_end_time = end_time.isoformat() if end_time is not None else row[3]
                new_description = description if description is not None else row[4]
                new_location = location if location is not None else row[5]
                
                # Update database
                cursor.execute('''
                    UPDATE calendar_events 
                    SET title = ?, start_time = ?, end_time = ?, description = ?, location = ?
                    WHERE id = ?
                ''', (
                    new_title,
                    new_start_time,
                    new_end_time,
                    new_description,
                    new_location,
                    event_id
                ))
                
                conn.commit()
                logger.info(f"Updated calendar event: {event_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating calendar event: {e}")
            return False

    def delete_calendar_event(self, event_id: str) -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: Event ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE calendar_events SET is_active = 0 WHERE id = ?", (event_id,))
                conn.commit()
                
                logger.info(f"Deleted calendar event: {event_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}")
            return False

    def get_upcoming_events(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get upcoming events within the specified time frame
        
        Args:
            hours_ahead: Number of hours to look ahead
            
        Returns:
            List of upcoming event dictionaries
        """
        now = datetime.now()
        end_time = now + timedelta(hours=hours_ahead)
        
        return self.get_calendar_events(start_date=now, end_date=end_time)

    def get_daily_schedule(self, target_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get the schedule for a specific day
        
        Args:
            target_date: Date to get schedule for (defaults to today)
            
        Returns:
            List of events for the day
        """
        if target_date is None:
            target_date = datetime.now()
        
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return self.get_calendar_events(start_date=start_of_day, end_date=end_of_day)

    def export_notes_to_file(self, file_path: str, format: str = "txt") -> bool:
        """
        Export all notes to a file
        
        Args:
            file_path: Path to export file
            format: Export format (txt, json, csv)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            notes = self.get_notes()
            
            if format.lower() == "json":
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(notes, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == "csv":
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if notes:
                        writer = csv.DictWriter(f, fieldnames=notes[0].keys())
                        writer.writeheader()
                        writer.writerows(notes)
            
            else:  # Default to txt
                with open(file_path, 'w', encoding='utf-8') as f:
                    for note in notes:
                        f.write(f"Title: {note['title']}\n")
                        f.write(f"Created: {note['created_time']}\n")
                        f.write(f"Tags: {', '.join(note['tags'])}\n")
                        f.write(f"Content:\n{note['content']}\n")
                        f.write("-" * 50 + "\n\n")
            
            logger.info(f"Exported {len(notes)} notes to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting notes: {e}")
            return False

    def import_notes_from_file(self, file_path: str, format: str = "txt") -> int:
        """
        Import notes from a file
        
        Args:
            file_path: Path to import file
            format: Import format (txt, json)
            
        Returns:
            Number of notes imported
        """
        try:
            imported_count = 0
            
            if format.lower() == "json":
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                
                for note_data in notes_data:
                    self.save_note(
                        note_data.get('title', 'Imported Note'),
                        note_data.get('content', ''),
                        note_data.get('tags', [])
                    )
                    imported_count += 1
            
            else:  # Default to txt
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple parsing for txt format
                sections = content.split("-" * 50)
                for section in sections:
                    if section.strip():
                        lines = section.strip().split('\n')
                        title = "Imported Note"
                        content_lines = []
                        tags = []
                        
                        for line in lines:
                            if line.startswith("Title:"):
                                title = line.replace("Title:", "").strip()
                            elif line.startswith("Tags:"):
                                tags_str = line.replace("Tags:", "").strip()
                                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                            elif line.startswith("Content:"):
                                continue
                            elif not line.startswith("Created:"):
                                content_lines.append(line)
                        
                        if content_lines:
                            content_text = '\n'.join(content_lines).strip()
                            if content_text:
                                self.save_note(title, content_text, tags)
                                imported_count += 1
            
            logger.info(f"Imported {imported_count} notes from {file_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing notes: {e}")
            return 0