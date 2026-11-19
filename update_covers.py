#!/usr/bin/env python3
"""Uzupełnia w games.json poprawne okładki (pole "img") oraz brakujące "id" ze Steama.

Nowsze gry mają okładki pod adresem z hashem, którego nie da się odgadnąć,
więc skrypt pyta oficjalne API Steam o dokładny adres.
Uruchomienie: python update_covers.py   (tylko biblioteka standardowa)
Gra z polem "imgLock": true zostaje pominięta (ręcznie ustawiona okładka).
"""
import json, re, sys, time, urllib.parse, urllib.request, urllib.error

PATH = 'games.json'
UA = {'User-Agent': 'Mozilla/5.0 (cover-updater for gramy-razem)'}
PAUSE = 1.3  # sekundy między zapytaniami, żeby Steam nie blokował


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(15 * (i + 1) if e.code in (403, 429) else 3)
        except Exception:
            time.sleep(3)
    return None


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def find_id(name):
    """Zwraca id tylko przy dokładnym dopasowaniu nazwy, żeby nie wpisać złej gry."""
    d = get('https://store.steampowered.com/api/storesearch/?term='
            + urllib.parse.quote(name) + '&l=english&cc=pl')
    for it in (d or {}).get('items', []):
        if it.get('type') == 'app' and norm(it.get('name', '')) == norm(name):
            return it['id']
    return None


def header(appid):
    d = get(f'https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic&l=english')
    e = (d or {}).get(str(appid)) or {}
    if e.get('success'):
        url = (e.get('data', {}).get('header_image') or '').split('?')[0]
        return url or None
    return None


def main():
    with open(PATH, encoding='utf8') as f:
        games = json.load(f)
    found_ids, new_imgs, no_cover = [], 0, []
    for i, g in enumerate(games, 1):
        if g.get('imgLock'):
            continue
        if not g.get('id'):
            gid = find_id(g['n']); time.sleep(PAUSE)
            if gid:
                g['id'] = gid; found_ids.append(g['n'])
        if g.get('id'):
            url = header(g['id']); time.sleep(PAUSE)
            if url and url != g.get('img'):
                g['img'] = url; new_imgs += 1
            elif not url and not g.get('img'):
                no_cover.append(g['n'])
        else:
            no_cover.append(g['n'])
        print(f'[{i}/{len(games)}] {g["n"]}', flush=True)
    with open(PATH, 'w', encoding='utf8') as f:
        f.write('[\n' + ',\n'.join(json.dumps(g, ensure_ascii=False) for g in games) + '\n]\n')
    print(f'\nNowe lub zmienione okładki: {new_imgs}')
    print('Znalezione brakujące id:', ', '.join(found_ids) or '—')
    print('Dalej bez okładki (użyje grafiki zastępczej):', ', '.join(no_cover) or '—')


if __name__ == '__main__':
    sys.exit(main())
