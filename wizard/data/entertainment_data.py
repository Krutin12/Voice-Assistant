"""
Entertainment Data Module

This module provides entertainment content including jokes, fun facts, trivia,
and interactive games for the Wizard voice assistant.
"""

import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Joke:
    """Represents a joke with category and content."""
    category: str
    setup: str
    punchline: str
    rating: str = "G"  # G, PG, PG-13


@dataclass
class FunFact:
    """Represents a fun fact with category and content."""
    category: str
    fact: str
    source: Optional[str] = None


@dataclass
class TriviaQuestion:
    """Represents a trivia question with answer and difficulty."""
    category: str
    question: str
    answer: str
    difficulty: str  # easy, medium, hard
    options: Optional[List[str]] = None  # For multiple choice


@dataclass
class MovieRecommendation:
    """Represents a movie recommendation."""
    title: str
    genre: str
    year: int
    rating: str  # G, PG, PG-13, R
    description: str
    director: Optional[str] = None
    cast: Optional[List[str]] = None


@dataclass
class MusicRecommendation:
    """Represents a music recommendation."""
    title: str
    artist: str
    genre: str
    description: str
    album: Optional[str] = None
    year: Optional[int] = None


@dataclass
class Riddle:
    """Represents a riddle with answer and difficulty."""
    question: str
    answer: str
    difficulty: str  # easy, medium, hard
    category: str
    hint: Optional[str] = None


@dataclass
class Quote:
    """Represents a motivational quote or daily tip."""
    text: str
    category: str  # motivational, daily_tip, wisdom, success
    author: Optional[str] = None
    source: Optional[str] = None


