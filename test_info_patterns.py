
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import route_command

def test_info():
    test_cases = [
        ("give me some information about medical", "medical"),
        ("find information on artificial intelligence", "artificial intelligence"),
        ("medical vise mahiti apo", "medical"),
        ("tell me about space exploration", "space exploration")
    ]
    
    print(f"{'INPUT':<50} | {'RESULT'}")
    print("-" * 100)
    
    for query, expected_topic in test_cases:
        try:
            # We check if the research assistant is triggered. 
            # In our mock/controlled environment, researcher.search_and_summarize
            # will return a string like "According to Wikipedia..." or "I found information..."
            response = route_command(query)
            
            # Since research assistant actually hits the web, we'll check if it 
            # mentions the topic or starts with a research indicator.
            success = expected_topic.lower() in response.lower() or "Wikipedia" in response or "search" in response
            status = "✅" if success else "❌"
            print(f"{query:<50} | {status} {response[:100]}...")
        except Exception as e:
            print(f"{query:<50} | ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_info()
