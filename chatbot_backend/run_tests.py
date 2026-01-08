#!/usr/bin/env python
"""
Test runner script for Lead Generation Chatbot

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py ConversationFlow   # Run specific test class
    python run_tests.py --verbose          # Run with verbose output
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_backend.settings')
django.setup()

from django.core.management import call_command


def run_tests():
    """Run all tests with coverage"""
    
    print("=" * 70)
    print("LEAD GENERATION CHATBOT - TEST SUITE")
    print("=" * 70)
    print()
    
    # Run tests
    if len(sys.argv) > 1 and sys.argv[1] == "--verbose":
        call_command('test', 'chat.tests', verbosity=2)
    elif len(sys.argv) > 1:
        # Run specific test
        test_pattern = sys.argv[1]
        call_command('test', f'chat.tests.test_conversation_flow.{test_pattern}', verbosity=2)
    else:
        call_command('test', 'chat.tests', verbosity=1)
    
    print()
    print("=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    run_tests()
