"""
Routine Engine Module

This module handles custom routine definition and execution for multi-command sequences,
scheduled tasks, and automation workflows.
"""

import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .command_router import Command, Response

logger = logging.getLogger(__name__)


@dataclass
class RoutineStep:
    """Represents a single step in a routine"""
    command: str
    delay: float = 0.0  # Delay in seconds before executing this step
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class Routine:
    """Represents a complete routine with multiple steps"""
    name: str
    description: str
    steps: List[RoutineStep]
    enabled: bool = True
    created_at: datetime = None
    last_executed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    name: str
    routine_name: str
    schedule_type: str  # 'daily', 'weekly', 'monthly', 'cron'
    schedule_time: str  # Time string like "08:00" or cron expression
    enabled: bool = True
    created_at: datetime = None
    last_executed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RoutineEngine:
    """
    Main routine engine that manages custom routines and scheduled tasks
    """
    
    def __init__(self, config: Dict, command_router=None):
        self.config = config
        self.command_router = command_router
        self.routines: Dict[str, Routine] = {}
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_routines: Dict[str, threading.Thread] = {}
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_running = False
        
        # Storage paths
        self.routines_file = Path("wizard/data/routines.json")
        self.tasks_file = Path("wizard/data/scheduled_tasks.json")
        
        # Ensure data directory exists
        self.routines_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing routines and tasks
        self._load_routines()
        self._load_scheduled_tasks()
        
        # Setup default routines
        self._setup_default_routines()
        
        # Start scheduler
        self._start_scheduler()
    
    def _load_routines(self) -> None:
        """Load routines from JSON file"""
        if not self.routines_file.exists():
            return
        
        try:
            with open(self.routines_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, routine_data in data.items():
                steps = [RoutineStep(**step) for step in routine_data['steps']]
                routine = Routine(
                    name=routine_data['name'],
                    description=routine_data['description'],
                    steps=steps,
                    enabled=routine_data.get('enabled', True),
                    created_at=datetime.fromisoformat(routine_data['created_at']),
                    last_executed=datetime.fromisoformat(routine_data['last_executed']) if routine_data.get('last_executed') else None
                )
                self.routines[name] = routine
                
        except Exception as e:
            logger.error(f"Error loading routines: {e}")
    
    def _load_scheduled_tasks(self) -> None:
        """Load scheduled tasks from JSON file"""
        if not self.tasks_file.exists():
            return
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, task_data in data.items():
                task = ScheduledTask(
                    name=task_data['name'],
                    routine_name=task_data['routine_name'],
                    schedule_type=task_data['schedule_type'],
                    schedule_time=task_data['schedule_time'],
                    enabled=task_data.get('enabled', True),
                    created_at=datetime.fromisoformat(task_data['created_at']),
                    last_executed=datetime.fromisoformat(task_data['last_executed']) if task_data.get('last_executed') else None
                )
                self.scheduled_tasks[name] = task
                
        except Exception as e:
            logger.error(f"Error loading scheduled tasks: {e}")
    
    def _save_routines(self) -> bool:
        """Save routines to JSON file"""
        try:
            data = {}
            for name, routine in self.routines.items():
                data[name] = {
                    'name': routine.name,
                    'description': routine.description,
                    'steps': [asdict(step) for step in routine.steps],
                    'enabled': routine.enabled,
                    'created_at': routine.created_at.isoformat(),
                    'last_executed': routine.last_executed.isoformat() if routine.last_executed else None
                }
            
            with open(self.routines_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logger.error(f"Error saving routines: {e}")
            return False  
  
    def _save_scheduled_tasks(self) -> bool:
        """Save scheduled tasks to JSON file"""
        try:
            data = {}
            for name, task in self.scheduled_tasks.items():
                data[name] = {
                    'name': task.name,
                    'routine_name': task.routine_name,
                    'schedule_type': task.schedule_type,
                    'schedule_time': task.schedule_time,
                    'enabled': task.enabled,
                    'created_at': task.created_at.isoformat(),
                    'last_executed': task.last_executed.isoformat() if task.last_executed else None
                }
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logger.error(f"Error saving scheduled tasks: {e}")
            return False
    
    def _setup_default_routines(self) -> None:
        """Setup default routines like 'Good morning'"""
        # Good morning routine
        if "good_morning" not in self.routines:
            good_morning_steps = [
                RoutineStep("what_time", 0.0),
                RoutineStep("what_date", 1.0),
                RoutineStep("weather", 2.0),
                RoutineStep("news", 3.0),
                RoutineStep("open_application", 4.0, {"application": "chrome"}),
                RoutineStep("open_application", 5.0, {"application": "spotify"}),
                RoutineStep("productivity_summary", 6.0)
            ]
            
            good_morning = Routine(
                name="good_morning",
                description="Morning routine with time, weather, news, and app launching",
                steps=good_morning_steps
            )
            self.routines["good_morning"] = good_morning
        
        # Good night routine
        if "good_night" not in self.routines:
            good_night_steps = [
                RoutineStep("set_volume", 0.0, {"volume_level": 20}),
                RoutineStep("close_application", 1.0, {"application": "chrome"}),
                RoutineStep("close_application", 2.0, {"application": "spotify"}),
                RoutineStep("system_lock", 3.0)
            ]
            
            good_night = Routine(
                name="good_night",
                description="Night routine to close apps and lock system",
                steps=good_night_steps
            )
            self.routines["good_night"] = good_night
        
        # Work mode routine
        if "work_mode" not in self.routines:
            work_mode_steps = [
                RoutineStep("open_application", 0.0, {"application": "vscode"}),
                RoutineStep("open_application", 1.0, {"application": "teams"}),
                RoutineStep("open_application", 2.0, {"application": "outlook"}),
                RoutineStep("set_volume", 3.0, {"volume_level": 30})
            ]
            
            work_mode = Routine(
                name="work_mode",
                description="Setup work environment with development tools",
                steps=work_mode_steps
            )
            self.routines["work_mode"] = work_mode
        
        # Save default routines
        self._save_routines()
    
    def create_routine(self, name: str, description: str, steps: List[Dict[str, Any]]) -> bool:
        """
        Create a new custom routine
        
        Args:
            name: Unique name for the routine
            description: Description of what the routine does
            steps: List of step dictionaries with command, delay, and parameters
            
        Returns:
            True if routine was created successfully
        """
        try:
            routine_steps = []
            for step_data in steps:
                step = RoutineStep(
                    command=step_data['command'],
                    delay=step_data.get('delay', 0.0),
                    parameters=step_data.get('parameters', {})
                )
                routine_steps.append(step)
            
            routine = Routine(
                name=name,
                description=description,
                steps=routine_steps
            )
            
            self.routines[name] = routine
            self._save_routines()
            
            logger.info(f"Created routine: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating routine {name}: {e}")
            return False
    
    def execute_routine(self, routine_name: str) -> Response:
        """
        Execute a routine by name
        
        Args:
            routine_name: Name of the routine to execute
            
        Returns:
            Response object with execution result
        """
        if routine_name not in self.routines:
            return Response(
                text=f"Routine '{routine_name}' not found.",
                error_message=f"Routine not found: {routine_name}"
            )
        
        routine = self.routines[routine_name]
        
        if not routine.enabled:
            return Response(
                text=f"Routine '{routine_name}' is disabled.",
                error_message=f"Routine disabled: {routine_name}"
            )
        
        # Check if routine is already running
        if routine_name in self.running_routines and self.running_routines[routine_name].is_alive():
            return Response(
                text=f"Routine '{routine_name}' is already running.",
                error_message=f"Routine already running: {routine_name}"
            )
        
        # Start routine execution in separate thread
        thread = threading.Thread(target=self._execute_routine_steps, args=(routine,))
        thread.daemon = True
        thread.start()
        
        self.running_routines[routine_name] = thread
        
        return Response(
            text=f"Starting routine '{routine_name}' with {len(routine.steps)} steps.",
            action_taken=True
        )    

    def _execute_routine_steps(self, routine: Routine) -> None:
        """
        Execute all steps in a routine with proper delays
        
        Args:
            routine: Routine object to execute
        """
        logger.info(f"Executing routine: {routine.name}")
        
        try:
            for i, step in enumerate(routine.steps):
                # Apply delay before executing step
                if step.delay > 0:
                    time.sleep(step.delay)
                
                logger.info(f"Executing step {i+1}/{len(routine.steps)}: {step.command}")
                
                # Create command object for this step
                command = Command(
                    intent=step.command,
                    entities=step.parameters,
                    confidence=1.0,
                    raw_text=f"routine_step_{step.command}",
                    timestamp=datetime.now()
                )
                
                # Execute command through router if available
                if self.command_router:
                    try:
                        response = self.command_router.route_command(command)
                        logger.info(f"Step {i+1} completed: {response.text[:100]}...")
                    except Exception as e:
                        logger.error(f"Error executing step {i+1}: {e}")
                        continue
                else:
                    logger.warning("No command router available for routine execution")
            
            # Update last executed time
            routine.last_executed = datetime.now()
            self._save_routines()
            
            logger.info(f"Routine '{routine.name}' completed successfully")
            
        except Exception as e:
            logger.error(f"Error executing routine '{routine.name}': {e}")
        finally:
            # Remove from running routines
            if routine.name in self.running_routines:
                del self.running_routines[routine.name]
    
    def schedule_routine(self, routine_name: str, schedule_type: str, schedule_time: str, task_name: str = None) -> bool:
        """
        Schedule a routine to run at specific times
        
        Args:
            routine_name: Name of routine to schedule
            schedule_type: Type of schedule ('daily', 'weekly', 'monthly')
            schedule_time: Time string like "08:00" or day specification
            task_name: Optional custom name for the scheduled task
            
        Returns:
            True if task was scheduled successfully
        """
        if routine_name not in self.routines:
            logger.error(f"Cannot schedule unknown routine: {routine_name}")
            return False
        
        if not task_name:
            task_name = f"{routine_name}_{schedule_type}_{schedule_time.replace(':', '')}"
        
        try:
            task = ScheduledTask(
                name=task_name,
                routine_name=routine_name,
                schedule_type=schedule_type,
                schedule_time=schedule_time
            )
            
            self.scheduled_tasks[task_name] = task
            self._save_scheduled_tasks()
            
            # Add to scheduler
            self._add_to_scheduler(task)
            
            logger.info(f"Scheduled routine '{routine_name}' as task '{task_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling routine: {e}")
            return False
    
    def _add_to_scheduler(self, task: ScheduledTask) -> None:
        """Add a task to the scheduler"""
        if not task.enabled:
            return
        
        try:
            # Simple scheduler implementation without external dependencies
            # In a real implementation, you'd use a proper scheduler like APScheduler
            logger.info(f"Task {task.name} would be scheduled for {task.schedule_type} at {task.schedule_time}")
            
        except Exception as e:
            logger.error(f"Error adding task to scheduler: {e}")
    
    def _execute_scheduled_task(self, task_name: str) -> None:
        """Execute a scheduled task"""
        if task_name not in self.scheduled_tasks:
            logger.error(f"Scheduled task not found: {task_name}")
            return
        
        task = self.scheduled_tasks[task_name]
        
        if not task.enabled:
            return
        
        logger.info(f"Executing scheduled task: {task_name}")
        
        # Execute the associated routine
        response = self.execute_routine(task.routine_name)
        
        # Update last executed time
        task.last_executed = datetime.now()
        self._save_scheduled_tasks()
        
        logger.info(f"Scheduled task '{task_name}' completed")
    
    def _start_scheduler(self) -> None:
        """Start the background scheduler thread"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        # Add all existing tasks to scheduler
        for task in self.scheduled_tasks.values():
            self._add_to_scheduler(task)
        
        # Start scheduler thread (simplified version)
        def run_scheduler():
            while self.scheduler_running:
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Routine scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the background scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2)
        logger.info("Routine scheduler stopped")
    
    def list_routines(self) -> List[Dict[str, Any]]:
        """Get list of all available routines"""
        routines_list = []
        for routine in self.routines.values():
            routines_list.append({
                'name': routine.name,
                'description': routine.description,
                'steps': len(routine.steps),
                'enabled': routine.enabled,
                'last_executed': routine.last_executed.isoformat() if routine.last_executed else None
            })
        return routines_list
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled tasks"""
        tasks_list = []
        for task in self.scheduled_tasks.values():
            tasks_list.append({
                'name': task.name,
                'routine_name': task.routine_name,
                'schedule_type': task.schedule_type,
                'schedule_time': task.schedule_time,
                'enabled': task.enabled,
                'last_executed': task.last_executed.isoformat() if task.last_executed else None
            })
        return tasks_list
    
    def get_routine_status(self) -> Dict[str, Any]:
        """Get overall status of routine engine"""
        return {
            'total_routines': len(self.routines),
            'enabled_routines': sum(1 for r in self.routines.values() if r.enabled),
            'running_routines': len(self.running_routines),
            'scheduled_tasks': len(self.scheduled_tasks),
            'enabled_tasks': sum(1 for t in self.scheduled_tasks.values() if t.enabled),
            'scheduler_running': self.scheduler_running
        }