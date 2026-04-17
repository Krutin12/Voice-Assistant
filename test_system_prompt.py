import sys
import os

try:
    from wizard.core import MASTER_SYSTEM_PROMPT
    print("Successfully imported MASTER_SYSTEM_PROMPT from wizard.core!")
    print(f"Prompt length: {len(MASTER_SYSTEM_PROMPT)} characters")
    print("Beginning of prompt:")
    print(MASTER_SYSTEM_PROMPT[:100].encode('utf-8', 'replace').decode('utf-8') + "...")
    sys.exit(0)
except Exception as e:
    print(f"Failed to import: {e}")
    sys.exit(1)
