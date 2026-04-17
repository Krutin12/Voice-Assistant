"""
Enhanced Knowledge Data for Wizard Voice Assistant

This module provides comprehensive data to populate the offline knowledge system
with extensive Wikipedia articles, dictionary entries, and currency information.
"""

from typing import Dict, List, Tuple
from .offline_knowledge import OfflineKnowledge


def populate_comprehensive_wikipedia_data(knowledge_system: OfflineKnowledge) -> None:
    """
    Populate the knowledge system with comprehensive Wikipedia articles.
    
    Args:
        knowledge_system: OfflineKnowledge instance to populate
    """
    
    # Comprehensive Wikipedia articles covering various topics
    wikipedia_articles = [
        # Technology and Computing
        {
            'title': 'Artificial Intelligence',
            'summary': 'Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving".',
            'url': 'https://en.wikipedia.org/wiki/Artificial_intelligence'
        },
        {
            'title': 'Machine Learning',
            'summary': 'Machine learning (ML) is a type of artificial intelligence (AI) that allows software applications to become more accurate at predicting outcomes without being explicitly programmed to do so. Machine learning algorithms use historical data as input to predict new output values. Machine learning is closely related to computational statistics, which focuses on making predictions using computers.',
            'url': 'https://en.wikipedia.org/wiki/Machine_learning'
        },
        {
            'title': 'Deep Learning',
            'summary': 'Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised. Deep learning architectures such as deep neural networks, deep belief networks, recurrent neural networks and convolutional neural networks have been applied to fields including computer vision, speech recognition, natural language processing, machine translation, bioinformatics and drug design.',
            'url': 'https://en.wikipedia.org/wiki/Deep_learning'
        },
        {
            'title': 'Neural Network',
            'summary': 'A neural network is a network or circuit of neurons, or in a modern sense, an artificial neural network, composed of artificial neurons or nodes. Thus a neural network is either a biological neural network, made up of real biological neurons, or an artificial neural network, for solving artificial intelligence (AI) problems. The connections of the biological neuron are modeled as weights.',
            'url': 'https://en.wikipedia.org/wiki/Neural_network'
        },
        {
            'title': 'Computer Science',
            'summary': 'Computer science is the study of algorithmic processes, computational systems and the design of computer systems and their applications. It includes the study of algorithms and data structures, computer and network design, modeling data and information processes, and artificial intelligence. Computer science draws some of its foundations from mathematics and engineering and therefore incorporates techniques from areas such as queueing theory, probability and statistics, and electronic circuit design.',
            'url': 'https://en.wikipedia.org/wiki/Computer_science'
        },
        {
            'title': 'Programming Language',
            'summary': 'A programming language is a formal language comprising a set of instructions that produce various kinds of output. Programming languages are used in computer programming to implement algorithms. Most programming languages consist of instructions for computers. There are programmable machines that use a set of specific instructions, rather than general programming languages.',
            'url': 'https://en.wikipedia.org/wiki/Programming_language'
        },
        {
            'title': 'Software Engineering',
            'summary': 'Software engineering is the systematic application of engineering approaches to the development of software. Software engineering is a computing discipline. A software engineer is a person who applies the principles of software engineering to design, develop, maintain, test, and evaluate computer software.',
            'url': 'https://en.wikipedia.org/wiki/Software_engineering'
        },
        {
            'title': 'Data Science',
            'summary': 'Data science is an inter-disciplinary field that uses scientific methods, processes, algorithms and systems to extract knowledge and insights from many structural and unstructured data. Data science is related to data mining, machine learning and big data. Data science is a "concept to unify statistics, data analysis, informatics, and their related methods" in order to "understand and analyze actual phenomena" with data.',
            'url': 'https://en.wikipedia.org/wiki/Data_science'
        },
        
        # Science and Mathematics
        {
            'title': 'Physics',
            'summary': 'Physics is the natural science that studies matter, its motion and behavior through space and time, and the related entities of energy and force. Physics is one of the most fundamental scientific disciplines, and its main goal is to understand how the universe behaves. Physics is one of the oldest academic disciplines and, through its inclusion of astronomy, perhaps the oldest.',
            'url': 'https://en.wikipedia.org/wiki/Physics'
        },
        {
            'title': 'Mathematics',
            'summary': 'Mathematics includes the study of such topics as quantity (number theory), structure (algebra), space (geometry), and change (mathematical analysis). It has no generally accepted definition. Mathematicians seek and use patterns to formulate new conjectures; they resolve the truth or falsity of such by mathematical proof.',
            'url': 'https://en.wikipedia.org/wiki/Mathematics'
        },
        {
            'title': 'Chemistry',
            'summary': 'Chemistry is the scientific discipline involved with elements and compounds composed of atoms, molecules and ions: their composition, structure, properties, behavior and the changes they undergo during a reaction with other substances. In the scope of its subject, chemistry occupies an intermediate position between physics and biology.',
            'url': 'https://en.wikipedia.org/wiki/Chemistry'
        },
        {
            'title': 'Biology',
            'summary': 'Biology is the natural science that studies life and living organisms, including their physical structure, chemical processes, molecular interactions, physiological mechanisms, development and evolution. Despite the complexity of the science, certain unifying concepts consolidate it into a single, coherent field.',
            'url': 'https://en.wikipedia.org/wiki/Biology'
        },
        
        # History and Geography
        {
            'title': 'World War II',
            'summary': 'World War II or the Second World War, often abbreviated as WWII or WW2, was a global war that lasted from 1939 to 1945. It involved the vast majority of the world\'s countries—including all of the great powers—forming two opposing military alliances: the Allies and the Axis powers. In a state of total war, directly involving more than 100 million personnel from more than 30 countries, the major participants threw their entire economic, industrial, and scientific capabilities behind the war effort.',
            'url': 'https://en.wikipedia.org/wiki/World_War_II'
        },
        {
            'title': 'United States',
            'summary': 'The United States of America (U.S.A. or USA), commonly known as the United States (U.S. or US) or America, is a country primarily located in North America. It consists of 50 states, a federal district, five major unincorporated territories, 326 Indian reservations, and some minor possessions. At 3.8 million square miles, it is the world\'s third- or fourth-largest country by total area.',
            'url': 'https://en.wikipedia.org/wiki/United_States'
        },
        {
            'title': 'Climate Change',
            'summary': 'Climate change includes both global warming driven by human emissions of greenhouse gases, and the resulting large-scale shifts in weather patterns. Though there have been previous periods of climatic change, since the mid-20th century humans have had an unprecedented impact on Earth\'s climate system and caused change on a global scale.',
            'url': 'https://en.wikipedia.org/wiki/Climate_change'
        },
        
        # Arts and Culture
        {
            'title': 'Music',
            'summary': 'Music is an art form and cultural activity whose medium is sound organized in time. General definitions of music include common elements such as pitch, rhythm, dynamics, and the sonic qualities of timbre and texture. Different styles or types of music may emphasize, de-emphasize or omit some of these elements.',
            'url': 'https://en.wikipedia.org/wiki/Music'
        },
        {
            'title': 'Literature',
            'summary': 'Literature is a method of recording, preserving, and transmitting knowledge and entertainment. It can also have a social, psychological, spiritual, or political role. Literature, as an art form, can also include works in various non-fiction genres, such as biography, diaries, memoir, letters, and essays.',
            'url': 'https://en.wikipedia.org/wiki/Literature'
        },
        {
            'title': 'Philosophy',
            'summary': 'Philosophy is the study of general and fundamental questions, such as those about existence, reason, knowledge, values, mind, and language. Such questions are often posed as problems to be studied or resolved. Some sources claim the term was coined by Pythagoras; others dispute this story.',
            'url': 'https://en.wikipedia.org/wiki/Philosophy'
        }
    ]
    
    # Populate Wikipedia articles
    for article in wikipedia_articles:
        knowledge_system.cache_wikipedia_article(
            title=article['title'],
            summary=article['summary'],
            url=article['url']
        )


