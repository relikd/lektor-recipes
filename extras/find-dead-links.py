#!/usr/bin/env python3
import os
import re
from contextlib import closing
from mmap import mmap, ACCESS_READ

rx_a = re.compile(br'[@(]\.\./([^/]*)')


def regex_file(file):
    with open(file, 'r') as f:
        with closing(mmap(f.fileno(), 0, access=ACCESS_READ)) as d:
            for x in re.finditer(rx_a, d):
                yield x.group(1).decode('utf-8')


base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
dist_dir = os.path.join(base_dir, 'data', 'distribution')
all_ids = None

for path, dirs, files in os.walk(dist_dir):
    if not all_ids:
        all_ids = dirs
    for lr_file in files:
        if not lr_file.endswith('lr'):
            continue
        for link in regex_file(path + os.path.sep + lr_file):
            if link not in all_ids:
                short_name = os.path.basename(path) + os.path.sep + lr_file
                print(f'dead-link: {short_name} ({link})')

print('done.')
