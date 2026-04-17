import sys
import os
import time
import traceback
from unittest.mock import patch
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import wizard.main
from wizard.commands.command_router import route_command

# All tasks to test visually and functionally
test_queries = [
    (1,  "who are you"),
    (2,  "set a timer for 1 minute"),
    (3,  "create an alarm for 7 am"),
    (4,  "remind me to call mom at 5 pm"),
    (5,  "add buy groceries to my todo list"),
    (6,  "type hello world into the active app"),
    (7,  "yes"),
    (8,  "check cpu and ram usage"),
    (9,  "what is the battery status"),
    (14, "close all running apps"),
    (15, "increase brightness"),
    (16, "volume up"),
    (17, "send a whatsapp message to john"),
    (18, "translate hello to gujarati"),
    (19, "close this browser tab"),
    (21, "select all and copy"),
    (22, "read the news headlines"),
    (23, "give me my daily briefing"),
    (24, "wikipedia search for artificial intelligence"),
    (25, "what's the weather in london"),
    (26, "navigate to new york"),
    (27, "play despacito on youtube"),
    (28, "pause youtube"),
    (29, "search google for python tutorial"),
    (30, "open github in chrome"),
    (31, "play some jazz on spotify"),
    (32, "next song on spotify"),
    (33, "open my documents folder"),
    (34, "open facebook"),
    (35, "what time is it"),
    (36, "what is today's date"),
    (37, "open notepad and write hello world"),
    (40, "play song or video on youtube"),
    (41, "write about topic on word"),
    (42, "make professional ppt"),
    (43, "play song on spotify"),
    (44, "collect information from online platform and give responce without opening any kind on pages"),
    (45, "send massage through whatsapp or any other massaging application"),
    (99, "exit program")
]

mock_interactions = [q[1] for q in test_queries]
call_count = 0

# Variables to collect results
results = []
passed = 0
failed = 0

# Save original route_command to wrap it
original_route_command = route_command

def wrapped_route_command(text):
    global passed, failed, results
    try:
        # Check if it needs a pending action for 'yes'
        if text == "yes":
            original_route_command.pending_action = lambda: "Confirmed action executed."
            
        res = original_route_command(text)
        
        # Clear pending action if not yes/no
        if hasattr(original_route_command, "pending_action") and text not in ["yes", "no"]:
            delattr(original_route_command, "pending_action")
            
        status = "PASS" if res and len(res.strip()) > 0 else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
            
        # Match with ID
        query_id = "?"
        for qid, qtext in test_queries:
            if qtext == text:
                query_id = qid
                break
                
        results.append(f"[{query_id}] [{status}] Q: {text}\n    A: {res}\n")
        return res
    except Exception as e:
        failed += 1
        query_id = "?"
        for qid, qtext in test_queries:
            if qtext == text:
                query_id = qid
                break
        results.append(f"[{query_id}] [ERROR] Q: {text}\n    E: {e}\n{traceback.format_exc()}\n")
        raise e

def mock_listen(*args, **kwargs):
    # Reduced wait time to speed through the 30+ tests, but long enough for visuals
    time.sleep(2) 
    return "MOCK_AUDIO"

def mock_recognize(recognizer, audio, show_confidence=False):
    global call_count
    if call_count < len(mock_interactions):
        cmd = mock_interactions[call_count]
        call_count += 1
        print(f"\n[Mock Microphone] -> User says: '{cmd}'")
        return cmd, 'mock'
    
    return "exit program", "mock"

def mock_test_microphone(*args, **kwargs):
    return True

def save_results(file_name="vtuber_integration_results.txt"):
    with open(file_name, "w", encoding="utf-8") as f:
        for r in results:
            f.write(r)
        
        # Adjust total back down by 1 because "exit program" is not a tested feature
        total_p = passed
        if results and "exit program" in results[-1] and "PASS" in results[-1]:
             total_p -= 1
        
        f.write(f"\n{'='*60}\nRESULTS: {total_p} PASSED / {failed} FAILED / {total_p+failed} TOTAL\n{'='*60}\n")
    print(f"\n✅ All tests finished. Results saved to {file_name}")

if __name__ == "__main__":
    print("==================================================")
    print(" INTEGRATION TEST: FULL VTUBER + BACKEND TASKS")
    print("==================================================")
    print(f"[INFO] Testing {len(mock_interactions)} commands with live UI...")
    
    # Patch main functions and router
    wizard.main.recognizer_listen = patch("speech_recognition.Recognizer.listen", side_effect=mock_listen)
    wizard.main.test_microphone = mock_test_microphone
    if hasattr(wizard.main, "recognize_speech_with_fallback"):
        wizard.main.recognize_speech_with_fallback = mock_recognize
        
    wizard.commands.command_router.route_command = wrapped_route_command
    sys.modules['wizard.commands.command_router'].route_command = wrapped_route_command
    
    patch_ambient = patch("speech_recognition.Recognizer.adjust_for_ambient_noise")
    
    with wizard.main.recognizer_listen, patch_ambient:
        try:
            wizard.main.main(continuous_mode=True, wake_word_mode=False)
        except Exception as e:
            print(f"Test exited or errored: {e}")
        finally:
            save_results()