def populate_comprehensive_dictionary_data(knowledge_system: OfflineKnowledge) -> None:
    """
    Populate the knowledge system with comprehensive dictionary entries.
    
    Args:
        knowledge_system: OfflineKnowledge instance to populate
    """
    
    # Comprehensive dictionary entries
    dictionary_entries = [
        # Technology Terms
        {
            'word': 'algorithm',
            'definition': 'A process or set of rules to be followed in calculations or other problem-solving operations, especially by a computer',
            'part_of_speech': 'noun',
            'example': 'The search algorithm quickly found the relevant results.',
            'synonyms': 'procedure, method, process, formula'
        },
        {
            'word': 'artificial',
            'definition': 'Made or produced by human beings rather than occurring naturally, especially as a copy of something natural',
            'part_of_speech': 'adjective',
            'example': 'Artificial intelligence is transforming technology.',
            'synonyms': 'synthetic, man-made, manufactured, simulated'
        },
        {
            'word': 'intelligence',
            'definition': 'The ability to acquire and apply knowledge and skills',
            'part_of_speech': 'noun',
            'example': 'Human intelligence is remarkably adaptable.',
            'synonyms': 'intellect, understanding, comprehension, wisdom'
        },
        {
            'word': 'machine',
            'definition': 'An apparatus using mechanical power and having several parts, each with a definite function and together performing a particular task',
            'part_of_speech': 'noun',
            'example': 'The machine processed thousands of data points per second.',
            'synonyms': 'device, apparatus, mechanism, equipment'
        },
        {
            'word': 'learning',
            'definition': 'The acquisition of knowledge or skills through experience, study, or by being taught',
            'part_of_speech': 'noun',
            'example': 'Machine learning enables computers to improve automatically.',
            'synonyms': 'education, training, instruction, study'
        },
        {
            'word': 'network',
            'definition': 'A group or system of interconnected people or things',
            'part_of_speech': 'noun',
            'example': 'The computer network allows all employees to share files.',
            'synonyms': 'system, web, grid, connection'
        },
        {
            'word': 'database',
            'definition': 'A structured set of data held in a computer, especially one that is accessible in various ways',
            'part_of_speech': 'noun',
            'example': 'The customer information is stored in a secure database.',
            'synonyms': 'databank, repository, archive, storage'
        },
        {
            'word': 'software',
            'definition': 'Computer programs and other operating information used by a computer',
            'part_of_speech': 'noun',
            'example': 'The new software update includes several bug fixes.',
            'synonyms': 'programs, applications, code, system'
        },
        {
            'word': 'hardware',
            'definition': 'The physical components of a computer system',
            'part_of_speech': 'noun',
            'example': 'The hardware requirements for this game are quite high.',
            'synonyms': 'equipment, components, machinery, devices'
        },
        {
            'word': 'programming',
            'definition': 'The process of creating a set of instructions that tell a computer how to perform a task',
            'part_of_speech': 'noun',
            'example': 'She learned programming to build her own website.',
            'synonyms': 'coding, development, scripting, software engineering'
        },
        
        # Science Terms
        {
            'word': 'experiment',
            'definition': 'A scientific procedure undertaken to make a discovery, test a hypothesis, or demonstrate a known fact',
            'part_of_speech': 'noun',
            'example': 'The experiment confirmed the theory of relativity.',
            'synonyms': 'test, trial, investigation, study'
        },
        {
            'word': 'hypothesis',
            'definition': 'A supposition or proposed explanation made on the basis of limited evidence as a starting point for further investigation',
            'part_of_speech': 'noun',
            'example': 'The scientist formed a hypothesis about the phenomenon.',
            'synonyms': 'theory, assumption, proposition, conjecture'
        },
        {
            'word': 'analysis',
            'definition': 'Detailed examination of the elements or structure of something',
            'part_of_speech': 'noun',
            'example': 'The data analysis revealed interesting patterns.',
            'synonyms': 'examination, study, investigation, evaluation'
        },
        {
            'word': 'research',
            'definition': 'The systematic investigation into and study of materials and sources in order to establish facts and reach new conclusions',
            'part_of_speech': 'noun',
            'example': 'The research project lasted three years.',
            'synonyms': 'investigation, study, inquiry, exploration'
        },
        
        # General Academic Terms
        {
            'word': 'knowledge',
            'definition': 'Facts, information, and skills acquired by a person through experience or education',
            'part_of_speech': 'noun',
            'example': 'Knowledge is power in the information age.',
            'synonyms': 'understanding, learning, wisdom, information'
        },
        {
            'word': 'education',
            'definition': 'The process of receiving or giving systematic instruction, especially at a school or university',
            'part_of_speech': 'noun',
            'example': 'Education is the foundation of personal development.',
            'synonyms': 'schooling, teaching, training, instruction'
        },
        {
            'word': 'information',
            'definition': 'Facts provided or learned about something or someone',
            'part_of_speech': 'noun',
            'example': 'The information was stored in the database.',
            'synonyms': 'data, facts, details, knowledge'
        },
        {
            'word': 'communication',
            'definition': 'The imparting or exchanging of information or ideas',
            'part_of_speech': 'noun',
            'example': 'Effective communication is essential for teamwork.',
            'synonyms': 'interaction, correspondence, dialogue, exchange'
        },
        
        # Common Words for Spell Checking
        {
            'word': 'necessary',
            'definition': 'Required to be done, achieved, or present; needed; essential',
            'part_of_speech': 'adjective',
            'example': 'It is necessary to backup your files regularly.',
            'synonyms': 'essential, required, needed, vital'
        },
        {
            'word': 'receive',
            'definition': 'Be given, presented with, or paid (something)',
            'part_of_speech': 'verb',
            'example': 'I will receive the package tomorrow.',
            'synonyms': 'get, obtain, acquire, accept'
        },
        {
            'word': 'separate',
            'definition': 'Forming or viewed as a unit apart or by itself',
            'part_of_speech': 'adjective',
            'example': 'Keep the files in separate folders.',
            'synonyms': 'distinct, individual, different, independent'
        },
        {
            'word': 'definitely',
            'definition': 'Without doubt (used for emphasis)',
            'part_of_speech': 'adverb',
            'example': 'I will definitely attend the meeting.',
            'synonyms': 'certainly, surely, absolutely, undoubtedly'
        },
        {
            'word': 'beginning',
            'definition': 'The point in time or space at which something starts',
            'part_of_speech': 'noun',
            'example': 'This is just the beginning of our journey.',
            'synonyms': 'start, commencement, opening, inception'
        }
    ]
    
    # Populate dictionary entries
    for entry in dictionary_entries:
        knowledge_system.add_definition(
            word=entry['word'],
            definition=entry['definition'],
            part_of_speech=entry['part_of_speech'],
            example=entry['example'],
            synonyms=entry.get('synonyms', '')
        )


