#!/usr/bin/env python3
import os
import sys

'''
Usage:  python3  generate-alternates.py  development/*

Input is a recipe folder.
Will take the `contents.lr` and extract `contents+de.lr` and `contents+en.lr`.
The content will be identical but its easier to edit this way.
No necessary redundant data fields.
'''


def prnt(key, val, inline=True):
    return '' if not val else '{}:{}{}\n---\n'.format(
        key, ' ' if inline else '\n\n', str(val).strip())


def splitContent(path):
    mode = 1
    idx = 0
    with open(os.path.join(path, 'contents.lr'), 'r') as fin:
        tmp = ['', '']
        for line in fin:
            if mode == 1:
                tag = line.split(':')[0]
                if tag in ['name', 'yield', 'ingredients', 'directions']:
                    idx = 1
                else:
                    idx = 0
                tmp[idx] += line
                mode = 2
            else:
                tmp[idx] += line
                if line == '---\n':
                    mode = 1
        tmp[1] = tmp[1][:-4]
        return tmp


def writeSplit(path):
    de_file = os.path.join(path, 'contents+de.lr')
    if not os.path.isdir(path) or os.path.exists(de_file):
        return
    print(path)
    content = splitContent(path)
    if not content[1]:
        return
    with open(de_file, 'w') as f:
        f.write(content[1])
    with open(os.path.join(path, 'contents+en.lr'), 'w') as f:
        f.write(content[1])
    with open(os.path.join(path, 'contents.lr'), 'w') as f:
        f.write(content[0])


for x in sys.argv[1:]:
    writeSplit(x)
