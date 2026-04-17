"""
Sample Knowledge Data for Wizard Voice Assistant

This module provides sample data to populate the offline knowledge system
with basic Wikipedia articles, dictionary entries, and other reference information.
"""

from typing import Dict, List
from .offline_knowledge import OfflineKnowledge


def populate_sample_data(knowledge_system: OfflineKnowledge) -> None:
    """
    Populate the knowledge system with sample data.
    
    Args:
        knowledge_system: OfflineKnowledge instance to populate
    """
    
    # Sample Wikipedia articles
    wikipedia_articles = [
        {
            'title': 'Artificial Intelligence',
            'summary': 'Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.',
            'url': 'https://en.wikipedia.org/wiki/Artificial_intelligence'
        },
        {
            'title': 'Machine Learning',
            'summary': 'Machine learning (ML) is a type of artificial intelligence (AI) that allows software applications to become more accurate at predicting outcomes without being explicitly programmed to do so. Machine learning algorithms use historical data as input to predict new output values.',
            'url': 'https://en.wikipedia.org/wiki/Machine_learning'
        },
        {
            'title': 'Computer',
            'summary': 'A computer is a machine that can be programmed to carry out sequences of arithmetic or logical operations automatically. Modern computers can perform generic sets of operations known as programs. These programs enable computers to perform a wide range of tasks.',
            'url': 'https://en.wikipedia.org/wiki/Computer'
        },
        {
            'title': 'Python Programming Language',
            'summary': 'Python is an interpreted, high-level and general-purpose programming language. Python\'s design philosophy emphasizes code readability with its notable use of significant whitespace. Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects.',
            'url': 'https://en.wikipedia.org/wiki/Python_(programming_language)'
        },
        {
            'title': 'Voice Assistant',
            'summary': 'A voice assistant is a digital assistant that uses voice recognition, speech synthesis, and natural language processing to provide aid to users through phones and voice-enabled devices. Voice assistants can perform various tasks such as answering questions, playing music, controlling smart home devices, and more.',
            'url': 'https://en.wikipedia.org/wiki/Virtual_assistant'
        }
    ]
    
    # Sample dictionary entries
    dictionary_entries = [
        {
            'word': 'algorithm',
            'definition': 'A process or set of rules to be followed in calculations or other problem-solving operations, especially by a computer',
            'part_of_speech': 'noun',
            'example': 'The search algorithm quickly found the relevant results.'
        },
        {
            'word': 'database',
            'definition': 'A structured set of data held in a computer, especially one that is accessible in various ways',
            'part_of_speech': 'noun',
            'example': 'The customer information is stored in a secure database.'
        },
        {
            'word': 'network',
            'definition': 'A group or system of interconnected people or things',
            'part_of_speech': 'noun',
            'example': 'The computer network allows all employees to share files.'
        },
        {
            'word': 'software',
            'definition': 'Computer programs and other operating information used by a computer',
            'part_of_speech': 'noun',
            'example': 'The new software update includes several bug fixes.'
        },
        {
            'word': 'hardware',
            'definition': 'The physical components of a computer system',
            'part_of_speech': 'noun',
            'example': 'The hardware requirements for this game are quite high.'
        },
        {
            'word': 'internet',
            'definition': 'A global computer network providing a variety of information and communication facilities',
            'part_of_speech': 'noun',
            'example': 'I found the information on the internet.'
        },
        {
            'word': 'programming',
            'definition': 'The process of creating a set of instructions that tell a computer how to perform a task',
            'part_of_speech': 'noun',
            'example': 'She learned programming to build her own website.'
        },
        {
            'word': 'technology',
            'definition': 'The application of scientific knowledge for practical purposes, especially in industry',
            'part_of_speech': 'noun',
            'example': 'Modern technology has revolutionized communication.'
        }
    ]
    
    # Populate Wikipedia articles
    for article in wikipedia_articles:
        knowledge_system.cache_wikipedia_article(
            title=article['title'],
            summary=article['summary'],
            url=article['url']
        )
    
    # Populate dictionary entries
    for entry in dictionary_entries:
        knowledge_system.add_definition(
            word=entry['word'],
            definition=entry['definition'],
            part_of_speech=entry['part_of_speech'],
            example=entry['example']
        )
    
    # Update some exchange rates
    exchange_rates = [
        ('USD', 'EUR', 0.85),
        ('USD', 'GBP', 0.73),
        ('USD', 'JPY', 110.0),
        ('USD', 'CAD', 1.25),
        ('USD', 'AUD', 1.35),
        ('EUR', 'USD', 1.18),
        ('EUR', 'GBP', 0.86),
        ('GBP', 'USD', 1.37),
        ('GBP', 'EUR', 1.16)
    ]
    
    for base, target, rate in exchange_rates:
        knowledge_system.update_exchange_rate(base, target, rate)


def get_sample_wikipedia_topics() -> List[str]:
    """
    Get list of sample Wikipedia topics available.
    
    Returns:
        List of topic names
    """
    return [
        'Artificial Intelligence',
        'Machine Learning',
        'Computer',
        'Python Programming Language',
        'Voice Assistant'
    ]


def get_sample_dictionary_words() -> List[str]:
    """
    Get list of sample dictionary words available.
    
    Returns:
        List of words
    """
    return [
        'algorithm',
        'database',
        'network',
        'software',
        'hardware',
        'internet',
        'programming',
        'technology'
    ]


def get_sample_currencies() -> List[str]:
    """
    Get list of sample currencies available for conversion.
    
    Returns:
        List of currency codes
    """
    return ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']