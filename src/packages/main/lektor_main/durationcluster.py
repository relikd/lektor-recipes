# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Union


def int_to_cluster(time: Union[str, int, None], clusters: List[int]) \
        -> Optional[int]:
    '''
    Choose cluster where time >= X and time < X+1
    Example: `[30, 60, 120]` -> (0-29, 30-59, 60-119, 120+)
    Return values are: 36 -> 60, 12 -> 30, 120 -> 121.
    '''
    time = int(time) if time else 0
    if not time:
        return None
    for x in clusters:
        if x > time:
            return x
    return clusters[-1] + 1


def cluster_as_str(
    time: Union[str, int, None],
    clusters: List[int],
    translations: Dict[str, str],
) -> Optional[str]:
    ''' Return descriptive duration range; 30 -> "15 min – 29 min". '''
    time = int(time) if time else 0
    if not time:
        return None
    for idx, x in enumerate(clusters):
        if x == time:
            if idx == 0:
                return '<' + human_readable_duration(time, translations)
            timeA = human_readable_duration(clusters[idx - 1], translations)
            timeB = human_readable_duration(time - 1, translations)
            return u'{} – {}'.format(timeA, timeB)
    return '>' + human_readable_duration(clusters[-1], translations)


def human_readable_duration(
    time: Union[str, int, None], translations: Dict[str, str]
) -> str:
    '''
    Take an arbitrary int and return readable duration string.
    For example, 16 -> "16 mins", 121 -> "2 hours 1 min"
    '''
    time = int(time) if time else 0
    if (time <= 0):
        return ''

    days = time // (60 * 24)
    time -= days * (60 * 24)
    hours = time // 60
    mins = time - hours * 60
    ret = ''
    if days:
        ret += f'{days} {translations["day" if days == 1 else "days"]}'
    if hours:
        if ret:
            ret += ' '
        ret += f'{hours} {translations["hour" if hours == 1 else "hours"]}'
    if mins:
        if ret:
            ret += ' '
        ret += f'{mins} {translations["min" if mins == 1 else "mins"]}'
    return ret
