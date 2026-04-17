"""
Information Services Module

This module handles local information services including weather data,
news headlines, sports scores, and movie information for the Wizard voice assistant.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from .command_router import Command, Response

logger = logging.getLogger(__name__)


class InformationServices:
    """Handles local information services and cached data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_dir = Path(config.get('data_directory', 'wizard/data'))
        self.cache_duration = config.get('cache_duration_hours', 24)
        
        # Initialize data storage
        self._initialize_data_files()
        
        # Load cached data
        self.weather_data = self._load_weather_data()
        self.news_data = self._load_news_data()
        self.sports_data = self._load_sports_data()
        self.movie_data = self._load_movie_data()
    
    def _initialize_data_files(self):
        """Initialize data files if they don't exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default data files
        default_files = {
            'weather_cache.json': self._get_default_weather_data(),
            'news_cache.json': self._get_default_news_data(),
            'sports_cache.json': self._get_default_sports_data(),
            'movie_cache.json': self._get_default_movie_data()
        }
        
        for filename, default_data in default_files.items():
            file_path = self.data_dir / filename
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=2)
    
    def handle_weather(self, command: Command) -> Response:
        """Handle weather information requests"""
        try:
            location = command.entities.get('location', 'current location')
            
            # Always provide weather information from cache/default data
            weather_info = self._get_current_weather(location)
            return Response(
                text=weather_info,
                action_taken=True,
                context_updates={'last_weather_check': datetime.now().isoformat()}
            )
                
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return Response(
                text="Sorry, I couldn't get the weather information right now.",
                error_message=str(e)
            )
    
    def handle_news(self, command: Command) -> Response:
        """Handle news headline requests"""
        try:
            category = command.entities.get('category', 'general')
            
            # Always provide news headlines from cache/default data
            headlines = self._get_news_headlines(category)
            return Response(
                text=headlines,
                action_taken=True,
                context_updates={'last_news_check': datetime.now().isoformat()}
            )
                
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return Response(
                text="Sorry, I couldn't get the news headlines right now.",
                error_message=str(e)
            )
    
    def handle_sports(self, command: Command) -> Response:
        """Handle sports scores and information requests"""
        try:
            sport = command.entities.get('sport', 'general')
            
            # Always provide sports scores from cache/default data
            scores = self._get_sports_scores(sport)
            return Response(
                text=scores,
                action_taken=True,
                context_updates={'last_sports_check': datetime.now().isoformat()}
            )
                
        except Exception as e:
            logger.error(f"Error getting sports information: {e}")
            return Response(
                text="Sorry, I couldn't get the sports information right now.",
                error_message=str(e)
            )
    
    def handle_movies(self, command: Command) -> Response:
        """Handle movie information requests"""
        try:
            query = command.entities.get('query', '')
            
            movie_info = self._get_movie_information(query)
            return Response(
                text=movie_info,
                action_taken=True,
                context_updates={'last_movie_search': query}
            )
                
        except Exception as e:
            logger.error(f"Error getting movie information: {e}")
            return Response(
                text="Sorry, I couldn't get the movie information right now.",
                error_message=str(e)
            )
    
    def _load_weather_data(self) -> Dict[str, Any]:
        """Load weather data from cache"""
        try:
            with open(self.data_dir / 'weather_cache.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading weather data: {e}")
            return self._get_default_weather_data()
    
    def _load_news_data(self) -> Dict[str, Any]:
        """Load news data from cache"""
        try:
            with open(self.data_dir / 'news_cache.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading news data: {e}")
            return self._get_default_news_data()
    
    def _load_sports_data(self) -> Dict[str, Any]:
        """Load sports data from cache"""
        try:
            with open(self.data_dir / 'sports_cache.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sports data: {e}")
            return self._get_default_sports_data()
    
    def _load_movie_data(self) -> Dict[str, Any]:
        """Load movie data from cache"""
        try:
            with open(self.data_dir / 'movie_cache.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading movie data: {e}")
            return self._get_default_movie_data()
    
    def _is_data_fresh(self, data: Dict[str, Any]) -> bool:
        """Check if cached data is still fresh"""
        try:
            last_update = datetime.fromisoformat(data.get('last_updated', '2000-01-01T00:00:00'))
            return (datetime.now() - last_update).total_seconds() < (self.cache_duration * 3600)
        except Exception:
            return False
    
    def _get_current_weather(self, location: str) -> str:
        """Get current weather information"""
        weather = self.weather_data.get('current', {})
        
        if not weather:
            return "I don't have weather information available right now."
        
        temperature = weather.get('temperature', 'unknown')
        condition = weather.get('condition', 'unknown')
        humidity = weather.get('humidity', 'unknown')
        wind_speed = weather.get('wind_speed', 'unknown')
        
        return (f"The current weather in {location} is {condition} with a temperature of "
                f"{temperature}°F. Humidity is {humidity}% and wind speed is {wind_speed} mph.")
    
    def _get_news_headlines(self, category: str) -> str:
        """Get news headlines for specified category"""
        headlines = self.news_data.get('headlines', {}).get(category, [])
        
        if not headlines:
            headlines = self.news_data.get('headlines', {}).get('general', [])
        
        if not headlines:
            return "I don't have any news headlines available right now."
        
        # Return top 3 headlines
        top_headlines = headlines[:3]
        result = f"Here are the top {category} news headlines: "
        
        for i, headline in enumerate(top_headlines, 1):
            result += f"{i}. {headline['title']}. "
        
        return result
    
    def _get_sports_scores(self, sport: str) -> str:
        """Get sports scores for specified sport"""
        scores = self.sports_data.get('scores', {}).get(sport, [])
        
        if not scores:
            scores = self.sports_data.get('scores', {}).get('general', [])
        
        if not scores:
            return "I don't have any sports scores available right now."
        
        # Return recent scores
        result = f"Here are recent {sport} scores: "
        
        for score in scores[:3]:
            result += f"{score['team1']} {score['score1']} - {score['score2']} {score['team2']}. "
        
        return result
    
    def _get_movie_information(self, query: str) -> str:
        """Get movie information"""
        movies = self.movie_data.get('movies', [])
        
        if query:
            # Search for specific movie or genre
            query_lower = query.lower()
            matching_movies = [
                movie for movie in movies 
                if query_lower in movie.get('title', '').lower() or 
                   query_lower in movie.get('genre', '').lower() or
                   any(word in movie.get('genre', '').lower() for word in query_lower.split())
            ]
            
            if matching_movies:
                movie = matching_movies[0]
                if len(matching_movies) == 1:
                    return (f"{movie['title']} is a {movie['genre']} movie from {movie['year']} "
                           f"with a rating of {movie['rating']}/10. {movie['description']}")
                else:
                    # Multiple matches, show the first one and mention others
                    result = (f"I found several matches. {movie['title']} is a {movie['genre']} movie from {movie['year']} "
                             f"with a rating of {movie['rating']}/10. {movie['description']}")
                    if len(matching_movies) > 1:
                        result += f" I also found {len(matching_movies) - 1} other matching movies."
                    return result
            else:
                return f"I couldn't find information about '{query}'. Try asking about a different movie or genre like adventure, comedy, mystery, science fiction, or romance."
        else:
            # Return random movie recommendation
            if movies:
                movie = random.choice(movies)
                return (f"I recommend '{movie['title']}', a {movie['genre']} movie from {movie['year']} "
                       f"with a rating of {movie['rating']}/10. {movie['description']}")
            else:
                return "I don't have any movie recommendations available right now."
    
    def _get_default_weather_data(self) -> Dict[str, Any]:
        """Get default weather data structure"""
        return {
            "last_updated": "2000-01-01T00:00:00",
            "current": {
                "temperature": 72,
                "condition": "partly cloudy",
                "humidity": 65,
                "wind_speed": 8
            },
            "forecast": [
                {"day": "Today", "high": 75, "low": 60, "condition": "sunny"},
                {"day": "Tomorrow", "high": 78, "low": 62, "condition": "partly cloudy"},
                {"day": "Day after", "high": 73, "low": 58, "condition": "cloudy"}
            ]
        }
    
    def _get_default_news_data(self) -> Dict[str, Any]:
        """Get default news data structure"""
        return {
            "last_updated": "2000-01-01T00:00:00",
            "headlines": {
                "general": [
                    {"title": "Local community center opens new programs", "source": "Local News"},
                    {"title": "Technology advances continue to shape daily life", "source": "Tech News"},
                    {"title": "Weather patterns show seasonal changes", "source": "Weather Service"}
                ],
                "technology": [
                    {"title": "New AI developments announced", "source": "Tech Today"},
                    {"title": "Software updates improve user experience", "source": "Digital News"},
                    {"title": "Cybersecurity measures enhanced", "source": "Security Weekly"}
                ],
                "sports": [
                    {"title": "Local teams prepare for upcoming season", "source": "Sports News"},
                    {"title": "Athletic programs expand community outreach", "source": "Community Sports"},
                    {"title": "Youth leagues show strong participation", "source": "Youth Sports"}
                ]
            }
        }
    
    def _get_default_sports_data(self) -> Dict[str, Any]:
        """Get default sports data structure"""
        return {
            "last_updated": "2000-01-01T00:00:00",
            "scores": {
                "general": [
                    {"team1": "Home Team", "score1": 3, "team2": "Away Team", "score2": 2, "sport": "soccer"},
                    {"team1": "Local Lions", "score1": 85, "team2": "City Eagles", "score2": 78, "sport": "basketball"},
                    {"team1": "Town Tigers", "score1": 7, "team2": "Metro Bears", "score2": 4, "sport": "baseball"}
                ],
                "football": [
                    {"team1": "Hometown Heroes", "score1": 21, "team2": "Rival Raiders", "score2": 14, "sport": "football"},
                    {"team1": "City Chargers", "score1": 28, "team2": "Metro Mustangs", "score2": 17, "sport": "football"}
                ],
                "basketball": [
                    {"team1": "Local Lions", "score1": 95, "team2": "City Eagles", "score2": 88, "sport": "basketball"},
                    {"team1": "Town Titans", "score1": 102, "team2": "Metro Mavericks", "score2": 97, "sport": "basketball"}
                ]
            }
        }
    
    def _get_default_movie_data(self) -> Dict[str, Any]:
        """Get default movie data structure"""
        return {
            "last_updated": datetime.now().isoformat(),
            "movies": [
                {
                    "title": "The Adventure Begins",
                    "year": 2023,
                    "genre": "adventure",
                    "rating": 8.2,
                    "description": "An exciting journey through unknown territories."
                },
                {
                    "title": "Comedy Central",
                    "year": 2023,
                    "genre": "comedy",
                    "rating": 7.5,
                    "description": "A hilarious story about everyday life situations."
                },
                {
                    "title": "Mystery Manor",
                    "year": 2022,
                    "genre": "mystery",
                    "rating": 8.7,
                    "description": "A thrilling mystery set in an old mansion."
                },
                {
                    "title": "Space Odyssey",
                    "year": 2023,
                    "genre": "science fiction",
                    "rating": 9.1,
                    "description": "An epic journey through the cosmos."
                },
                {
                    "title": "Romance in Paris",
                    "year": 2022,
                    "genre": "romance",
                    "rating": 7.8,
                    "description": "A beautiful love story set in the city of lights."
                }
            ]
        }


def register_information_handlers(router, config: Dict[str, Any]) -> None:
    """Register all information service handlers with the command router"""
    services = InformationServices(config)
    
    # Register handlers
    router.register_handler("weather", services.handle_weather)
    router.register_handler("news", services.handle_news)
    router.register_handler("sports", services.handle_sports)
    router.register_handler("movies", services.handle_movies)
    
    logger.info("Registered information service handlers")