"""
Loading messages collection for IntelliSearch CLI.

This module contains random programmer jokes and messages
displayed during loading states to keep users entertained.
"""

import random

# Programmer jokes and messages for processing state
PROCESSING_MESSAGES = [
    "Parsing the infinite loop of your request...",
    "Consulting the Magic 8-Ball for answers...",
    "Training hamsters to run faster...",
    "Searching for the missing semicolon...",
    "Compiling your thoughts into bytecode...",
    "Asking the rubber duck for help...",
    "Converting coffee into code...",
    "Debugging the fabric of reality...",
    "Loading useful information (and some jokes)...",
    "Optimizing the algorithms of knowledge...",
]

# Messages for summarizing state (final response generation)
SUMMARIZING_MESSAGES = [
    "Connecting the dots in the knowledge graph...",
    "Synthesizing wisdom from scattered data...",
    "Weaving information into coherent answers...",
    "Distilling essence from raw data...",
    "Crafting the perfect response for you...",
    "Turning data into understanding...",
    "Baking knowledge into a fresh response...",
    "Composing the symphony of information...",
    "Translating machine thoughts to human language...",
    "Preparing the final answer with extra care...",
]


def get_random_processing_message() -> str:
    """
    Get a random processing message from the collection.

    Returns:
        Random message string
    """
    return random.choice(PROCESSING_MESSAGES)


def get_random_summarizing_message() -> str:
    """
    Get a random summarizing message from the collection.

    Returns:
        Random message string
    """
    return random.choice(SUMMARIZING_MESSAGES)
