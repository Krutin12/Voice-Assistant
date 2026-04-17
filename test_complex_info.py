
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import route_command

def test_complex_info():
    test_cases = [
        "give me the all information about ajit pawar death",
        "give me some detailed information on renewable energy",
        "explain something about mars rover",
        "find information about the latest news in india",
        "give me all information on global warming"
    ]
    
    print(f"{'INPUT':<60} | {'RESULT'}")
    print("-" * 120)
    
    for query in test_cases:
        try:
            print(f"Testing: {query}")
            response = route_command(query)
            # Check for generic failure message
            failed = "I couldn't summarize it easily" in response or query in response.lower()
            status = "❌" if failed else "✅"
            print(f"{' ': <60} | {status} {response[:100]}...")
            print("-" * 120)
        except Exception as e:
            print(f"{query:<60} | ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_complex_info()