def populate_comprehensive_currency_data(knowledge_system: OfflineKnowledge) -> None:
    """
    Populate the knowledge system with comprehensive currency exchange rates.
    
    Args:
        knowledge_system: OfflineKnowledge instance to populate
    """
    
    # Comprehensive exchange rates (as of reference date)
    exchange_rates = [
        # USD base rates
        ('USD', 'EUR', 0.85),    # US Dollar to Euro
        ('USD', 'GBP', 0.73),    # US Dollar to British Pound
        ('USD', 'JPY', 110.0),   # US Dollar to Japanese Yen
        ('USD', 'CAD', 1.25),    # US Dollar to Canadian Dollar
        ('USD', 'AUD', 1.35),    # US Dollar to Australian Dollar
        ('USD', 'CHF', 0.92),    # US Dollar to Swiss Franc
        ('USD', 'CNY', 6.45),    # US Dollar to Chinese Yuan
        ('USD', 'INR', 74.5),    # US Dollar to Indian Rupee
        ('USD', 'KRW', 1180.0),  # US Dollar to South Korean Won
        ('USD', 'MXN', 20.1),    # US Dollar to Mexican Peso
        ('USD', 'BRL', 5.2),     # US Dollar to Brazilian Real
        ('USD', 'RUB', 73.5),    # US Dollar to Russian Ruble
        ('USD', 'SEK', 8.6),     # US Dollar to Swedish Krona
        ('USD', 'NOK', 8.8),     # US Dollar to Norwegian Krone
        ('USD', 'DKK', 6.3),     # US Dollar to Danish Krone
        
        # EUR base rates
        ('EUR', 'USD', 1.18),    # Euro to US Dollar
        ('EUR', 'GBP', 0.86),    # Euro to British Pound
        ('EUR', 'JPY', 129.5),   # Euro to Japanese Yen
        ('EUR', 'CAD', 1.47),    # Euro to Canadian Dollar
        ('EUR', 'AUD', 1.59),    # Euro to Australian Dollar
        ('EUR', 'CHF', 1.08),    # Euro to Swiss Franc
        ('EUR', 'CNY', 7.6),     # Euro to Chinese Yuan
        ('EUR', 'INR', 87.8),    # Euro to Indian Rupee
        
        # GBP base rates
        ('GBP', 'USD', 1.37),    # British Pound to US Dollar
        ('GBP', 'EUR', 1.16),    # British Pound to Euro
        ('GBP', 'JPY', 150.7),   # British Pound to Japanese Yen
        ('GBP', 'CAD', 1.71),    # British Pound to Canadian Dollar
        ('GBP', 'AUD', 1.85),    # British Pound to Australian Dollar
        ('GBP', 'CHF', 1.26),    # British Pound to Swiss Franc
        
        # JPY base rates
        ('JPY', 'USD', 0.0091),  # Japanese Yen to US Dollar
        ('JPY', 'EUR', 0.0077),  # Japanese Yen to Euro
        ('JPY', 'GBP', 0.0066),  # Japanese Yen to British Pound
        ('JPY', 'CAD', 0.0114),  # Japanese Yen to Canadian Dollar
        ('JPY', 'AUD', 0.0123),  # Japanese Yen to Australian Dollar
        
        # CAD base rates
        ('CAD', 'USD', 0.80),    # Canadian Dollar to US Dollar
        ('CAD', 'EUR', 0.68),    # Canadian Dollar to Euro
        ('CAD', 'GBP', 0.58),    # Canadian Dollar to British Pound
        ('CAD', 'JPY', 88.0),    # Canadian Dollar to Japanese Yen
        ('CAD', 'AUD', 1.08),    # Canadian Dollar to Australian Dollar
        
        # AUD base rates
        ('AUD', 'USD', 0.74),    # Australian Dollar to US Dollar
        ('AUD', 'EUR', 0.63),    # Australian Dollar to Euro
        ('AUD', 'GBP', 0.54),    # Australian Dollar to British Pound
        ('AUD', 'JPY', 81.5),    # Australian Dollar to Japanese Yen
        ('AUD', 'CAD', 0.93),    # Australian Dollar to Canadian Dollar
        
        # Additional currencies
        ('CHF', 'USD', 1.09),    # Swiss Franc to US Dollar
        ('CHF', 'EUR', 0.92),    # Swiss Franc to Euro
        ('CNY', 'USD', 0.155),   # Chinese Yuan to US Dollar
        ('INR', 'USD', 0.0134),  # Indian Rupee to US Dollar
        ('KRW', 'USD', 0.00085), # South Korean Won to US Dollar
        ('MXN', 'USD', 0.0498),  # Mexican Peso to US Dollar
        ('BRL', 'USD', 0.192),   # Brazilian Real to US Dollar
        ('RUB', 'USD', 0.0136),  # Russian Ruble to US Dollar
        ('SEK', 'USD', 0.116),   # Swedish Krona to US Dollar
        ('NOK', 'USD', 0.114),   # Norwegian Krone to US Dollar
        ('DKK', 'USD', 0.159),   # Danish Krone to US Dollar
    ]
    
    # Update exchange rates
    for base, target, rate in exchange_rates:
        knowledge_system.update_exchange_rate(base, target, rate)


def get_comprehensive_wikipedia_topics() -> List[str]:
    """
    Get list of comprehensive Wikipedia topics available.
    
    Returns:
        List of topic names
    """
    return [
        'Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Neural Network',
        'Computer Science', 'Programming Language', 'Software Engineering', 'Data Science',
        'Physics', 'Mathematics', 'Chemistry', 'Biology',
        'World War II', 'United States', 'Climate Change',
        'Music', 'Literature', 'Philosophy'
    ]


def get_comprehensive_dictionary_words() -> List[str]:
    """
    Get list of comprehensive dictionary words available.
    
    Returns:
        List of words
    """
    return [
        'algorithm', 'artificial', 'intelligence', 'machine', 'learning', 'network',
        'database', 'software', 'hardware', 'programming', 'experiment', 'hypothesis',
        'analysis', 'research', 'knowledge', 'education', 'information', 'communication',
        'necessary', 'receive', 'separate', 'definitely', 'beginning'
    ]


def get_comprehensive_currencies() -> List[str]:
    """
    Get list of comprehensive currencies available for conversion.
    
    Returns:
        List of currency codes
    """
    return [
        'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR',
        'KRW', 'MXN', 'BRL', 'RUB', 'SEK', 'NOK', 'DKK'
    ]