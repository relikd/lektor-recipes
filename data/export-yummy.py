#!/usr/bin/env python3
import sqlite3
import os
import sys
from datetime import datetime

'''
Usage:  python3  generate-alternates.py  '…/YummySoup.library/Database.SQL'

You may have to adjust `mapTag`, `clearUTF()`, and `slugify()` below.
Output is generated in the current folder under `yummysoup-exported`.
'''

# check if input param is SQL database file
try:
    inputPath = os.path.abspath(sys.argv[1])
    if not os.path.isfile(inputPath) or not inputPath.upper().endswith('SQL'):
        raise Exception()
    base = os.path.dirname(inputPath)
    print('connecting...')
    db = sqlite3.connect(inputPath)
except Exception:
    print()
    print(f'usage: {os.path.basename(sys.argv[0])} "path/to/db.SQL"')
    print('(e.g., "…/YummySoup! Librarys.library/Library Database.SQL")')
    print()
    exit()

# create output export dir if necessary
_out = os.path.abspath('./yummysoup-exported/')
if not os.path.exists(_out):
    os.mkdir(_out)

# map old tags to new one. Should be all available tags in YummySoup!
# right hand side must be lower case string or None
mapTag = {
    '': None,
    'Weihnachten': 'xmas',
    'Wurst': None,
    'Dressing': 'dressing',
    'Soße': 'sauce',
    'Hauptspeise': 'main-dish',
    'Süßes': 'sweet',
    'Zutat': 'ingredient',
    'Raw': 'raw',
    'Aufstrich': 'spread',
    'Brot': 'bread',
    'Kuchen': 'cake',
    'Kekse': 'cookies',
    'trocken': None,
    'Salat': 'salad',
    'Drink': 'drinks',
    'Riegel': None,
    'Schokolade': 'chocolate',
    'Dip': 'dip',
    'fruchtig': None,
    'Glutenfrei': 'glutenfree'
}


def ttoint(txt):
    i, n = txt.split(' ') if txt else (0, 'M')
    return int(i) * [1, 60, 1440]['MST'.index(n[0])]


# def matchTime(time):
#     if time in [0, 25, 135, 165, 300]:
#         return [None, 30, 150, 150, 360][[0, 25, 135, 165, 300].index(time)]
#     prev = 99999
#     val = time
#     for x in [5, 10, 15, 20, 30, 45, 60, 75, 90, 105,
#               120, 150, 180, 240, 360, 480, 720, 1440]:
#         diff = abs(time - x)
#         if diff < prev:
#             prev = diff
#             val = x
#         elif diff == prev:
#             print(time)
#     return val


def clearUTF(txt):
    return txt.replace('\\U00df', 'ß').replace('\\U00f1', 'ñ')\
        .replace('\\U00c4', 'Ä').replace('\\U00e4', 'ä')\
        .replace('\\U00d6', 'Ö').replace('\\U00f6', 'ö')\
        .replace('\\U00dc', 'Ü').replace('\\U00fc', 'ü')


def slugify(txt):
    return txt.lower().replace(' ', '-').replace(':', '').replace('ß', 'ss')\
        .replace('(', '').replace(')', '').replace(',', '').replace('ê', 'e')\
        .replace('ä', 'ae').replace('ü', 'ue').replace('ö', 'oe').strip('-')


def formatIngredient(info):
    try:
        if info['isG'] in ['YES', '1']:
            return '\n' + info['nam']
    except KeyError:
        pass
    txt = info['nam'].replace(',', ' ')
    if info['mea']:
        txt = '{} {}'.format(info['mea'], txt)
    if info['qua']:
        txt = '{} {}'.format(info['qua'], txt)
    if info['met']:
        txt = '{}, {}'.format(txt, info['met'])
    return txt


def ingredientToStr(txt):
    res = ''
    for ing in clearUTF(txt).split('},'):
        ing = ing.strip('{()} \n')
        info = {'qua': '', 'mea': '', 'nam': '', 'met': ''}
        for prop in ing.split(';'):
            if not prop:
                continue
            k, v = [x.strip('\n "') for x in prop.split('=')]
            info[k[:3]] = v
        res += '\n' + formatIngredient(info)
    return res


def directionsToStr(txt):
    return txt.replace('<font face="" size="">', '').replace(' ', '')\
        .replace('</font>', '').replace('<br>', '').replace('<b>', '__').\
        replace('</b>', '__').replace('<i>', '_').replace('</i>', '_')\
        .replace('℃', '°C').replace(' °C', '°C')\
        .replace('½', '1/2').replace('¼', '1/4').replace('⅛', '1/8')\
        .replace('⅓', '1/3').replace('⅔', '2/3').replace('¾', '3/4')


def prnt(key, val, inline=True):
    return '' if not val else '{}:{}{}\n---\n'.format(
        key, ' ' if inline else '\n\n', str(val).strip())


def export(slug, content, img):
    output = os.path.join(_out, slug)
    for i in range(10):
        folder = output
        if i > 0:
            folder += '-%d' % i
        if not os.path.isdir(folder):
            output = folder
            break
    os.mkdir(output)
    with open(os.path.join(output, 'contents.lr'), 'w') as f:
        f.write(txt.strip().rstrip('-'))

    for i in range(1, 10):
        src = img % i
        dest = os.path.join(output, f'image{"" if i == 1 else i}.jpg')
        if not os.path.isfile(src):
            break
        with open(src, 'rb') as a, open(dest, 'wb') as b:
            b.write(a.read())


print('exporting...')
for row in db.cursor().execute('''SELECT * FROM ZRECIPES'''):
    difficulty, rating, date, img = row[4], row[7], row[9], row[10]
    duration, tags, name, yields = row[12:15], row[15], row[17], row[21]
    notes, directions, source, ingredients = row[23], row[25], row[26], row[27]

    # preprocess
    date = datetime.fromtimestamp(date + 978307200).strftime('%Y-%m-%d')
    img = os.path.join(base, 'Images', img + '-Image%d.jpg')
    duration = sum([ttoint(x) for x in duration])  # matchTime()
    tags = ', '.join(sorted([mapTag[x] for x in tags.split(',') if mapTag[x]]))
    slug = slugify(name)
    if yields:
        y = yields.split(' ')
        if len(y) == 3 and y[1].endswith('form'):
            yields = '{} {}'.format(y[2], y[1])

    txt = ''
    txt += prnt('name', name)
    txt += prnt('tags', tags)
    txt += prnt('time', duration)
    txt += prnt('difficulty', [None, 'easy', 'medium', 'hard'][difficulty])
    txt += prnt('rating', rating)
    txt += prnt('yield', yields)
    txt += prnt('ingredients', ingredientToStr(ingredients), False)
    desc = directionsToStr(directions)
    if notes:
        desc = '{}\n\n__Notes:__ {}'.format(desc.strip(), notes)
    txt += prnt('directions', desc, False)
    txt += prnt('source', source)
    txt += prnt('date', date)

    export(slug, txt, img)

db.close()
print('done.')
