import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from wizard.commands.command_router import route_command

def test_router():
    queries = [
        "play song or video on youtube",
        "write about AI on word",
        "make professional ppt",
        "play song on spotify",
        "collect information from online platform and give responce without opening any kind on pages",
        "send massage through whatsapp to john saying hello"
    ]
    
    print("="*60)
    print(" TESTING NEW INTENT ALIGNMENTS ")
    print("="*60)
    
    # Mock all the execution functions to safely intercept what got called
    with patch('wizard.commands.web_browser.search_youtube') as mock_youtube, \
         patch('wizard.commands.smart_writer.write_about_topic') as mock_writer, \
         patch('wizard.commands.system_control.play_spotify_music') as mock_spotify, \
         patch('wizard.commands.research_assistant.ResearchAssistant.search_and_summarize') as mock_research, \
         patch('pyautogui.hotkey'), \
         patch('pyautogui.typewrite'), \
         patch('pyautogui.press'), \
         patch('time.sleep'):
         
         # specific return values
         mock_youtube.return_value = "YouTube mock success"
         mock_writer.return_value = "Smart writer mock success"
         mock_spotify.return_value = "Spotify mock success"
         mock_research.return_value = "Research mock success"
         
         for q in queries:
             print(f"\n[QUERY] : {q}")
             try:
                 res = route_command(q)
                 print(f"[RESULT]: {res}")
             except Exception as e:
                 print(f"[ERROR] : {e}")

if __name__ == '__main__':
    test_router()
