#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""מושך מ-data.nadlan.gov.il תמצית חציוני עסקאות לכל יישוב בישראל וכותב summary.json.

רץ שבועית ב-GitHub Actions (הנתונים באתר מתעדכנים רבעונית).
לכל יישוב: חציון מחיר אחרון לפי מספר חדרים + שינוי שנתי ודו-שנתי באחוזים.
יישוב בלי סדרת נתונים מדולג. כשל בודד לא מפיל את הריצה.
"""
import json
import sys
import time
import urllib.request

HDRS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'),
    'Origin': 'https://www.nadlan.gov.il',
    'Referer': 'https://www.nadlan.gov.il/',
}
DATA_BASE = 'https://data.nadlan.gov.il/api'


def fetch_json(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode('utf-8-sig'))
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2 * (attempt + 1))


def pct(new, old):
    if not new or not old:
        return None
    return round(100.0 * (new - old) / old, 1)


def summarize(page):
    out = {}
    as_of = None
    for series in (page.get('trends', {}) or {}).get('rooms', []) or []:
        label = str(series.get('numRooms'))
        pts = [(p.get('year'), p.get('month'),
                p.get('neighborhoodPrice') or p.get('settlementPrice'))
               for p in (series.get('graphData') or [])]
        pts = [(y, m, v) for (y, m, v) in pts if v]
        if not pts:
            continue
        pts.sort(reverse=True)
        y, m, latest = pts[0]
        year_ago = next((v for (yy, mm, v) in pts if (y - yy) * 12 + (m - mm) >= 12), None)
        two_years = next((v for (yy, mm, v) in pts if (y - yy) * 12 + (m - mm) >= 24), None)
        out[label] = {'median': latest, 'quarter': '%d/%02d' % (y, m),
                      'yoy_pct': pct(latest, year_ago), 'two_year_pct': pct(latest, two_years)}
        as_of = as_of or ('%d/%02d' % (y, m))
    return out, as_of


def main():
    idx = fetch_json(DATA_BASE + '/index/setl_types.json')
    result, ok, skipped, failed = {}, 0, 0, 0
    codes = sorted(idx.keys(), key=lambda c: -(idx[c].get('POPULATION') or 0))
    for i, code in enumerate(codes):
        name = (idx[code].get('SETL_NAME') or '').strip()
        if not name:
            continue
        try:
            page = fetch_json('%s/pages/settlement/buy/%s.json' % (DATA_BASE, code))
            by_rooms, as_of = summarize(page)
            if by_rooms:
                result[name] = {'code': int(code), 'as_of': as_of, 'by_rooms': by_rooms}
                ok += 1
            else:
                skipped += 1
        except Exception as e:
            failed += 1
            if failed <= 10:
                print('FAIL %s (%s): %s' % (name, code, e), file=sys.stderr)
        if i % 100 == 0:
            print('%d/%d done (ok=%d skip=%d fail=%d)' % (i, len(codes), ok, skipped, failed), flush=True)
        time.sleep(0.25)

    with open('summary.json', 'w', encoding='utf-8') as f:
        json.dump({'generated_ok': ok, 'skipped': skipped, 'failed': failed,
                   'cities': result}, f, ensure_ascii=False)
    print('DONE ok=%d skip=%d fail=%d' % (ok, skipped, failed))
    if ok < 100:
        sys.exit(1)  # משהו שבור מהותית — אל תדרוס summary תקין בקומיט ריק


if __name__ == '__main__':
    main()
