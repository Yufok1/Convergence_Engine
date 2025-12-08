#!/usr/bin/env python3
"""Test the 7-agent swarm chat."""
from standalone_butterfly_chat import StandaloneButterflyChat

chat = StandaloneButterflyChat('agent_downloads/cocoon_ensemble_20251208164133')
print('Testing chat with 7-agent swarm...')
print()

messages = ['Hello', 'What do you think about cooperation?', 'Tell me about survival']

for msg in messages:
    r = chat.chat(msg)
    response = r if r else "(no response)"
    print(f'User: {msg}')
    print(f'Bot:  {response}')
    print()
