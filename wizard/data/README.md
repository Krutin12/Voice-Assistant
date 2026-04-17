# AI Brain Module

## Overview

The AI Brain module provides intelligent response generation, local knowledge base management, and conversation context tracking for the Wizard Voice Assistant.

## Features

### 1. SQLite Database Storage
- **Facts Table**: Stores knowledge facts with categories, questions, answers, and confidence scores
- **Conversations Table**: Tracks conversation history with session management
- **User Preferences Table**: Stores user-specific settings and preferences
- **Response Patterns Table**: Manages pattern-based response templates

### 2. Pattern-Based Response Generation
- Regex-based intent matching for common queries
- Multiple response variations for natural conversation
- Template-based responses with dynamic variable substitution
- Support for greetings, farewells, time/date queries, and more

### 3. Conversation Context Management
- Session-based conversation tracking
- Follow-up question handling
- Context variable storage and retrieval
- Conversation history analysis

### 4. Local Knowledge Base
- Pre-populated with facts across multiple categories:
  - Definitions (AI, ML, programming concepts)
  - Science (physics, chemistry, biology)
  - Mathematics (constants, formulas)
  - History (important events, dates)
  - Geography (countries, landmarks)
  - Technology (internet, devices)
  - General knowledge (time, dates, measurements)

### 5. Advanced Features
- Similar question detection
- Learning from user corrections
- Conversation export (JSON/text formats)
- Knowledge base statistics and analytics
- Session summaries and insights

## Usage

### Basic Usage

```python
from wizard.data.ai_brain import AIBrain

# Initialize the AI brain
brain = AIBrain()

# Start a new session
session_id = brain.start_new_session()

# Process queries
response = brain.process_query("What is artificial intelligence?")
print(response)

# Update context
brain.update_context("user_name", "John")

# Handle follow-up questions
response = brain.process_query("Tell me more")
print(response)

# End session
brain.end_session()
```

### Knowledge Management

```python
# Add new knowledge
brain.add_knowledge_fact(
    category="science",
    question="what is photosynthesis",
    answer="Photosynthesis is the process by which plants convert light energy into chemical energy.",
    confidence=1.0
)

# Search for facts
facts = brain.search_facts("photosynthesis")

# Find similar questions
similar = brain.get_similar_questions("what is AI")
```

### User Preferences

```python
# Set preferences
brain.set_user_preference("theme", "dark")
brain.set_user_preference("voice_speed", 1.2)

# Get preferences
theme = brain.get_user_preference("theme", default="light")
```

### Session Management

```python
# Get session summary
summary = brain.get_session_summary()
print(f"Conversations: {summary['conversation_count']}")
print(f"Common intents: {summary['common_intents']}")

# Export conversation history
history_json = brain.export_conversation_history(format="json")
history_text = brain.export_conversation_history(format="text")
```

## Knowledge Manager

The `KnowledgeManager` class provides utilities for bulk knowledge operations:

```python
from wizard.data.knowledge_manager import KnowledgeManager

km = KnowledgeManager()

# Import knowledge from JSON
km.import_knowledge_from_json("knowledge.json")

# Export knowledge to CSV
km.export_knowledge_to_csv("knowledge.csv")

# Get categories
categories = km.get_categories()

# Get knowledge statistics
stats = km.get_knowledge_stats()
```

## Database Schema

### Facts Table
```sql
CREATE TABLE facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Conversations Table
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_input TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    intent TEXT,
    entities TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### User Preferences Table
```sql
CREATE TABLE user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Response Patterns

The AI brain supports various intent patterns:

- **greeting**: Hello, hi, hey, good morning
- **goodbye**: Bye, goodbye, see you
- **thanks**: Thank you, thanks, appreciate
- **what_time**: What time, current time
- **what_date**: What date, today's date
- **how_are_you**: How are you, how do you feel
- **who_are_you**: Who are you, what are you
- **capabilities**: What can you do, help me
- **general_query**: What is, tell me about, explain

## Testing

Run the test script to verify functionality:

```bash
python test_ai_brain.py
```

Run the demo script to see the AI brain in action:

```bash
python demo_ai_brain.py
```

## Requirements

The AI brain module requires the following dependencies:
- sqlite3 (built-in)
- json (built-in)
- re (built-in)
- random (built-in)
- datetime (built-in)
- pathlib (built-in)
- logging (built-in)

No external dependencies are required for core functionality.

## Integration

The AI brain integrates with other Wizard components:

1. **Command Router**: Provides intent classification and entity extraction
2. **Speech Recognition**: Receives transcribed text for processing
3. **Text-to-Speech**: Sends generated responses for audio output
4. **Configuration Manager**: Loads user preferences and settings

## Performance

- Database operations are optimized with proper indexing
- In-memory caching for frequently accessed data
- Efficient pattern matching with compiled regex
- Minimal memory footprint for continuous operation

## Future Enhancements

Potential improvements for future versions:

- Machine learning-based intent classification
- Multi-language support
- Advanced NLP with entity recognition
- Knowledge graph relationships
- Sentiment analysis
- Personalized response generation
- Voice tone adaptation
