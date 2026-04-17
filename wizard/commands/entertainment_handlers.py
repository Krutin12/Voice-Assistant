"""
Entertainment Handlers Module

This module handles entertainment-related voice commands including jokes,
fun facts, trivia, and interactive games for the Wizard voice assistant.
"""

import re
from typing import Dict, Any, Optional, List
from ..data.entertainment_data import entertainment_db, interactive_games, recommendation_engine
from .command_router import Response


class EntertainmentHandlers:
    """Handles entertainment-related commands."""
    
    def __init__(self):
        self.entertainment_db = entertainment_db
        self.games = interactive_games
        
    def handle_joke_request(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle requests for jokes."""
        try:
            # Extract category if specified
            category = entities.get('category')
            if not category:
                # Try to extract category from command text
                category_patterns = {
                    r'\b(programming|code|coding|tech|computer)\b': 'programming',
                    r'\b(dad|father)\b': 'dad',
                    r'\b(general|random|any)\b': 'general',
                    r'\b(technology|tech)\b': 'tech'
                }
                
                for pattern, cat in category_patterns.items():
                    if re.search(pattern, command_text.lower()):
                        category = cat
                        break
            
            joke = self.entertainment_db.get_random_joke(category)
            
            response_text = f"Here's a {joke.category} joke for you: {joke.setup} ... {joke.punchline}"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"last_joke_category": joke.category}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I couldn't find a joke right now. Maybe I need to work on my sense of humor!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_fun_fact_request(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle requests for fun facts."""
        try:
            # Extract category if specified
            category = entities.get('category')
            if not category:
                # Try to extract category from command text
                category_patterns = {
                    r'\b(science|scientific|biology|chemistry|physics)\b': 'science',
                    r'\b(technology|tech|computer|digital)\b': 'technology',
                    r'\b(history|historical|ancient)\b': 'history',
                    r'\b(nature|animal|animals|wildlife)\b': 'nature',
                    r'\b(space|astronomy|universe|planet)\b': 'space'
                }
                
                for pattern, cat in category_patterns.items():
                    if re.search(pattern, command_text.lower()):
                        category = cat
                        break
            
            fact = self.entertainment_db.get_random_fun_fact(category)
            
            response_text = f"Here's a fun {fact.category} fact: {fact.fact}"
            if fact.source:
                response_text += f" (Source: {fact.source})"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"last_fact_category": fact.category}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I couldn't retrieve a fun fact right now. Let me gather more interesting information!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_trivia_request(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle requests for trivia questions."""
        try:
            # Extract category and difficulty if specified
            category = entities.get('category')
            difficulty = entities.get('difficulty')
            
            if not category:
                # Try to extract category from command text
                category_patterns = {
                    r'\b(geography|countries|cities|capitals)\b': 'geography',
                    r'\b(science|scientific|biology|chemistry)\b': 'science',
                    r'\b(history|historical)\b': 'history',
                    r'\b(sports|sport|athletics)\b': 'sports',
                    r'\b(literature|books|authors)\b': 'literature',
                    r'\b(technology|tech|computer)\b': 'technology'
                }
                
                for pattern, cat in category_patterns.items():
                    if re.search(pattern, command_text.lower()):
                        category = cat
                        break
            
            if not difficulty:
                # Try to extract difficulty from command text
                if re.search(r'\b(easy|simple|basic)\b', command_text.lower()):
                    difficulty = 'easy'
                elif re.search(r'\b(hard|difficult|challenging)\b', command_text.lower()):
                    difficulty = 'hard'
                elif re.search(r'\b(medium|moderate)\b', command_text.lower()):
                    difficulty = 'medium'
            
            question = self.entertainment_db.get_trivia_question(category, difficulty)
            
            response_text = f"Here's a {question.difficulty} {question.category} trivia question: {question.question}"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={
                    "trivia_answer": question.answer,
                    "trivia_category": question.category,
                    "trivia_difficulty": question.difficulty,
                    "awaiting_trivia_answer": True
                }
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I couldn't find a trivia question right now. Let me think of something interesting to ask!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_trivia_answer(self, command_text: str, entities: Dict[str, Any], context: Dict[str, Any]) -> Response:
        """Handle trivia answer submissions."""
        try:
            correct_answer = context.get("trivia_answer", "").lower()
            user_answer = command_text.lower().strip()
            
            if not correct_answer:
                return Response(
                    text="I don't have a trivia question pending. Would you like me to ask you one?",
                    action_taken=False
                )
            
            # Simple answer matching (could be enhanced with fuzzy matching)
            if correct_answer in user_answer or user_answer in correct_answer:
                response_text = f"Correct! The answer is {context.get('trivia_answer')}. Great job!"
            else:
                response_text = f"Not quite right. The correct answer is {context.get('trivia_answer')}. Better luck next time!"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={
                    "trivia_answer": None,
                    "awaiting_trivia_answer": False
                }
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I had trouble checking your answer. Let's try another question!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_coin_flip(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle coin flip requests."""
        try:
            result = self.games.flip_coin()
            
            return Response(
                text=result["message"],
                action_taken=True,
                context_updates={"last_coin_flip": result["result"]}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I seem to have lost my coin! Let me find another one.",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_dice_roll(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle dice roll requests."""
        try:
            # Extract number of dice and sides from entities or command text
            num_dice = entities.get('number', 1)
            sides = entities.get('sides', 6)
            
            # Try to extract from command text if not in entities
            if num_dice == 1:
                dice_match = re.search(r'(\d+)\s*dice?', command_text.lower())
                if dice_match:
                    num_dice = int(dice_match.group(1))
            
            if sides == 6:
                sides_match = re.search(r'(\d+)\s*sided?', command_text.lower())
                if sides_match:
                    sides = int(sides_match.group(1))
            
            result = self.games.roll_dice(num_dice, sides)
            
            return Response(
                text=result["message"],
                action_taken=True,
                context_updates={"last_dice_roll": result}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, my dice seem to have rolled away! Let me find them.",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_number_generation(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle random number generation requests."""
        try:
            # Extract range from entities or command text
            min_num = entities.get('min_number', 1)
            max_num = entities.get('max_number', 100)
            
            # Try to extract range from command text
            range_match = re.search(r'between\s+(\d+)\s+and\s+(\d+)', command_text.lower())
            if range_match:
                min_num = int(range_match.group(1))
                max_num = int(range_match.group(2))
            else:
                # Look for "from X to Y" pattern
                from_to_match = re.search(r'from\s+(\d+)\s+to\s+(\d+)', command_text.lower())
                if from_to_match:
                    min_num = int(from_to_match.group(1))
                    max_num = int(from_to_match.group(2))
            
            result = self.games.generate_number(min_num, max_num)
            
            return Response(
                text=result["message"],
                action_taken=True,
                context_updates={"last_generated_number": result}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, my random number generator is having trouble. Let me recalibrate it!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_magic_8_ball(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle Magic 8-Ball requests."""
        try:
            result = self.games.magic_8_ball()
            
            return Response(
                text=result["message"],
                action_taken=True,
                context_updates={"last_8_ball_response": result["response"]}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, the Magic 8-Ball is cloudy right now. Try asking again later!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_rock_paper_scissors(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle Rock, Paper, Scissors game."""
        try:
            # Extract user choice from entities or command text
            user_choice = entities.get('choice')
            
            if not user_choice:
                # Try to extract choice from command text, but not if it's just the game name
                if "rock paper scissors" not in command_text.lower():
                    choice_patterns = {
                        r'\brock\b': 'rock',
                        r'\bpaper\b': 'paper',
                        r'\bscissors?\b': 'scissors'
                    }
                    
                    for pattern, choice in choice_patterns.items():
                        if re.search(pattern, command_text.lower()):
                            user_choice = choice
                            break
            
            if not user_choice:
                return Response(
                    text="Please choose rock, paper, or scissors to play!",
                    action_taken=False
                )
            
            result = self.games.rock_paper_scissors(user_choice)
            
            if "error" in result:
                return Response(
                    text=result["message"],
                    action_taken=False,
                    error_message=result["error"]
                )
            
            return Response(
                text=result["message"],
                action_taken=True,
                context_updates={"last_rps_game": result}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I'm having trouble with the game. Let's try again!",
                action_taken=False,
                error_message=str(e)
            )
    
    def get_entertainment_categories(self) -> Dict[str, List[str]]:
        """Get available entertainment categories."""
        return {
            "jokes": self.entertainment_db.get_joke_categories(),
            "facts": self.entertainment_db.get_fact_categories(),
            "trivia": self.entertainment_db.get_trivia_categories(),
            "movies": self.entertainment_db.get_movie_genres(),
            "music": self.entertainment_db.get_music_genres(),
            "riddles": self.entertainment_db.get_riddle_categories(),
            "quotes": self.entertainment_db.get_quote_categories()
        }
    
    def handle_entertainment_help(self) -> Response:
        """Provide help for entertainment commands."""
        help_text = """I can entertain you with:
        
• Jokes: "Tell me a joke" or "Tell me a programming joke"
• Fun Facts: "Tell me a fun fact" or "Give me a science fact"
• Trivia: "Ask me a trivia question" or "Give me an easy history question"
• Games: "Flip a coin", "Roll dice", "Generate a number", "Magic 8-Ball", "Rock paper scissors"
• Movie Recommendations: "Recommend a movie" or "Suggest an action movie"
• Music Recommendations: "Recommend music" or "Suggest some rock music"
• Riddles: "Give me a riddle" or "Ask me an easy riddle"
• Quotes & Tips: "Give me a motivational quote" or "Daily tip"

Available categories:
• Jokes: programming, general, dad, tech
• Facts: science, technology, history, nature, space
• Trivia: geography, science, history, sports, literature, technology
• Movies: Action, Comedy, Drama, Sci-Fi, Animation, Family
• Music: Pop, Rock, Hip-Hop, Electronic, Alternative
• Riddles: wordplay, nature, geography, logic
• Quotes: motivational, daily_tip, wisdom, success

Just ask and I'll entertain you!"""
        
        return Response(
            text=help_text,
            action_taken=True
        )
    
    def handle_movie_recommendation(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle movie recommendation requests."""
        try:
            # Extract genre if specified
            genre = entities.get('genre')
            if not genre:
                # Try to extract genre from command text
                genre_patterns = {
                    r'\b(action|adventure)\b': 'Action',
                    r'\b(comedy|funny|humor)\b': 'Comedy',
                    r'\b(drama|dramatic)\b': 'Drama',
                    r'\b(sci-?fi|science fiction)\b': 'Sci-Fi',
                    r'\b(horror|scary)\b': 'Horror',
                    r'\b(romance|romantic)\b': 'Romance',
                    r'\b(thriller|suspense)\b': 'Thriller',
                    r'\b(animation|animated|cartoon)\b': 'Animation',
                    r'\b(family|kids?)\b': 'Family'
                }
                
                for pattern, g in genre_patterns.items():
                    if re.search(pattern, command_text.lower()):
                        genre = g
                        break
            
            # Get recommendation
            if "personalized" in command_text.lower() or "for me" in command_text.lower():
                movie = recommendation_engine.get_personalized_movie_recommendation()
            else:
                movie = entertainment_db.get_movie_recommendation(genre)
            
            response_text = f"I recommend '{movie.title}' ({movie.year}). It's a {movie.genre} movie rated {movie.rating}. {movie.description}"
            
            if movie.director:
                response_text += f" Directed by {movie.director}."
            
            if movie.cast:
                response_text += f" Starring {', '.join(movie.cast[:2])}."
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"last_movie_recommendation": movie.title}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I couldn't find a movie recommendation right now. Let me update my movie database!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_music_recommendation(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle music recommendation requests."""
        try:
            # Extract genre if specified
            genre = entities.get('genre')
            if not genre:
                # Try to extract genre from command text
                genre_patterns = {
                    r'\b(pop|popular)\b': 'Pop',
                    r'\b(rock|rock and roll)\b': 'Rock',
                    r'\b(hip-?hop|rap)\b': 'Hip-Hop',
                    r'\b(electronic|edm|dance)\b': 'Electronic',
                    r'\b(alternative|indie)\b': 'Alternative',
                    r'\b(jazz)\b': 'Jazz',
                    r'\b(classical)\b': 'Classical',
                    r'\b(country)\b': 'Country'
                }
                
                for pattern, g in genre_patterns.items():
                    if re.search(pattern, command_text.lower()):
                        genre = g
                        break
            
            # Get recommendation
            if "personalized" in command_text.lower() or "for me" in command_text.lower():
                music = recommendation_engine.get_personalized_music_recommendation()
            else:
                music = entertainment_db.get_music_recommendation(genre)
            
            response_text = f"I recommend '{music.title}' by {music.artist}. It's a {music.genre} song"
            
            if music.album:
                response_text += f" from the album '{music.album}'"
            
            if music.year:
                response_text += f" ({music.year})"
            
            response_text += f". {music.description}"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"last_music_recommendation": music.title}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I couldn't find a music recommendation right now. Let me tune up my music database!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_riddle_request(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle riddle requests."""
        try:
            # Extract difficulty and category if specified
            difficulty = entities.get('difficulty')
            category = entities.get('category')
            
            if not difficulty:
                # Try to extract difficulty from command text
                if re.search(r'\b(easy|simple|basic)\b', command_text.lower()):
                    difficulty = 'easy'
                elif re.search(r'\b(hard|difficult|challenging)\b', command_text.lower()):
                    difficulty = 'hard'
                elif re.search(r'\b(medium|moderate)\b', command_text.lower()):
                    difficulty = 'medium'
            
            riddle = entertainment_db.get_riddle(difficulty, category)
            
            response_text = f"Here's a {riddle.difficulty} riddle for you: {riddle.question}"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={
                    "riddle_answer": riddle.answer,
                    "riddle_hint": riddle.hint,
                    "riddle_difficulty": riddle.difficulty,
                    "awaiting_riddle_answer": True
                }
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I couldn't think of a riddle right now. Let me puzzle over this!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_riddle_answer(self, command_text: str, entities: Dict[str, Any], context: Dict[str, Any]) -> Response:
        """Handle riddle answer submissions."""
        try:
            correct_answer = context.get("riddle_answer", "").lower()
            user_answer = command_text.lower().strip()
            
            if not correct_answer:
                return Response(
                    text="I don't have a riddle pending. Would you like me to give you one?",
                    action_taken=False
                )
            
            # Simple answer matching (could be enhanced with fuzzy matching)
            if correct_answer in user_answer or user_answer in correct_answer:
                response_text = f"Excellent! The answer is {context.get('riddle_answer')}. You solved it!"
            else:
                hint = context.get('riddle_hint')
                response_text = f"Not quite right. "
                if hint:
                    response_text += f"Here's a hint: {hint}. "
                response_text += f"The answer is {context.get('riddle_answer')}. Better luck next time!"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={
                    "riddle_answer": None,
                    "awaiting_riddle_answer": False
                }
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I had trouble checking your answer. Let's try another riddle!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_quote_request(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle motivational quote and daily tip requests."""
        try:
            # Extract category if specified
            category = entities.get('category')
            if not category:
                # Try to extract category from command text
                category_patterns = {
                    r'\b(motivational|motivation|inspire|inspiring)\b': 'motivational',
                    r'\b(daily tip|tip|advice|helpful)\b': 'daily_tip',
                    r'\b(wisdom|wise|philosophical)\b': 'wisdom',
                    r'\b(success|successful|achievement)\b': 'success'
                }
                
                for pattern, cat in category_patterns.items():
                    if re.search(pattern, command_text.lower()):
                        category = cat
                        break
            
            quote = entertainment_db.get_quote(category)
            
            response_text = f"Here's a {quote.category.replace('_', ' ')} quote"
            if quote.author:
                response_text += f" from {quote.author}"
            response_text += f": '{quote.text}'"
            
            if quote.source and quote.author:
                response_text += f" (Source: {quote.source})"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"last_quote_category": quote.category}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I couldn't find an inspiring quote right now. Let me gather some wisdom!",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_daily_tip(self, command_text: str, entities: Dict[str, Any]) -> Response:
        """Handle daily tip requests specifically."""
        try:
            tip = entertainment_db.get_quote("daily_tip")
            
            response_text = f"Here's your daily tip: {tip.text}"
            
            if tip.source:
                response_text += f" (Source: {tip.source})"
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"last_daily_tip": tip.text}
            )
            
        except Exception as e:
            return Response(
                text="Sorry, I don't have a tip ready right now. Check back later!",
                action_taken=False,
                error_message=str(e)
            )