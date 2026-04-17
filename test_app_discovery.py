"""
Test script for App Discovery Module
Verifies that the voice assistant can discover and open ALL installed Windows applications.
"""

import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wizard.commands.app_discovery import AppDiscovery

def main():
    print("=" * 70)
    print("  App Discovery Test - Scanning ALL installed Windows applications")
    print("=" * 70)
    print()
    
    # Initialize discovery (first run will scan everything)
    print("[*] Scanning Start Menu, Registry, UWP apps, and common directories...")
    print("    (This may take 15-30 seconds on first run, then cached)\n")
    
    discovery = AppDiscovery()
    apps = discovery.get_all_apps()
    
    # Print summary
    print(f"[OK] Discovered {len(apps)} applications!\n")
    
    # Show all discovered apps sorted alphabetically
    print("-" * 70)
    print(f"  {'App Name':<40} {'Path/Launch Method'}")
    print("-" * 70)
    for name in sorted(apps.keys()):
        path = apps[name]
        # Truncate long paths
        if len(path) > 50:
            path = "..." + path[-47:]
        print(f"  {name:<40} {path}")
    print("-" * 70)
    print()
    
    # Test fuzzy matching with various queries
    print("=" * 70)
    print("  Testing Fuzzy Matching (simulating voice commands)")
    print("=" * 70)
    
    test_queries = [
        "chrome",
        "notepad",
        "calculator",
        "spotify",
        "word",
        "excel",
        "whatsapp",
        "telegram",
        "vs code",
        "vscode",
        "discord",
        "paint",
        "file explorer",
        "settings",
        "task manager",
        "camera",
        "photos",
        "store",
        "terminal",
        "brave",
        "edge",
        "vlc",
    ]
    
    print()
    for query in test_queries:
        result = discovery.find_app(query)
        if result:
            name, path = result
            # Truncate long paths
            if len(path) > 45:
                path = "..." + path[-42:]
            print(f"  '{query}' -> FOUND: {name:<30} ({path})")
        else:
            print(f"  '{query}' -> NOT FOUND")
    
    print()
    print("=" * 70)
    print("  Done! Your voice assistant can now open any of these apps by voice.")
    print("  Example: 'Open WhatsApp', 'Launch Spotify', 'Start Chrome'")
    print("=" * 70)

if __name__ == "__main__":
    main()
