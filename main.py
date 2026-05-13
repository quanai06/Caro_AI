#!/usr/bin/env python3
import sys
from caro_ai.app import main, start_demo_ui

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        start_demo_ui()
    else:
        main()