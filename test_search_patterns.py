
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import route_command

def test_search():
    test_cases = [
        ("search python on google", "Searching Google for python"),
        ("google python search", "Searching Google for python"),
        ("google search for python", "Searching Google for python"),
        ("python vise sodh", "Searching Google for python"),
        ("google par python sodho", "Searching Google for python"),
        ("search machine learning in google", "Searching Google for machine learning"),
    ]
    
    print(f"{'INPUT':<40} | {'RESULT'}")
    print("-" * 80)
    
    for query, expected_snippet in test_cases:
        try:
            response = route_command(query)
            success = expected_snippet.lower() in response.lower()
            status = "✅" if success else "❌"
            print(f"{query:<40} | {status} {response}")
        except Exception as e:
            print(f"{query:<40} | ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_search()
