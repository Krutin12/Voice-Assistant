"""
Media Command Handlers

Handles voice commands related to media control, volume management,
and audio device operations for the Wizard AI Assistant.
"""

import sys
import logging
from typing import Dict, Any, Optional
from .command_router import Command, Response
from .media_controller import MediaController, create_media_controller

logger = logging.getLogger(__name__)


class MediaHandlers:
    """
    Collection of command handlers for media-related voice commands.
    
    Integrates with MediaController to provide voice control for:
    - Volume adjustment and muting
    - Media playback control
    - Application launching and control
    - Audio device management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize media handlers.
        
        Args:
            config: Configuration dictionary for media controller
        """
        self.config = config or {}
        self.media_controller = create_media_controller(config)
        self.logger = logging.getLogger(__name__)
        
        # Default media app preference
        self.default_music_app = self.config.get("default_music_app", "spotify")
        
        self.logger.info("Media handlers initialized")
    
    def handle_set_volume(self, command: Command) -> Response:
        """
        Handle volume setting commands.
        
        Examples:
        - "Set volume to 50"
        - "Volume 75"
        - "Change volume to 25"
        """
        try:
            volume_level = command.entities.get("volume_level")
            
            if volume_level is None:
                # Try to extract from numbers
                numbers = command.entities.get("numbers", [])
                if numbers:
                    volume_level = numbers[0]
            
            if volume_level is None:
                return Response(
                    text="I didn't catch the volume level. Please specify a number between 0 and 100.",
                    error_message="No volume level specified"
                )
            
            if not 0 <= volume_level <= 100:
                return Response(
                    text=f"Volume level must be between 0 and 100. You said {volume_level}.",
                    error_message="Invalid volume level"
                )
            
            success = self.media_controller.set_volume(volume_level)
            
            if success:
                return Response(
                    text=f"Volume set to {volume_level} percent.",
                    action_taken=True,
                    context_updates={"last_volume": volume_level}
                )
            else:
                return Response(
                    text="Sorry, I couldn't change the volume. There might be an audio system issue.",
                    error_message="Failed to set volume"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling set volume command: {e}")
            return Response(
                text="Sorry, I encountered an error while changing the volume.",
                error_message=str(e)
            )
    
    def handle_volume_up(self, command: Command) -> Response:
        """
        Handle volume increase commands.
        
        Examples:
        - "Volume up"
        - "Increase volume"
        - "Turn up volume"
        - "Louder"
        """
        try:
            # Default increment is 10%, but check for specific amounts
            increment = 10
            numbers = command.entities.get("numbers", [])
            if numbers:
                increment = numbers[0]
            
            success = self.media_controller.adjust_volume(increment)
            
            if success:
                current_volume = self.media_controller.get_current_volume()
                return Response(
                    text=f"Volume increased. Now at {current_volume} percent.",
                    action_taken=True,
                    context_updates={"last_volume": current_volume}
                )
            else:
                return Response(
                    text="Sorry, I couldn't increase the volume.",
                    error_message="Failed to increase volume"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling volume up command: {e}")
            return Response(
                text="Sorry, I encountered an error while increasing the volume.",
                error_message=str(e)
            )
    
    def handle_volume_down(self, command: Command) -> Response:
        """
        Handle volume decrease commands.
        
        Examples:
        - "Volume down"
        - "Decrease volume"
        - "Turn down volume"
        - "Quieter"
        """
        try:
            # Default decrement is 10%, but check for specific amounts
            decrement = -10
            numbers = command.entities.get("numbers", [])
            if numbers:
                decrement = -numbers[0]
            
            success = self.media_controller.adjust_volume(decrement)
            
            if success:
                current_volume = self.media_controller.get_current_volume()
                return Response(
                    text=f"Volume decreased. Now at {current_volume} percent.",
                    action_taken=True,
                    context_updates={"last_volume": current_volume}
                )
            else:
                return Response(
                    text="Sorry, I couldn't decrease the volume.",
                    error_message="Failed to decrease volume"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling volume down command: {e}")
            return Response(
                text="Sorry, I encountered an error while decreasing the volume.",
                error_message=str(e)
            )
    
    def handle_mute(self, command: Command) -> Response:
        """
        Handle mute commands.
        
        Examples:
        - "Mute"
        - "Silence"
        - "Turn off sound"
        """
        try:
            success = self.media_controller.mute()
            
            if success:
                return Response(
                    text="Audio muted.",
                    action_taken=True,
                    context_updates={"audio_muted": True}
                )
            else:
                return Response(
                    text="Sorry, I couldn't mute the audio.",
                    error_message="Failed to mute audio"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling mute command: {e}")
            return Response(
                text="Sorry, I encountered an error while muting the audio.",
                error_message=str(e)
            )
    
    def handle_unmute(self, command: Command) -> Response:
        """
        Handle unmute commands.
        
        Examples:
        - "Unmute"
        - "Turn on sound"
        """
        try:
            success = self.media_controller.unmute()
            
            if success:
                current_volume = self.media_controller.get_current_volume()
                return Response(
                    text=f"Audio unmuted. Volume is at {current_volume} percent.",
                    action_taken=True,
                    context_updates={"audio_muted": False}
                )
            else:
                return Response(
                    text="Sorry, I couldn't unmute the audio.",
                    error_message="Failed to unmute audio"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling unmute command: {e}")
            return Response(
                text="Sorry, I encountered an error while unmuting the audio.",
                error_message=str(e)
            )
    
    def handle_play_music(self, command: Command) -> Response:
        """
        Handle music playback commands.
        
        Examples:
        - "Play music"
        - "Play Bohemian Rhapsody"
        - "Start playing The Beatles"
        - "Put on some jazz"
        """
        try:
            query = command.entities.get("query", "").strip()
            
            if query:
                # Search and play specific content
                success = self.media_controller.search_and_play(query, self.default_music_app)
                
                if success:
                    return Response(
                        text=f"Playing '{query}' on {self.default_music_app.title()}.",
                        action_taken=True,
                        context_updates={"last_played": query, "media_app": self.default_music_app}
                    )
                else:
                    return Response(
                        text=f"Sorry, I couldn't find or play '{query}'. Make sure {self.default_music_app.title()} is available.",
                        error_message="Failed to search and play content"
                    )
            else:
                # Just resume playback
                success = self.media_controller.control_playback("play")
                
                if success:
                    return Response(
                        text="Resuming playback.",
                        action_taken=True,
                        context_updates={"playback_state": "playing"}
                    )
                else:
                    return Response(
                        text="Sorry, I couldn't resume playback. Make sure a media app is open.",
                        error_message="Failed to resume playback"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error handling play music command: {e}")
            return Response(
                text="Sorry, I encountered an error while trying to play music.",
                error_message=str(e)
            )
    
    def handle_pause_music(self, command: Command) -> Response:
        """
        Handle music pause commands.
        
        Examples:
        - "Pause"
        - "Stop playing"
        - "Pause music"
        """
        try:
            success = self.media_controller.control_playback("pause")
            
            if success:
                return Response(
                    text="Music paused.",
                    action_taken=True,
                    context_updates={"playback_state": "paused"}
                )
            else:
                return Response(
                    text="Sorry, I couldn't pause the music. Make sure a media app is playing.",
                    error_message="Failed to pause playback"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling pause music command: {e}")
            return Response(
                text="Sorry, I encountered an error while trying to pause music.",
                error_message=str(e)
            )
    
    def handle_next_track(self, command: Command) -> Response:
        """
        Handle next track commands.
        
        Examples:
        - "Next song"
        - "Skip song"
        - "Next track"
        """
        try:
            success = self.media_controller.control_playback("next")
            
            if success:
                return Response(
                    text="Skipped to next track.",
                    action_taken=True,
                    context_updates={"playback_action": "next"}
                )
            else:
                return Response(
                    text="Sorry, I couldn't skip to the next track. Make sure a media app is playing.",
                    error_message="Failed to skip track"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling next track command: {e}")
            return Response(
                text="Sorry, I encountered an error while trying to skip to the next track.",
                error_message=str(e)
            )
    
    def handle_previous_track(self, command: Command) -> Response:
        """
        Handle previous track commands.
        
        Examples:
        - "Previous song"
        - "Last song"
        - "Previous track"
        """
        try:
            success = self.media_controller.control_playback("previous")
            
            if success:
                return Response(
                    text="Went back to previous track.",
                    action_taken=True,
                    context_updates={"playback_action": "previous"}
                )
            else:
                return Response(
                    text="Sorry, I couldn't go to the previous track. Make sure a media app is playing.",
                    error_message="Failed to go to previous track"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling previous track command: {e}")
            return Response(
                text="Sorry, I encountered an error while trying to go to the previous track.",
                error_message=str(e)
            )
    
    def handle_open_media_app(self, command: Command) -> Response:
        """
        Handle media application opening commands.
        
        Examples:
        - "Open Spotify"
        - "Launch YouTube Music"
        - "Start VLC"
        - "Open Apple Music"
        """
        try:
            app_name = command.entities.get("application", "").lower()
            
            if not app_name:
                return Response(
                    text="I didn't catch which media app you want to open. Please specify an app like Spotify, YouTube Music, Apple Music, or VLC.",
                    error_message="No application specified"
                )
            
            # Enhanced app mapping with more alternatives
            app_mapping = {
                "spotify": "spotify",
                "youtube music": "youtube_music",
                "youtube": "youtube_music",
                "yt music": "youtube_music",
                "vlc": "vlc",
                "vlc player": "vlc",
                "vlc media player": "vlc",
                "apple music": "apple_music",
                "music": "apple_music" if sys.platform == "darwin" else "windows_media_player",
                "itunes": "itunes",
                "windows media player": "windows_media_player",
                "media player": "windows_media_player",
                "wmp": "windows_media_player"
            }
            
            mapped_app = app_mapping.get(app_name, app_name)
            
            success = self.media_controller.open_media_app(mapped_app)
            
            if success:
                return Response(
                    text=f"Opening {app_name.title()}.",
                    action_taken=True,
                    context_updates={"opened_app": app_name, "media_app": mapped_app}
                )
            else:
                return Response(
                    text=f"Sorry, I couldn't open {app_name.title()}. Make sure it's installed on your system.",
                    error_message=f"Failed to open {app_name}"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling open media app command: {e}")
            return Response(
                text="Sorry, I encountered an error while trying to open the media app.",
                error_message=str(e)
            )
    
    def handle_get_volume_status(self, command: Command) -> Response:
        """
        Handle volume status inquiry commands.
        
        Examples:
        - "What's the volume?"
        - "Current volume level"
        - "Volume status"
        """
        try:
            volume_state = self.media_controller.get_volume_state()
            
            if volume_state.is_muted:
                status_text = f"Audio is currently muted. Volume was at {volume_state.level} percent."
            else:
                status_text = f"Volume is currently at {volume_state.level} percent."
            
            return Response(
                text=status_text,
                action_taken=False,
                context_updates={"volume_level": volume_state.level, "is_muted": volume_state.is_muted}
            )
            
        except Exception as e:
            self.logger.error(f"Error handling volume status command: {e}")
            return Response(
                text="Sorry, I couldn't check the volume status.",
                error_message=str(e)
            )
    
    def handle_get_media_status(self, command: Command) -> Response:
        """
        Handle media status inquiry commands.
        
        Examples:
        - "What's playing?"
        - "Media status"
        - "What music apps are running?"
        """
        try:
            media_status = self.media_controller.get_media_status()
            
            volume = media_status.get("volume", "unknown")
            is_muted = media_status.get("is_muted", False)
            active_apps = media_status.get("active_apps", [])
            
            status_parts = []
            
            # Volume status
            if is_muted:
                status_parts.append("Audio is muted")
            else:
                status_parts.append(f"Volume is at {volume} percent")
            
            # Active media apps
            if active_apps:
                apps_text = ", ".join(active_apps)
                status_parts.append(f"Running media apps: {apps_text}")
            else:
                status_parts.append("No media apps are currently running")
            
            status_text = ". ".join(status_parts) + "."
            
            return Response(
                text=status_text,
                action_taken=False,
                context_updates=media_status
            )
            
        except Exception as e:
            self.logger.error(f"Error handling media status command: {e}")
            return Response(
                text="Sorry, I couldn't check the media status.",
                error_message=str(e)
            )
    
    def handle_set_audio_device(self, command: Command) -> Response:
        """
        Handle audio device selection commands.
        
        Examples:
        - "Switch to speakers"
        - "Use headphones"
        - "Change audio device to Bluetooth"
        """
        try:
            device_name = command.entities.get("device_name", "").strip()
            
            if not device_name:
                # List available devices if no specific device mentioned
                devices = self.media_controller.get_audio_devices()
                devices_text = ", ".join(devices)
                return Response(
                    text=f"Available audio devices: {devices_text}. Please specify which device you'd like to use.",
                    action_taken=False,
                    context_updates={"available_devices": devices}
                )
            
            success = self.media_controller.set_audio_device(device_name)
            
            if success:
                return Response(
                    text=f"Audio device switched to {device_name}.",
                    action_taken=True,
                    context_updates={"current_audio_device": device_name}
                )
            else:
                devices = self.media_controller.get_audio_devices()
                devices_text = ", ".join(devices)
                return Response(
                    text=f"Sorry, I couldn't switch to '{device_name}'. Available devices: {devices_text}",
                    error_message=f"Failed to set audio device to {device_name}"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling set audio device command: {e}")
            return Response(
                text="Sorry, I encountered an error while changing the audio device.",
                error_message=str(e)
            )
    
    def handle_get_audio_devices(self, command: Command) -> Response:
        """
        Handle audio device listing commands.
        
        Examples:
        - "List audio devices"
        - "What audio devices are available?"
        - "Show me audio outputs"
        """
        try:
            devices = self.media_controller.get_audio_devices()
            
            if len(devices) == 1:
                return Response(
                    text=f"Currently using: {devices[0]}",
                    action_taken=False,
                    context_updates={"available_devices": devices}
                )
            else:
                devices_text = ", ".join(devices)
                return Response(
                    text=f"Available audio devices: {devices_text}",
                    action_taken=False,
                    context_updates={"available_devices": devices}
                )
                
        except Exception as e:
            self.logger.error(f"Error handling get audio devices command: {e}")
            return Response(
                text="Sorry, I couldn't list the audio devices.",
                error_message=str(e)
            )
    
    def handle_play_specific_content(self, command: Command) -> Response:
        """
        Handle commands to play specific songs, artists, or albums.
        
        Examples:
        - "Play Bohemian Rhapsody on Spotify"
        - "Search for The Beatles on YouTube Music"
        - "Play jazz music"
        - "Find Taylor Swift songs"
        """
        try:
            query = command.entities.get("query", "").strip()
            app_preference = command.entities.get("application", self.default_music_app).lower()
            
            if not query:
                return Response(
                    text="I didn't catch what you want to play. Please specify a song, artist, or album.",
                    error_message="No search query specified"
                )
            
            # Map app names
            app_mapping = {
                "spotify": "spotify",
                "youtube music": "youtube_music",
                "youtube": "youtube_music",
                "apple music": "apple_music",
                "itunes": "itunes",
                "vlc": "vlc"
            }
            
            mapped_app = app_mapping.get(app_preference, self.default_music_app)
            
            success = self.media_controller.search_and_play(query, mapped_app)
            
            if success:
                app_display_name = mapped_app.replace("_", " ").title()
                return Response(
                    text=f"Searching for '{query}' on {app_display_name}.",
                    action_taken=True,
                    context_updates={
                        "last_search": query, 
                        "media_app": mapped_app,
                        "playback_state": "searching"
                    }
                )
            else:
                return Response(
                    text=f"Sorry, I couldn't search for '{query}'. Make sure {mapped_app.replace('_', ' ').title()} is available.",
                    error_message="Failed to search and play content"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling play specific content command: {e}")
            return Response(
                text="Sorry, I encountered an error while trying to search for that content.",
                error_message=str(e)
            )


def register_media_handlers(command_router, config: Optional[Dict[str, Any]] = None):
    """
    Register all media command handlers with the command router.
    
    Args:
        command_router: CommandRouter instance to register handlers with
        config: Optional configuration for media handlers
    """
    handlers = MediaHandlers(config)
    
    # Volume control handlers
    command_router.register_handler("set_volume", handlers.handle_set_volume)
    command_router.register_handler("volume_up", handlers.handle_volume_up)
    command_router.register_handler("volume_down", handlers.handle_volume_down)
    command_router.register_handler("mute", handlers.handle_mute)
    command_router.register_handler("unmute", handlers.handle_unmute)
    
    # Media playback handlers
    command_router.register_handler("play_music", handlers.handle_play_music)
    command_router.register_handler("pause_music", handlers.handle_pause_music)
    command_router.register_handler("next_track", handlers.handle_next_track)
    command_router.register_handler("previous_track", handlers.handle_previous_track)
    command_router.register_handler("play_specific_content", handlers.handle_play_specific_content)
    
    # Media application handlers
    command_router.register_handler("open_media_app", handlers.handle_open_media_app)
    
    # Audio device management handlers
    command_router.register_handler("set_audio_device", handlers.handle_set_audio_device)
    command_router.register_handler("get_audio_devices", handlers.handle_get_audio_devices)
    
    # Status inquiry handlers
    command_router.register_handler("get_volume_status", handlers.handle_get_volume_status)
    command_router.register_handler("get_media_status", handlers.handle_get_media_status)
    
    logger.info("Media command handlers registered successfully")


# Convenience function for quick media control
def quick_volume_control(action: str, value: Optional[int] = None) -> bool:
    """
    Quick function for programmatic volume control.
    
    Args:
        action: "set", "up", "down", "mute", "unmute"
        value: Volume level for "set", increment for "up"/"down"
        
    Returns:
        True if successful, False otherwise
    """
    controller = create_media_controller()
    
    try:
        if action == "set" and value is not None:
            return controller.set_volume(value)
        elif action == "up":
            return controller.adjust_volume(value or 10)
        elif action == "down":
            return controller.adjust_volume(-(value or 10))
        elif action == "mute":
            return controller.mute()
        elif action == "unmute":
            return controller.unmute()
        else:
            return False
    except Exception:
        return False


def quick_media_control(action: str, content: str = "") -> bool:
    """
    Quick function for programmatic media control.
    
    Args:
        action: "play", "pause", "next", "previous", "stop"
        content: Optional content to search/play
        
    Returns:
        True if successful, False otherwise
    """
    controller = create_media_controller()
    
    try:
        if action == "play" and content:
            return controller.search_and_play(content)
        else:
            return controller.control_playback(action)
    except Exception:
        return False