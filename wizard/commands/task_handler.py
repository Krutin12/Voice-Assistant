"""
Task Handler Module
Handles random tasks like calculations, jokes, time, date, timers, reminders
"""

import datetime
import random
import threading
import math
import re

# Jokes database
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? He was outstanding in his field!",
    "Why don't eggs tell jokes? They'd crack each other up!",
    "What do you call a fake noodle? An impasta!",
    "Why did the math book look so sad? Because it had too many problems!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why don't programmers like nature? It has too many bugs!",
    "How do you comfort a JavaScript bug? You console it!",
    "Why do Java developers wear glasses? Because they can't C#!",
    "Why did the Python programmer not respond? They were stuck in an infinite loop!",
    "What's a programmer's favorite hangout place? Foo Bar!",
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
    "What's the object-oriented way to become wealthy? Inheritance!",
    "Why did the programmer quit their job? They didn't get arrays!",
    "What's a programmer's favorite snack? Cookies!",
    "Why do programmers hate nature? It has too many bugs!",
    "What do you call a programmer from Finland? Nerdic!",
    "Why did the programmer go broke? Because they used up all their cache!",
    "What's a programmer's favorite drink? Java!",
    "Why don't programmers like to go outside? The sun gives them compiler errors!",
    "What do you call a programmer who doesn't comment code? A developer!",
    "Why did the programmer get stuck in the shower? The instructions said 'lather, rinse, repeat'!",
    "What's a programmer's favorite place to hang out? The Foo Bar!",
    "Why do programmers always mix up Halloween and Christmas? Because Oct 31 == Dec 25!",
]

# Basic knowledge base
KNOWLEDGE_BASE = {
    'python': 'Python is a high-level programming language known for its simplicity and readability.',
    'javascript': 'JavaScript is a programming language used for web development.',
    'computer': 'A computer is an electronic device that processes data.',
    'internet': 'The internet is a global network of interconnected computers.',
    'ai': 'Artificial Intelligence is the simulation of human intelligence by machines.',
    'machine learning': 'Machine Learning is a subset of AI that enables computers to learn from data.',
    'voice assistant': 'A voice assistant is a software that responds to voice commands.',
}

def calculate(expression):
    """Calculate a mathematical expression safely"""
    try:
        # Remove common words
        expression = expression.lower()
        expression = re.sub(r'calculate|what is|compute|solve|math|equals|equal to', '', expression)
        expression = expression.strip()
        
        # Replace common math words
        expression = expression.replace('plus', '+')
        expression = expression.replace('minus', '-')
        expression = expression.replace('times', '*')
        expression = expression.replace('multiplied by', '*')
        expression = expression.replace('divided by', '/')
        expression = expression.replace('to the power of', '**')
        expression = expression.replace('squared', '**2')
        expression = expression.replace('cubed', '**3')
        
        # Safety check - only allow safe characters
        safe_chars = set('0123456789+-*/.() **sqrt')
        if not all(c in safe_chars or c.isspace() for c in expression):
            return "I can only calculate basic math operations"
        
        # Check for dangerous operations
        if '__' in expression or 'import' in expression or 'exec' in expression:
            return "I can't perform that calculation for security reasons"
        
        # Handle sqrt
        if 'sqrt' in expression:
            import re
            matches = re.findall(r'sqrt\((\d+)\)', expression)
            for match in matches:
                result = math.sqrt(float(match))
                expression = expression.replace(f'sqrt({match})', str(result))
        
        # Evaluate safely
        result = eval(expression)
        return f"The answer is {result}"
    except Exception as e:
        return f"I couldn't calculate that: {str(e)}"

def tell_joke():
    """Tell a random joke"""
    return random.choice(JOKES)

def get_time():
    """Get current time"""
    now = datetime.datetime.now()
    return now.strftime("It's %I:%M %p")

def get_date():
    """Get current date"""
    now = datetime.datetime.now()
    return now.strftime("Today is %B %d, %Y")

def set_timer(minutes):
    """Set a countdown timer"""
    try:
        minutes = int(minutes)
        if minutes <= 0:
            return "Timer must be at least 1 minute"
        
        seconds = minutes * 60
        
        def timer_callback():
            # This would need TTS to speak, but for now just return
            print(f"Timer for {minutes} minutes is complete!")
        
        timer = threading.Timer(seconds, timer_callback)
        timer.start()
        return f"Timer set for {minutes} minutes"
    except Exception as e:
        return f"Error setting timer: {str(e)}"

def answer_question(question):
    """Answer a question from knowledge base"""
    question_lower = question.lower()
    
    # Check knowledge base
    for key, answer in KNOWLEDGE_BASE.items():
        if key in question_lower:
            return answer
    
    # Default response
    return "I don't know that yet. I'm still learning!"