class EntertainmentDatabase:
    """Manages entertainment content including jokes, facts, and trivia."""
    
    def __init__(self):
        self.jokes = self._load_jokes()
        self.fun_facts = self._load_fun_facts()
        self.trivia_questions = self._load_trivia()
        self.movie_recommendations = self._load_movies()
        self.music_recommendations = self._load_music()
        self.riddles = self._load_riddles()
        self.quotes = self._load_quotes()
        
    def _load_jokes(self) -> List[Joke]:
        """Load joke database."""
        return [
            # Programming Jokes
            Joke("programming", "Why do programmers prefer dark mode?", 
                  "Because light attracts bugs!", "G"),
            Joke("programming", "How many programmers does it take to change a light bulb?", 
                  "None, that's a hardware problem!", "G"),
            Joke("programming", "Why do Java developers wear glasses?", 
                  "Because they can't C#!", "G"),
            Joke("programming", "What's a programmer's favorite hangout place?", 
                  "Foo Bar!", "G"),
            
            # General Jokes
            Joke("general", "Why don't scientists trust atoms?", 
                  "Because they make up everything!", "G"),
            Joke("general", "What do you call a fake noodle?", 
                  "An impasta!", "G"),
            Joke("general", "Why did the scarecrow win an award?", 
                  "He was outstanding in his field!", "G"),
            Joke("general", "What do you call a bear with no teeth?", 
                  "A gummy bear!", "G"),
            
            # Dad Jokes
            Joke("dad", "I'm reading a book about anti-gravity.", 
                  "It's impossible to put down!", "G"),
            Joke("dad", "Did you hear about the mathematician who's afraid of negative numbers?", 
                  "He'll stop at nothing to avoid them!", "G"),
            Joke("dad", "Why don't eggs tell jokes?", 
                  "They'd crack each other up!", "G"),
            
            # Tech Jokes
            Joke("tech", "Why was the computer cold?", 
                  "It left its Windows open!", "G"),
            Joke("tech", "What do you call a computer superhero?", 
                  "A screensaver!", "G"),
            Joke("tech", "Why did the smartphone go to therapy?", 
                  "It had too many apps and couldn't find itself!", "G"),
        ]
    
    def _load_fun_facts(self) -> List[FunFact]:
        """Load fun facts database."""
        return [
            # Science Facts
            FunFact("science", "A group of flamingos is called a 'flamboyance'.", "National Geographic"),
            FunFact("science", "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.", "Smithsonian"),
            FunFact("science", "Octopuses have three hearts and blue blood.", "Marine Biology Institute"),
            FunFact("science", "A single cloud can weigh more than a million pounds.", "NOAA"),
            FunFact("science", "Bananas are berries, but strawberries aren't.", "Botanical Society"),
            
            # Technology Facts
            FunFact("technology", "The first computer bug was an actual bug - a moth trapped in a Harvard computer in 1947.", "Computer History Museum"),
            FunFact("technology", "The word 'robot' comes from the Czech word 'robota', meaning 'forced labor'.", "Etymology Dictionary"),
            FunFact("technology", "The first webcam was created to monitor a coffee pot at Cambridge University.", "Cambridge University"),
            FunFact("technology", "Google processes over 8.5 billion searches per day.", "Google Statistics"),
            
            # History Facts
            FunFact("history", "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid of Giza.", "Historical Timeline"),
            FunFact("history", "The Great Wall of China isn't visible from space with the naked eye.", "NASA"),
            FunFact("history", "Napoleon wasn't actually short - he was 5'7\", which was average height for his time.", "Historical Records"),
            
            # Nature Facts
            FunFact("nature", "A shrimp's heart is in its head.", "Marine Biology"),
            FunFact("nature", "Elephants are afraid of bees and will avoid areas where they hear buzzing.", "Animal Behavior Studies"),
            FunFact("nature", "A group of pandas is called an 'embarrassment'.", "Zoological Society"),
            
            # Space Facts
            FunFact("space", "One day on Venus is longer than one year on Venus.", "NASA"),
            FunFact("space", "There are more possible games of chess than atoms in the observable universe.", "Mathematics"),
            FunFact("space", "If you could drive a car to the sun at 60 mph, it would take you 106 years.", "Astronomy"),
        ]
    
    def _load_trivia(self) -> List[TriviaQuestion]:
        """Load trivia questions database."""
        return [
            # Easy Questions
            TriviaQuestion("geography", "What is the capital of France?", "Paris", "easy"),
            TriviaQuestion("science", "What gas do plants absorb from the atmosphere?", "Carbon dioxide", "easy"),
            TriviaQuestion("history", "In which year did World War II end?", "1945", "easy"),
            TriviaQuestion("sports", "How many players are on a basketball team on the court at one time?", "5", "easy"),
            
            # Medium Questions
            TriviaQuestion("science", "What is the chemical symbol for gold?", "Au", "medium"),
            TriviaQuestion("geography", "Which is the longest river in the world?", "The Nile River", "medium"),
            TriviaQuestion("literature", "Who wrote 'Pride and Prejudice'?", "Jane Austen", "medium"),
            TriviaQuestion("technology", "What does 'HTTP' stand for?", "HyperText Transfer Protocol", "medium"),
            
            # Hard Questions
            TriviaQuestion("science", "What is the smallest unit of matter?", "Atom", "hard"),
            TriviaQuestion("history", "Which ancient wonder of the world was located in Alexandria?", "The Lighthouse of Alexandria", "hard"),
            TriviaQuestion("geography", "What is the deepest point in Earth's oceans?", "Mariana Trench", "hard"),
            TriviaQuestion("literature", "In which Shakespeare play does the character Iago appear?", "Othello", "hard"),
        ]
    
    def _load_movies(self) -> List[MovieRecommendation]:
        """Load movie recommendations database."""
        return [
            # Action Movies
            MovieRecommendation("The Matrix", "Action/Sci-Fi", 1999, "R", 
                              "A computer hacker learns about the true nature of reality.", 
                              "The Wachowskis", ["Keanu Reeves", "Laurence Fishburne"]),
            MovieRecommendation("Mad Max: Fury Road", "Action", 2015, "R", 
                              "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler.", 
                              "George Miller", ["Tom Hardy", "Charlize Theron"]),
            MovieRecommendation("John Wick", "Action", 2014, "R", 
                              "An ex-hitman comes out of retirement to track down the gangsters who killed his dog.", 
                              "Chad Stahelski", ["Keanu Reeves", "Michael Nyqvist"]),
            
            # Comedy Movies
            MovieRecommendation("The Grand Budapest Hotel", "Comedy", 2014, "R", 
                              "The adventures of a legendary concierge and his protégé at a famous European hotel.", 
                              "Wes Anderson", ["Ralph Fiennes", "F. Murray Abraham"]),
            MovieRecommendation("Knives Out", "Comedy/Mystery", 2019, "PG-13", 
                              "A detective investigates the death of a patriarch of an eccentric family.", 
                              "Rian Johnson", ["Daniel Craig", "Chris Evans"]),
            MovieRecommendation("The Princess Bride", "Comedy/Adventure", 1987, "PG", 
                              "A classic fairy tale adventure with romance, sword fights, and humor.", 
                              "Rob Reiner", ["Cary Elwes", "Robin Wright"]),
            
            # Drama Movies
            MovieRecommendation("The Shawshank Redemption", "Drama", 1994, "R", 
                              "Two imprisoned men bond over years, finding solace and redemption.", 
                              "Frank Darabont", ["Tim Robbins", "Morgan Freeman"]),
            MovieRecommendation("Parasite", "Drama/Thriller", 2019, "R", 
                              "A poor family schemes to become employed by a wealthy family.", 
                              "Bong Joon-ho", ["Song Kang-ho", "Lee Sun-kyun"]),
            MovieRecommendation("Moonlight", "Drama", 2016, "R", 
                              "A young African-American man grapples with his identity and sexuality.", 
                              "Barry Jenkins", ["Mahershala Ali", "Naomie Harris"]),
            
            # Sci-Fi Movies
            MovieRecommendation("Blade Runner 2049", "Sci-Fi", 2017, "R", 
                              "A young blade runner discovers a secret that could plunge society into chaos.", 
                              "Denis Villeneuve", ["Ryan Gosling", "Harrison Ford"]),
            MovieRecommendation("Arrival", "Sci-Fi/Drama", 2016, "PG-13", 
                              "A linguist works with the military to communicate with alien visitors.", 
                              "Denis Villeneuve", ["Amy Adams", "Jeremy Renner"]),
            MovieRecommendation("Ex Machina", "Sci-Fi/Thriller", 2014, "R", 
                              "A programmer is invited to administer a Turing test to an intelligent humanoid robot.", 
                              "Alex Garland", ["Domhnall Gleeson", "Alicia Vikander"]),
            
            # Family Movies
            MovieRecommendation("Spider-Man: Into the Spider-Verse", "Animation/Action", 2018, "PG", 
                              "Teen Miles Morales becomes Spider-Man and meets other Spider-People.", 
                              "Bob Persichetti", ["Shameik Moore", "Jake Johnson"]),
            MovieRecommendation("Coco", "Animation/Family", 2017, "PG", 
                              "A young boy travels to the Land of the Dead to uncover his family's history.", 
                              "Lee Unkrich", ["Anthony Gonzalez", "Gael García Bernal"]),
            MovieRecommendation("The Incredibles", "Animation/Family", 2004, "PG", 
                              "A family of superheroes is forced to hide their powers and live normal lives.", 
                              "Brad Bird", ["Craig T. Nelson", "Holly Hunter"]),
        ]
    
    def _load_music(self) -> List[MusicRecommendation]:
        """Load music recommendations database."""
        return [
            # Pop Music
            MusicRecommendation("Blinding Lights", "The Weeknd", "Pop", 
                              "An upbeat synthwave-inspired pop song with 80s influences.", "After Hours", 2019),
            MusicRecommendation("Watermelon Sugar", "Harry Styles", "Pop", 
                              "A feel-good summer anthem with tropical vibes.", "Fine Line", 2019),
            MusicRecommendation("Levitating", "Dua Lipa", "Pop", 
                              "A disco-influenced dance-pop track with infectious energy.", "Future Nostalgia", 2020),
            
            # Rock Music
            MusicRecommendation("Bohemian Rhapsody", "Queen", "Rock", 
                              "An epic rock opera that defies conventional song structure.", "A Night at the Opera", 1975),
            MusicRecommendation("Hotel California", "Eagles", "Rock", 
                              "A classic rock song with mysterious lyrics and iconic guitar solos.", "Hotel California", 1976),
            MusicRecommendation("Sweet Child O' Mine", "Guns N' Roses", "Rock", 
                              "A hard rock anthem with one of the most recognizable guitar riffs.", "Appetite for Destruction", 1987),
            
            # Hip-Hop Music
            MusicRecommendation("HUMBLE.", "Kendrick Lamar", "Hip-Hop", 
                              "A powerful rap track with minimalist production and sharp lyrics.", "DAMN.", 2017),
            MusicRecommendation("Sicko Mode", "Travis Scott", "Hip-Hop", 
                              "A multi-part hip-hop epic with multiple beat switches.", "Astroworld", 2018),
            MusicRecommendation("God's Plan", "Drake", "Hip-Hop", 
                              "An introspective rap song about success and giving back.", "Scorpion", 2018),
            
            # Electronic Music
            MusicRecommendation("Strobe", "Deadmau5", "Electronic", 
                              "A progressive house masterpiece with a 10-minute emotional journey.", "For Lack of a Better Name", 2009),
            MusicRecommendation("Midnight City", "M83", "Electronic", 
                              "A dreamy synthpop anthem with an iconic saxophone solo.", "Hurry Up, We're Dreaming", 2011),
            MusicRecommendation("One More Time", "Daft Punk", "Electronic", 
                              "A euphoric French house track that defined electronic dance music.", "Discovery", 2000),
            
            # Alternative Music
            MusicRecommendation("Radioactive", "Imagine Dragons", "Alternative", 
                              "An anthemic alternative rock song with electronic elements.", "Night Visions", 2012),
            MusicRecommendation("Somebody That I Used to Know", "Gotye", "Alternative", 
                              "A melancholic indie pop song about the end of a relationship.", "Making Mirrors", 2011),
            MusicRecommendation("Take Me to Church", "Hozier", "Alternative", 
                              "A soulful alternative rock song with powerful vocals and social commentary.", "Hozier", 2014),
        ]
    
    def _load_riddles(self) -> List[Riddle]:
        """Load riddles database."""
        return [
            # Easy Riddles
            Riddle("What has keys but no locks, space but no room, and you can enter but not go inside?", 
                   "A keyboard", "easy", "wordplay", "Think about computer equipment"),
            Riddle("What gets wet while drying?", 
                   "A towel", "easy", "wordplay", "Think about bathroom items"),
            Riddle("What has hands but cannot clap?", 
                   "A clock", "easy", "wordplay", "Think about time"),
            Riddle("What can travel around the world while staying in a corner?", 
                   "A stamp", "easy", "wordplay", "Think about mail"),
            
            # Medium Riddles
            Riddle("I am not alive, but I grow; I don't have lungs, but I need air; I don't have a mouth, but water kills me. What am I?", 
                   "Fire", "medium", "nature", "Think about elements"),
            Riddle("The more you take, the more you leave behind. What am I?", 
                   "Footsteps", "medium", "wordplay", "Think about walking"),
            Riddle("I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?", 
                   "A map", "medium", "geography", "Think about navigation"),
            Riddle("What comes once in a minute, twice in a moment, but never in a thousand years?", 
                   "The letter M", "medium", "wordplay", "Think about letters"),
            
            # Hard Riddles
            Riddle("I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?", 
                   "An echo", "hard", "nature", "Think about sound"),
            Riddle("The person who makes it, sells it. The person who buys it, never uses it. The person who uses it, never knows they're using it. What is it?", 
                   "A coffin", "hard", "logic", "Think about life and death"),
            Riddle("What can run but never walks, has a mouth but never talks, has a head but never weeps, has a bed but never sleeps?", 
                   "A river", "hard", "nature", "Think about water"),
            Riddle("I am taken from a mine and shut up in a wooden case, from which I am never released, and yet I am used by almost everyone. What am I?", 
                   "Pencil lead (graphite)", "hard", "logic", "Think about writing tools"),
        ]
    
    def _load_quotes(self) -> List[Quote]:
        """Load motivational quotes and daily tips."""
        return [
            # Motivational Quotes
            Quote("The only way to do great work is to love what you do.", "motivational", "Steve Jobs", "Apple Keynote"),
            Quote("Innovation distinguishes between a leader and a follower.", "motivational", "Steve Jobs", "Apple"),
            Quote("The future belongs to those who believe in the beauty of their dreams.", "motivational", "Eleanor Roosevelt"),
            Quote("It is during our darkest moments that we must focus to see the light.", "motivational", "Aristotle"),
            Quote("Success is not final, failure is not fatal: it is the courage to continue that counts.", "motivational", "Winston Churchill"),
            
            # Daily Tips
            Quote("Start your day with a glass of water to kickstart your metabolism.", "daily_tip", None, "Health Experts"),
            Quote("Take a 5-minute break every hour to rest your eyes when working on a computer.", "daily_tip", None, "Ergonomics Guide"),
            Quote("Practice the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds.", "daily_tip", None, "Eye Care"),
            Quote("Keep a notebook by your bed to jot down ideas that come to you before sleep.", "daily_tip", None, "Productivity"),
            Quote("Spend 10 minutes each morning planning your day to increase productivity.", "daily_tip", None, "Time Management"),
            
            # Wisdom Quotes
            Quote("The only true wisdom is in knowing you know nothing.", "wisdom", "Socrates"),
            Quote("In the middle of difficulty lies opportunity.", "wisdom", "Albert Einstein"),
            Quote("The journey of a thousand miles begins with one step.", "wisdom", "Lao Tzu"),
            Quote("Yesterday is history, tomorrow is a mystery, today is a gift.", "wisdom", "Eleanor Roosevelt"),
            Quote("Be yourself; everyone else is already taken.", "wisdom", "Oscar Wilde"),
            
            # Success Quotes
            Quote("Success is walking from failure to failure with no loss of enthusiasm.", "success", "Winston Churchill"),
            Quote("The way to get started is to quit talking and begin doing.", "success", "Walt Disney"),
            Quote("Don't be afraid to give up the good to go for the great.", "success", "John D. Rockefeller"),
            Quote("The only impossible journey is the one you never begin.", "success", "Tony Robbins"),
            Quote("Success is not how high you have climbed, but how you make a positive difference to the world.", "success", "Roy T. Bennett"),
        ]
    
    def get_random_joke(self, category: Optional[str] = None) -> Joke:
        """Get a random joke, optionally filtered by category."""
        if category:
            filtered_jokes = [j for j in self.jokes if j.category.lower() == category.lower()]
            if filtered_jokes:
                return random.choice(filtered_jokes)
        return random.choice(self.jokes)
    
    def get_random_fun_fact(self, category: Optional[str] = None) -> FunFact:
        """Get a random fun fact, optionally filtered by category."""
        if category:
            filtered_facts = [f for f in self.fun_facts if f.category.lower() == category.lower()]
            if filtered_facts:
                return random.choice(filtered_facts)
        return random.choice(self.fun_facts)
    
    def get_trivia_question(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> TriviaQuestion:
        """Get a trivia question, optionally filtered by category and difficulty."""
        filtered_questions = self.trivia_questions
        
        if category:
            filtered_questions = [q for q in filtered_questions if q.category.lower() == category.lower()]
        
        if difficulty:
            filtered_questions = [q for q in filtered_questions if q.difficulty.lower() == difficulty.lower()]
        
        if not filtered_questions:
            filtered_questions = self.trivia_questions
            
        return random.choice(filtered_questions)
    
    def get_joke_categories(self) -> List[str]:
        """Get list of available joke categories."""
        return list(set(joke.category for joke in self.jokes))
    
    def get_fact_categories(self) -> List[str]:
        """Get list of available fun fact categories."""
        return list(set(fact.category for fact in self.fun_facts))
    
    def get_trivia_categories(self) -> List[str]:
        """Get list of available trivia categories."""
        return list(set(question.category for question in self.trivia_questions))
    
    def get_movie_recommendation(self, genre: Optional[str] = None) -> MovieRecommendation:
        """Get a movie recommendation, optionally filtered by genre."""
        if genre:
            filtered_movies = [m for m in self.movie_recommendations if genre.lower() in m.genre.lower()]
            if filtered_movies:
                return random.choice(filtered_movies)
        return random.choice(self.movie_recommendations)
    
    def get_music_recommendation(self, genre: Optional[str] = None) -> MusicRecommendation:
        """Get a music recommendation, optionally filtered by genre."""
        if genre:
            filtered_music = [m for m in self.music_recommendations if m.genre.lower() == genre.lower()]
            if filtered_music:
                return random.choice(filtered_music)
        return random.choice(self.music_recommendations)
    
    def get_riddle(self, difficulty: Optional[str] = None, category: Optional[str] = None) -> Riddle:
        """Get a riddle, optionally filtered by difficulty and category."""
        filtered_riddles = self.riddles
        
        if difficulty:
            filtered_riddles = [r for r in filtered_riddles if r.difficulty.lower() == difficulty.lower()]
        
        if category:
            filtered_riddles = [r for r in filtered_riddles if r.category.lower() == category.lower()]
        
        if not filtered_riddles:
            filtered_riddles = self.riddles
            
        return random.choice(filtered_riddles)
    
    def get_quote(self, category: Optional[str] = None) -> Quote:
        """Get a quote, optionally filtered by category."""
        if category:
            filtered_quotes = [q for q in self.quotes if q.category.lower() == category.lower()]
            if filtered_quotes:
                return random.choice(filtered_quotes)
        return random.choice(self.quotes)
    
    def get_movie_genres(self) -> List[str]:
        """Get list of available movie genres."""
        genres = set()
        for movie in self.movie_recommendations:
            # Split genres like "Action/Sci-Fi" into separate genres
            movie_genres = [g.strip() for g in movie.genre.split('/')]
            genres.update(movie_genres)
        return list(genres)
    
    def get_music_genres(self) -> List[str]:
        """Get list of available music genres."""
        return list(set(music.genre for music in self.music_recommendations))
    
    def get_riddle_categories(self) -> List[str]:
        """Get list of available riddle categories."""
        return list(set(riddle.category for riddle in self.riddles))
    
    def get_quote_categories(self) -> List[str]:
        """Get list of available quote categories."""
        return list(set(quote.category for quote in self.quotes))


class RecommendationEngine:
    """Handles personalized recommendations based on user preferences."""
    
    def __init__(self, entertainment_db: EntertainmentDatabase):
        self.db = entertainment_db
        self.user_preferences = {}
        self.interaction_history = []
    
    def update_user_preference(self, category: str, item: str, rating: float):
        """Update user preferences based on ratings."""
        if category not in self.user_preferences:
            self.user_preferences[category] = {}
        self.user_preferences[category][item] = rating
    
    def get_personalized_movie_recommendation(self) -> MovieRecommendation:
        """Get a personalized movie recommendation."""
        # Simple recommendation based on preferred genres
        preferred_genres = self._get_preferred_genres('movies')
        
        if preferred_genres:
            # Try to recommend from preferred genres
            for genre in preferred_genres:
                try:
                    return self.db.get_movie_recommendation(genre)
                except:
                    continue
        
        # Fallback to random recommendation
        return self.db.get_movie_recommendation()
    
    def get_personalized_music_recommendation(self) -> MusicRecommendation:
        """Get a personalized music recommendation."""
        # Simple recommendation based on preferred genres
        preferred_genres = self._get_preferred_genres('music')
        
        if preferred_genres:
            # Try to recommend from preferred genres
            for genre in preferred_genres:
                try:
                    return self.db.get_music_recommendation(genre)
                except:
                    continue
        
        # Fallback to random recommendation
        return self.db.get_music_recommendation()
    
    def _get_preferred_genres(self, category: str) -> List[str]:
        """Get user's preferred genres for a category."""
        if category not in self.user_preferences:
            return []
        
        # Sort by rating and return top genres
        preferences = self.user_preferences[category]
        sorted_prefs = sorted(preferences.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_prefs[:3]]  # Top 3 preferences
    
    def record_interaction(self, interaction_type: str, content: str, user_feedback: Optional[str] = None):
        """Record user interaction for future recommendations."""
        self.interaction_history.append({
            'type': interaction_type,
            'content': content,
            'feedback': user_feedback,
            'timestamp': datetime.now()
        })
        
        # Keep only recent interactions (last 100)
        if len(self.interaction_history) > 100:
            self.interaction_history = self.interaction_history[-100:]


class InteractiveGames:
    """Handles interactive games like coin flip, dice roll, number generation."""
    
    def __init__(self):
        self.random = random.Random()
        self.random.seed(datetime.now().timestamp())
    
    def flip_coin(self) -> Dict[str, Any]:
        """Flip a coin and return result."""
        result = self.random.choice(["heads", "tails"])
        return {
            "action": "coin_flip",
            "result": result,
            "message": f"The coin landed on {result}!"
        }
    
    def roll_dice(self, num_dice: int = 1, sides: int = 6) -> Dict[str, Any]:
        """Roll dice and return results."""
        if num_dice < 1 or num_dice > 10:
            num_dice = 1
        if sides < 2 or sides > 100:
            sides = 6
            
        rolls = [self.random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls)
        
        if num_dice == 1:
            message = f"You rolled a {rolls[0]} on a {sides}-sided die!"
        else:
            message = f"You rolled {rolls} on {num_dice} {sides}-sided dice. Total: {total}"
        
        return {
            "action": "dice_roll",
            "rolls": rolls,
            "total": total,
            "num_dice": num_dice,
            "sides": sides,
            "message": message
        }
    
    def generate_number(self, min_num: int = 1, max_num: int = 100) -> Dict[str, Any]:
        """Generate a random number within range."""
        if min_num > max_num:
            min_num, max_num = max_num, min_num
        
        number = self.random.randint(min_num, max_num)
        
        return {
            "action": "number_generation",
            "number": number,
            "range": f"{min_num}-{max_num}",
            "message": f"I generated the number {number} between {min_num} and {max_num}!"
        }
    
    def magic_8_ball(self) -> Dict[str, Any]:
        """Magic 8-ball responses."""
        responses = [
            "It is certain",
            "Reply hazy, try again",
            "Don't count on it",
            "It is decidedly so",
            "Ask again later",
            "My reply is no",
            "Without a doubt",
            "Better not tell you now",
            "My sources say no",
            "Yes definitely",
            "Cannot predict now",
            "Outlook not so good",
            "You may rely on it",
            "Concentrate and ask again",
            "Very doubtful",
            "As I see it, yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes"
        ]
        
        response = self.random.choice(responses)
        
        return {
            "action": "magic_8_ball",
            "response": response,
            "message": f"The Magic 8-Ball says: {response}"
        }
    
    def rock_paper_scissors(self, user_choice: str) -> Dict[str, Any]:
        """Play rock, paper, scissors."""
        choices = ["rock", "paper", "scissors"]
        user_choice = user_choice.lower().strip()
        
        if user_choice not in choices:
            return {
                "action": "rock_paper_scissors",
                "error": "Invalid choice. Please choose rock, paper, or scissors.",
                "message": "Please choose rock, paper, or scissors!"
            }
        
        computer_choice = self.random.choice(choices)
        
        # Determine winner
        if user_choice == computer_choice:
            result = "tie"
            message = f"We both chose {user_choice}. It's a tie!"
        elif (user_choice == "rock" and computer_choice == "scissors") or \
             (user_choice == "paper" and computer_choice == "rock") or \
             (user_choice == "scissors" and computer_choice == "paper"):
            result = "win"
            message = f"You chose {user_choice}, I chose {computer_choice}. You win!"
        else:
            result = "lose"
            message = f"You chose {user_choice}, I chose {computer_choice}. I win!"
        
        return {
            "action": "rock_paper_scissors",
            "user_choice": user_choice,
            "computer_choice": computer_choice,
            "result": result,
            "message": message
        }


# Global instances
entertainment_db = EntertainmentDatabase()
interactive_games = InteractiveGames()
recommendation_engine = RecommendationEngine(entertainment_db)