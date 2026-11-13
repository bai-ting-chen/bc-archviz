"""Put the controls folder and its topic folders on sys.path, so controls import each other by name.

Each control adds the controls folder itself, then imports this module.
"""
import os
import sys

CONTROLS = os.path.dirname(os.path.abspath(__file__))
TOPICS = ('archviz', 'tile', 'effects', 'water', 'lighting', 'environment', 'regression')

for folder in [CONTROLS] + [os.path.join(CONTROLS, topic) for topic in TOPICS]:
    if folder not in sys.path:
        sys.path.append(folder)
