#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the standalone CLI
from standalone_butterfly_chat import main

if __name__ == '__main__':
    main()
