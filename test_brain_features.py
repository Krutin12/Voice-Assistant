import sys
from wizard.data.ai_brain import AIBrain

def test_master_prompt_logic():
    print("Testing AIBrain Master System Prompt Logic...\n")
    brain = AIBrain()
    
    test_queries = [
        "enable developer mode",
        "teach you a new command",
        "i feel sad",
        "i'm stressed out by work",
        "research ai trends and write a report about it",
        "can you act as a pdf reader",
        "what about the new plugin system",
        "take a screenshot right now",
        "send email to krutin",
        "memory recall",
        "what time is it"  # Should hit standard logic
    ]
    
    success = True
    for query in test_queries:
        print(f"\nUser: {query}")
        response = brain.process_query(query)
        print(f"Wizard: {response}")
        
    print("\n Task feature tests complete!")
    
if __name__ == "__main__":
    test_master_prompt_logic()
