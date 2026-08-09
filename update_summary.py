#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ממזג ערים חדשות ל-summary.json (נקרא ע"י סוכן הענן אחרי WebFetch)."""
import json, sys, os
path = 'summary.json'
existing = {}
if os.path.exists(path):
    try: existing = json.load(open(path, encoding='utf-8')).get('cities', {})
    except Exception: existing = {}
new = json.load(open(sys.argv[1], encoding='utf-8'))  # {city: {code, as_of, by_rooms}}
existing.update(new)
json.dump({'cities': existing}, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
print('merged: %d new, %d total' % (len(new), len(existing)))
