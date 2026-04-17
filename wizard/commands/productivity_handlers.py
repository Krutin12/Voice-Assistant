"""
Productivity Command Handlers

This module contains command handlers for productivity features including
timers, reminders, alarms, notes, and todo management.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from .command_router import Command, Response
from .productivity_manager import ProductivityManager

logger = logging.getLogger(__name__)


class ProductivityHandlers:
    """
    Command handlers for productivity features
    """

    def __init__(self, productivity_manager: ProductivityManager):
        self.productivity_manager = productivity_manager

    def handle_set_timer(self, command: Command) -> Response:
        """
        Handle timer setting commands
        
        Examples:
        - "Set timer for 5 minutes"
        - "Timer 30 seconds"
        - "Remind me in 2 hours"
        """
        try:
            # Extract duration and unit from entities
            duration = command.entities.get('duration')
            unit = command.entities.get('unit')
            
            if not duration or not unit:
                # Try to extract from raw text
                duration_match = re.search(r'(\d+)\s+(second|minute|hour)s?', command.raw_text, re.IGNORECASE)
                if duration_match:
                    duration = int(duration_match.group(1))
                    unit = duration_match.group(2)
                else:
                    return Response(
                        text="I need to know the duration and time unit. For example, 'set timer for 5 minutes'.",
                        error_message="Missing duration or unit"
                    )
            
            # Create label from command
            label_match = re.search(r'for\s+(.+?)(?:\s+timer|\s*$)', command.raw_text, re.IGNORECASE)
            label = label_match.group(1) if label_match else f"{duration} {unit} timer"
            
            # Set the timer
            timer_id = self.productivity_manager.set_timer(duration, unit, label)
            
            return Response(
                text=f"Timer set for {duration} {unit}. I'll notify you when it's done.",
                action_taken=True,
                context_updates={"last_timer_id": timer_id}
            )
            
        except Exception as e:
            logger.error(f"Error setting timer: {e}")
            return Response(
                text="Sorry, I couldn't set the timer. Please try again.",
                error_message=str(e)
            )

    def handle_create_reminder(self, command: Command) -> Response:
        """
        Handle reminder creation commands
        
        Examples:
        - "Remind me to call John at 3 PM"
        - "Set reminder to take medicine in 2 hours"
        - "Create reminder for meeting tomorrow at 9 AM"
        """
        try:
            content = command.entities.get('content', '')
            
            if not content:
                # Extract from raw text
                reminder_match = re.search(r'remind\s+me\s+to\s+(.+)', command.raw_text, re.IGNORECASE)
                if not reminder_match:
                    reminder_match = re.search(r'reminder\s+(.+)', command.raw_text, re.IGNORECASE)
                
                if reminder_match:
                    content = reminder_match.group(1)
                else:
                    return Response(
                        text="What would you like me to remind you about?",
                        error_message="Missing reminder content"
                    )
            
            # Parse time from content
            scheduled_time = self._parse_reminder_time(content)
            
            if not scheduled_time:
                # Default to 1 hour from now if no time specified
                scheduled_time = datetime.now() + timedelta(hours=1)
                content += " (in 1 hour)"
            
            # Create the reminder
            reminder_id = self.productivity_manager.create_reminder(content, scheduled_time)
            
            time_str = scheduled_time.strftime("%I:%M %p on %B %d")
            return Response(
                text=f"Reminder set: {content} at {time_str}",
                action_taken=True,
                context_updates={"last_reminder_id": reminder_id}
            )
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return Response(
                text="Sorry, I couldn't create the reminder. Please try again.",
                error_message=str(e)
            )

    def handle_create_alarm(self, command: Command) -> Response:
        """
        Handle alarm creation commands
        
        Examples:
        - "Set alarm for 7 AM"
        - "Wake me up at 6:30 tomorrow"
        - "Create daily alarm for 8 AM"
        """
        try:
            # Extract time from command
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)', command.raw_text, re.IGNORECASE)
            if not time_match:
                time_match = re.search(r'(\d{1,2})\s*(AM|PM)', command.raw_text, re.IGNORECASE)
            
            if not time_match:
                return Response(
                    text="Please specify a time for the alarm, like '7 AM' or '6:30 PM'.",
                    error_message="Missing alarm time"
                )
            
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3).upper() if len(time_match.groups()) >= 3 else time_match.group(2).upper()
            
            # Convert to 24-hour format
            if period == 'PM' and hour != 12:
                hour += 12
            elif period == 'AM' and hour == 12:
                hour = 0
            
            time_str = f"{hour:02d}:{minute:02d}"
            
            # Determine days (default to daily)
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            if 'weekday' in command.raw_text.lower():
                days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            elif 'weekend' in command.raw_text.lower():
                days = ['saturday', 'sunday']
            
            # Create label
            label = f"Alarm for {time_match.group(0)}"
            
            # Create the alarm
            alarm_id = self.productivity_manager.create_alarm(label, time_str, days)
            
            return Response(
                text=f"Alarm set for {time_match.group(0)} on {', '.join(days)}",
                action_taken=True,
                context_updates={"last_alarm_id": alarm_id}
            )
            
        except Exception as e:
            logger.error(f"Error creating alarm: {e}")
            return Response(
                text="Sorry, I couldn't create the alarm. Please try again.",
                error_message=str(e)
            )

    def handle_take_note(self, command: Command) -> Response:
        """
        Handle note-taking commands
        
        Examples:
        - "Take note: Meeting with client tomorrow"
        - "Write down: Buy groceries"
        - "Note that the password is 12345"
        """
        try:
            content = command.entities.get('content', '')
            
            if not content:
                # Extract from raw text
                note_patterns = [
                    r'take\s+note:?\s*(.+)',
                    r'write\s+down:?\s*(.+)',
                    r'note\s+that\s+(.+)',
                    r'note:?\s*(.+)'
                ]
                
                for pattern in note_patterns:
                    match = re.search(pattern, command.raw_text, re.IGNORECASE)
                    if match:
                        content = match.group(1)
                        break
                
                if not content:
                    return Response(
                        text="What would you like me to write down?",
                        error_message="Missing note content"
                    )
            
            # Generate title from first few words
            words = content.split()
            title = ' '.join(words[:5]) + ('...' if len(words) > 5 else '')
            
            # Save the note
            note_id = self.productivity_manager.save_note(title, content)
            
            return Response(
                text=f"Note saved: {title}",
                action_taken=True,
                context_updates={"last_note_id": note_id}
            )
            
        except Exception as e:
            logger.error(f"Error taking note: {e}")
            return Response(
                text="Sorry, I couldn't save the note. Please try again.",
                error_message=str(e)
            )

    def handle_add_todo(self, command: Command) -> Response:
        """
        Handle todo item addition commands
        
        Examples:
        - "Add to todo: Call dentist"
        - "Todo: Finish project report"
        - "Task: Buy birthday gift"
        """
        try:
            content = command.entities.get('content', '')
            
            if not content:
                # Extract from raw text
                todo_patterns = [
                    r'add\s+to\s+todo:?\s*(.+)',
                    r'todo:?\s*(.+)',
                    r'task:?\s*(.+)'
                ]
                
                for pattern in todo_patterns:
                    match = re.search(pattern, command.raw_text, re.IGNORECASE)
                    if match:
                        content = match.group(1)
                        break
                
                if not content:
                    return Response(
                        text="What task would you like me to add to your todo list?",
                        error_message="Missing todo content"
                    )
            
            # Determine priority from keywords
            priority = "normal"
            if any(word in content.lower() for word in ['urgent', 'important', 'asap', 'priority']):
                priority = "high"
            elif any(word in content.lower() for word in ['later', 'someday', 'maybe']):
                priority = "low"
            
            # Add the todo item
            todo_id = self.productivity_manager.add_todo_item(content, priority=priority)
            
            return Response(
                text=f"Added to todo list: {content}",
                action_taken=True,
                context_updates={"last_todo_id": todo_id}
            )
            
        except Exception as e:
            logger.error(f"Error adding todo: {e}")
            return Response(
                text="Sorry, I couldn't add that to your todo list. Please try again.",
                error_message=str(e)
            )

    def handle_list_todos(self, command: Command) -> Response:
        """
        Handle todo list viewing commands
        
        Examples:
        - "Show my todo list"
        - "What's on my todo list?"
        - "List my tasks"
        """
        try:
            # Get todo items
            todos = self.productivity_manager.get_todo_items(include_completed=False)
            
            if not todos:
                return Response(
                    text="Your todo list is empty. Great job!",
                    action_taken=True
                )
            
            # Format the list
            todo_text = "Here's your todo list:\n"
            for i, todo in enumerate(todos[:10], 1):  # Limit to 10 items
                priority_marker = "🔴" if todo['priority'] == 'high' else "🟡" if todo['priority'] == 'normal' else "🟢"
                todo_text += f"{i}. {priority_marker} {todo['content']}\n"
            
            if len(todos) > 10:
                todo_text += f"... and {len(todos) - 10} more items"
            
            return Response(
                text=todo_text,
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error listing todos: {e}")
            return Response(
                text="Sorry, I couldn't retrieve your todo list. Please try again.",
                error_message=str(e)
            )

    def handle_complete_todo(self, command: Command) -> Response:
        """
        Handle todo completion commands
        
        Examples:
        - "Mark first todo as done"
        - "Complete task about groceries"
        - "Done with calling dentist"
        """
        try:
            # Get current todos
            todos = self.productivity_manager.get_todo_items(include_completed=False)
            
            if not todos:
                return Response(
                    text="You don't have any pending todo items.",
                    action_taken=False
                )
            
            # Try to identify which todo to complete
            todo_to_complete = None
            
            # Check for number references
            number_match = re.search(r'(\d+)', command.raw_text)
            if number_match:
                index = int(number_match.group(1)) - 1
                if 0 <= index < len(todos):
                    todo_to_complete = todos[index]
            
            # Check for content matching
            if not todo_to_complete:
                for todo in todos:
                    if any(word.lower() in todo['content'].lower() for word in command.raw_text.split() if len(word) > 3):
                        todo_to_complete = todo
                        break
            
            # Default to first item if nothing specific found
            if not todo_to_complete:
                todo_to_complete = todos[0]
            
            # Complete the todo
            success = self.productivity_manager.complete_todo_item(todo_to_complete['id'])
            
            if success:
                return Response(
                    text=f"Marked as completed: {todo_to_complete['content']}",
                    action_taken=True
                )
            else:
                return Response(
                    text="Sorry, I couldn't mark that item as completed.",
                    error_message="Failed to complete todo"
                )
            
        except Exception as e:
            logger.error(f"Error completing todo: {e}")
            return Response(
                text="Sorry, I couldn't complete that todo item. Please try again.",
                error_message=str(e)
            )

    def handle_list_timers(self, command: Command) -> Response:
        """
        Handle timer listing commands
        
        Examples:
        - "Show my timers"
        - "What timers are running?"
        - "List active timers"
        """
        try:
            timers = self.productivity_manager.get_active_timers()
            
            if not timers:
                return Response(
                    text="You don't have any active timers.",
                    action_taken=True
                )
            
            timer_text = "Active timers:\n"
            for timer in timers:
                minutes = timer['remaining_seconds'] // 60
                seconds = timer['remaining_seconds'] % 60
                timer_text += f"• {timer['label']}: {minutes}m {seconds}s remaining\n"
            
            return Response(
                text=timer_text,
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error listing timers: {e}")
            return Response(
                text="Sorry, I couldn't retrieve your timers. Please try again.",
                error_message=str(e)
            )

    def handle_productivity_summary(self, command: Command) -> Response:
        """
        Handle productivity summary commands
        
        Examples:
        - "Show my productivity summary"
        - "What's my status?"
        - "Productivity overview"
        """
        try:
            summary = self.productivity_manager.get_productivity_summary()
            
            summary_text = "Productivity Summary:\n"
            summary_text += f"• Active timers: {summary['active_timers']}\n"
            summary_text += f"• Active reminders: {summary['active_reminders']}\n"
            summary_text += f"• Active alarms: {summary['active_alarms']}\n"
            summary_text += f"• Total notes: {summary['total_notes']}\n"
            summary_text += f"• Pending todos: {summary['pending_todos']}\n"
            summary_text += f"• Completed todos: {summary['completed_todos']}\n"
            
            return Response(
                text=summary_text,
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error getting productivity summary: {e}")
            return Response(
                text="Sorry, I couldn't get your productivity summary. Please try again.",
                error_message=str(e)
            )

    def handle_create_calendar_event(self, command: Command) -> Response:
        """
        Handle calendar event creation commands
        
        Examples:
        - "Schedule meeting with John tomorrow at 2 PM"
        - "Create event for dentist appointment Friday at 10 AM"
        - "Add calendar event for lunch at noon"
        """
        try:
            content = command.entities.get('content', '')
            
            if not content:
                # Extract from raw text
                event_patterns = [
                    r'schedule\s+(.+)',
                    r'create\s+event\s+for\s+(.+)',
                    r'add\s+calendar\s+event\s+for\s+(.+)',
                    r'calendar\s+(.+)'
                ]
                
                for pattern in event_patterns:
                    match = re.search(pattern, command.raw_text, re.IGNORECASE)
                    if match:
                        content = match.group(1)
                        break
                
                if not content:
                    return Response(
                        text="What event would you like me to schedule?",
                        error_message="Missing event content"
                    )
            
            # Parse time from content
            event_time = self._parse_event_time(content)
            
            if not event_time:
                # Default to 1 hour from now if no time specified
                event_time = datetime.now() + timedelta(hours=1)
                content += " (in 1 hour)"
            
            # Extract title from content (remove time references)
            title = self._extract_event_title(content)
            
            # Create the calendar event
            event_id = self.productivity_manager.create_calendar_event(title, event_time)
            
            time_str = event_time.strftime("%I:%M %p on %B %d")
            return Response(
                text=f"Calendar event created: {title} at {time_str}",
                action_taken=True,
                context_updates={"last_event_id": event_id}
            )
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return Response(
                text="Sorry, I couldn't create the calendar event. Please try again.",
                error_message=str(e)
            )

    def handle_list_calendar_events(self, command: Command) -> Response:
        """
        Handle calendar event listing commands
        
        Examples:
        - "Show my calendar"
        - "What's on my schedule today?"
        - "List upcoming events"
        """
        try:
            # Determine time range based on command
            if any(word in command.raw_text.lower() for word in ['today', 'schedule']):
                events = self.productivity_manager.get_daily_schedule()
                time_desc = "today"
            elif 'upcoming' in command.raw_text.lower():
                events = self.productivity_manager.get_upcoming_events(hours_ahead=48)
                time_desc = "upcoming"
            else:
                events = self.productivity_manager.get_upcoming_events(hours_ahead=24)
                time_desc = "next 24 hours"
            
            if not events:
                return Response(
                    text=f"You don't have any events {time_desc}.",
                    action_taken=True
                )
            
            # Format the list
            events_text = f"Events {time_desc}:\n"
            for event in events:
                start_time = datetime.fromisoformat(event['start_time'])
                time_str = start_time.strftime("%I:%M %p")
                date_str = start_time.strftime("%B %d") if 'upcoming' in time_desc else ""
                
                events_text += f"• {event['title']} at {time_str}"
                if date_str:
                    events_text += f" on {date_str}"
                if event['location']:
                    events_text += f" ({event['location']})"
                events_text += "\n"
            
            return Response(
                text=events_text,
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            return Response(
                text="Sorry, I couldn't retrieve your calendar events. Please try again.",
                error_message=str(e)
            )

    def handle_search_notes(self, command: Command) -> Response:
        """
        Handle note searching commands
        
        Examples:
        - "Find notes about project"
        - "Search notes for meeting"
        - "Show notes tagged with work"
        """
        try:
            query = command.entities.get('query', '')
            
            if not query:
                # Extract from raw text
                search_patterns = [
                    r'find\s+notes\s+about\s+(.+)',
                    r'search\s+notes\s+for\s+(.+)',
                    r'show\s+notes\s+tagged\s+with\s+(.+)',
                    r'notes\s+about\s+(.+)'
                ]
                
                for pattern in search_patterns:
                    match = re.search(pattern, command.raw_text, re.IGNORECASE)
                    if match:
                        query = match.group(1)
                        break
                
                if not query:
                    return Response(
                        text="What would you like me to search for in your notes?",
                        error_message="Missing search query"
                    )
            
            # Search notes
            if 'tagged with' in command.raw_text.lower():
                # Search by tags
                tags = [tag.strip() for tag in query.split(',')]
                notes = self.productivity_manager.get_notes(tags=tags)
            else:
                # Search by content
                notes = self.productivity_manager.get_notes(search_query=query)
            
            if not notes:
                return Response(
                    text=f"I couldn't find any notes matching '{query}'.",
                    action_taken=True
                )
            
            # Format results
            results_text = f"Found {len(notes)} notes matching '{query}':\n"
            for note in notes[:5]:  # Limit to 5 results
                results_text += f"• {note['title']}: {note['content'][:50]}...\n"
            
            if len(notes) > 5:
                results_text += f"... and {len(notes) - 5} more notes"
            
            return Response(
                text=results_text,
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return Response(
                text="Sorry, I couldn't search your notes. Please try again.",
                error_message=str(e)
            )

    def _parse_event_time(self, content: str) -> Optional[datetime]:
        """
        Parse time information from event content
        
        Args:
            content: Event content that may contain time information
            
        Returns:
            Datetime object or None if no time found
        """
        now = datetime.now()
        
        # Check for relative time patterns
        relative_patterns = [
            (r'tomorrow\s+at\s+(\d{1,2}):?(\d{2})?\s*(AM|PM)', 
             lambda m: self._get_time_tomorrow(int(m.group(1)), int(m.group(2)) if m.group(2) else 0, m.group(3))),
            (r'today\s+at\s+(\d{1,2}):?(\d{2})?\s*(AM|PM)', 
             lambda m: self._get_time_today(int(m.group(1)), int(m.group(2)) if m.group(2) else 0, m.group(3))),
            (r'at\s+(\d{1,2}):?(\d{2})?\s*(AM|PM)', 
             lambda m: self._get_time_today(int(m.group(1)), int(m.group(2)) if m.group(2) else 0, m.group(3))),
            (r'(\d{1,2})\s*(AM|PM)', 
             lambda m: self._get_time_today(int(m.group(1)), 0, m.group(2))),
            (r'in\s+(\d+)\s+hours?', lambda m: now + timedelta(hours=int(m.group(1)))),
            (r'in\s+(\d+)\s+minutes?', lambda m: now + timedelta(minutes=int(m.group(1)))),
        ]
        
        for pattern, time_func in relative_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return time_func(match)
        
        return None

    def _get_time_today(self, hour: int, minute: int, period: str) -> datetime:
        """Get datetime for today at specified time"""
        now = datetime.now()
        
        # Convert to 24-hour format
        if period.upper() == 'PM' and hour != 12:
            hour += 12
        elif period.upper() == 'AM' and hour == 12:
            hour = 0
        
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if target_time <= now:
            target_time += timedelta(days=1)
        
        return target_time

    def _get_time_tomorrow(self, hour: int, minute: int, period: str) -> datetime:
        """Get datetime for tomorrow at specified time"""
        tomorrow = datetime.now() + timedelta(days=1)
        
        # Convert to 24-hour format
        if period.upper() == 'PM' and hour != 12:
            hour += 12
        elif period.upper() == 'AM' and hour == 12:
            hour = 0
        
        return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def _extract_event_title(self, content: str) -> str:
        """Extract event title by removing time references"""
        # Remove common time patterns
        time_patterns = [
            r'\s+tomorrow\s+at\s+\d{1,2}:?\d{0,2}\s*(AM|PM)',
            r'\s+today\s+at\s+\d{1,2}:?\d{0,2}\s*(AM|PM)',
            r'\s+at\s+\d{1,2}:?\d{0,2}\s*(AM|PM)',
            r'\s+\d{1,2}\s*(AM|PM)',
            r'\s+in\s+\d+\s+(hours?|minutes?)',
            r'\s+\(in\s+\d+\s+(hours?|minutes?)\)'
        ]
        
        title = content
        for pattern in time_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        return title.strip()

    def _parse_reminder_time(self, content: str) -> Optional[datetime]:
        """
        Parse time information from reminder content
        
        Args:
            content: Reminder content that may contain time information
            
        Returns:
            Datetime object or None if no time found
        """
        now = datetime.now()
        
        # Check for relative time patterns
        relative_patterns = [
            (r'in\s+(\d+)\s+minutes?', lambda m: now + timedelta(minutes=int(m.group(1)))),
            (r'in\s+(\d+)\s+hours?', lambda m: now + timedelta(hours=int(m.group(1)))),
            (r'in\s+(\d+)\s+days?', lambda m: now + timedelta(days=int(m.group(1)))),
            (r'tomorrow', lambda m: now + timedelta(days=1)),
            (r'next\s+week', lambda m: now + timedelta(weeks=1)),
        ]
        
        for pattern, time_func in relative_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return time_func(match)
        
        # Check for absolute time patterns
        time_match = re.search(r'at\s+(\d{1,2}):?(\d{2})?\s*(AM|PM)', content, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3).upper()
            
            # Convert to 24-hour format
            if period == 'PM' and hour != 12:
                hour += 12
            elif period == 'AM' and hour == 12:
                hour = 0
            
            # Set for today or tomorrow if time has passed
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time <= now:
                target_time += timedelta(days=1)
            
            return target_time
        
        return None


def register_productivity_handlers(command_router, productivity_manager: ProductivityManager):
    """
    Register all productivity command handlers with the command router
    
    Args:
        command_router: CommandRouter instance
        productivity_manager: ProductivityManager instance
    """
    handlers = ProductivityHandlers(productivity_manager)
    
    # Timer handlers
    command_router.register_handler("set_timer", handlers.handle_set_timer)
    command_router.register_handler("list_timers", handlers.handle_list_timers)
    
    # Reminder handlers
    command_router.register_handler("create_reminder", handlers.handle_create_reminder)
    
    # Alarm handlers
    command_router.register_handler("create_alarm", handlers.handle_create_alarm)
    
    # Note handlers
    command_router.register_handler("take_note", handlers.handle_take_note)
    command_router.register_handler("search_notes", handlers.handle_search_notes)
    
    # Todo handlers
    command_router.register_handler("add_todo", handlers.handle_add_todo)
    command_router.register_handler("list_todos", handlers.handle_list_todos)
    command_router.register_handler("complete_todo", handlers.handle_complete_todo)
    
    # Calendar handlers
    command_router.register_handler("create_calendar_event", handlers.handle_create_calendar_event)
    command_router.register_handler("list_calendar_events", handlers.handle_list_calendar_events)
    
    # Summary handlers
    command_router.register_handler("productivity_summary", handlers.handle_productivity_summary)
    
    logger.info("Registered productivity command handlers")