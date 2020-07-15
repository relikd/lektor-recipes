# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin

durationLocale = {
    'de': {'day': 'Tag', 'hour': 'Std', 'min': 'Min',
           'days': 'Tage', 'hours': 'Std', 'mins': 'Min'},
    'en': {'day': 'day', 'hour': 'hour', 'min': 'min',
           'days': 'days', 'hours': 'hours', 'mins': 'min'}
}

# -----------
# Single Time


def pluralize(n, single, multi):
    if n == 0:
        return ''
    return u'{} {}'.format(n, single if n == 1 else multi)


def to_duration(time, alt='en'):
    time = int(time) if time else 0
    if (time <= 0):
        return ''
    days = time // (60 * 24)
    time -= days * (60 * 24)
    L = durationLocale[alt]
    return ' '.join([
        pluralize(days, L['day'], L['days']),
        pluralize(time // 60, L['hour'], L['hours']),
        pluralize(time % 60, L['min'], L['mins'])]).strip()

# ------------
# Time Cluster


def to_time_in_cluster(time, cluster, alt='en'):
    for idx, x in enumerate(cluster):
        x = int(x)
        if x == time:
            if idx == 0:
                timeB = to_duration(time, alt)
                return '<' + timeB
            else:
                timeA = to_duration(cluster[idx - 1], alt)
                timeB = to_duration(time - 1, alt)
                return u'{} – {}'.format(timeA, timeB)
    else:
        return '>' + to_duration(cluster[-1], alt)


def find_in_cluster(key, clusterList=[30, 60, 120]):
    key = int(key) if key else 0
    if key > 0:
        for cluster in clusterList:
            if key < cluster:
                key = cluster
                break
        else:
            key = clusterList[-1] + 1
    return key


def group_by_time_cluster(dic, arr=[30, 60, 120], reverse=False):
    arr = sorted([int(x) for x in arr])
    groups = dict()
    for key, recipes in dic:
        key = find_in_cluster(key, arr)
        if key == 0 and not reverse:
            key = ''
        try:
            groups[key]
        except KeyError:
            groups[key] = set()
        groups[key].update(recipes)
    return sorted(groups.items(), reverse=bool(reverse),
                  key=lambda x: x[0] if x[0] != '' else 999999999)


class TimeDurationPlugin(Plugin):
    name = u'Time Duration'
    description = u'Convert int to duration. E.g., 90 -> "1hr 30min".'

    def on_setup_env(self, **extra):
        self.env.jinja_env.filters['duration'] = to_duration
        self.env.jinja_env.filters['durationCluster'] = to_time_in_cluster
        self.env.jinja_env.filters['groupTimeCluster'] = group_by_time_cluster
