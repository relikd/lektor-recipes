# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin
from lektor.databags import Databags
import unicodedata
import os
import shutil

# -------
# Sorting


def sortKeyInt(x):
    return int(x[0]) if x[0] else 0


def sortKeyStr(x):
    return noUmlaut(x[0]).lower()


def groupByDictSort(dic, sorter=None, reverse=False):
    if type(sorter) == list:  # sort by pre-defined, ordered list
        return sorted(dic, reverse=bool(reverse), key=lambda x:
                      sorter.index(x[0]) if x[0] in sorter else 0)
    fn = sortKeyInt if sorter == 'int' else sortKeyStr
    return sorted(dic, reverse=bool(reverse), key=fn)

# -----------------------
# Pure text manupulations


def noUmlaut(text):
    try:
        text = unicode(text, 'utf-8')
    except (TypeError, NameError):
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def pluralize(n, single, multi):
    if n == 0:
        return ''
    return u'{} {}'.format(n, single if n == 1 else multi)


def replaceFractions(txt):
    res = ''
    for x in txt.split():
        try:
            i = ['1/2', '1/3', '2/3', '1/4', '3/4', '1/8', '-'].index(x)
            res += [u'½', u'⅓', u'⅔', u'¼', u'¾', u'⅛', u' - '][i]
        except ValueError:
            res += ' ' + x
    return res.lstrip()


def numFillWithText(num, fill=u'★', empty=u'☆', total=5):
    num = int(num) if num else 0
    return fill * num + empty * (total - num)

# ------------------
# Array manipulation


def updateSet_if(dic, parent, parentkey, value):
    try:
        key = parent[parentkey]
    except KeyError:
        return
    if not key:
        key = ''
    try:
        dic[key]
    except KeyError:
        dic[key] = set()
    dic[key].add(value)


def updateSet_addMultiple(dic, key, others):
    try:
        dic[key]
    except KeyError:
        dic[key] = set()
    dic[key].update(others)


def findCluster(key, clusterList=[30, 60, 120]):
    key = int(key) if key else 0
    if key > 0:
        for cluster in clusterList:
            if key < cluster:
                key = cluster
                break
    return key

# --------------------
# Ingredient splitting


def splitIngredientLine(line):
    state = 1
    capture = False
    indices = [0, len(line)]
    for i, char in enumerate(line):
        if char.isspace():
            capture = False
            indices[state] = i
            state += 1
            continue
        elif capture:
            continue
        elif state == 1 and char in '0123456789-.,':
            state -= 1
        elif state > 1:
            break
        capture = True
    return indices


def parseIngredientLine(line, measureList=[], rep_frac=False):
    idx = splitIngredientLine(line)
    val = line[:idx[0]]
    if rep_frac:
        val = replaceFractions(val)
    measure = line[idx[0]:idx[1]].lstrip()
    if measure.lower() in measureList:
        name = line[idx[1]:].lstrip()
    else:
        measure = ''
        name = line[idx[0]:].lstrip()
    note = ''
    name_note = name.split(',', 1)
    if len(name_note) > 1:
        name, note = [x.strip() for x in name_note]
    return {'value': val, 'measure': measure, 'name': name, 'note': note}

# --------------------
# Other Helper methods


def groupByMergeCluster(dic, arr=[30, 60, 120], reverse=False):
    arr = sorted([int(x) for x in arr])
    groups = dict()
    for key, recipes in dic:
        key = findCluster(key, arr)
        if key == 0 and not reverse:
            key = ''
        updateSet_addMultiple(groups, key, recipes)
    return sorted(groups.items(), reverse=bool(reverse))

# ----------------
# Main entry point


class HelperPlugin(Plugin):
    name = u'Helper'
    description = u'Some helper methods, filters, and templates.'
    alt = None
    availableTags = set()

    # -----------
    # Event hooks
    # -----------

    def on_before_build_all(self, builder, **extra):
        # display only tags that contain at least one recipe
        pad = self.env.new_pad()
        for r in pad.query('recipes'):
            self.availableTags.update(r['tags'])

    def on_after_prune(self, builder, **extra):
        # redirect to /en/
        for file in ['index.html']:
            src_f = os.path.join(self.env.root_path, 'root', file)
            if os.path.exists(src_f):
                dst_f = os.path.join(builder.destination_path, file)
                with open(dst_f, 'wb') as df:
                    with open(src_f, 'rb') as sf:
                        shutil.copyfileobj(sf, df)

    def on_process_template_context(self, context, **extra):
        self.alt = context['alt']

    def on_setup_env(self, **extra):
        # self.env.load_config().iter_alternatives()
        # pad = self.env.new_pad()
        # pad.query('groupby', alt=alt)

        def localizeDic(key, subkey=None):
            bag = Databags(self.env).lookup('i18n+{}.{}'.format(self.alt, key))
            return bag[subkey] if subkey else bag

        def to_duration(time, cluster=None):
            time = int(time) if time else 0
            if (time <= 0):
                return ''
            # Calls itself without cluster argument
            if cluster:
                cluster = [int(x) for x in cluster]
                idx = cluster.index(time)
                if idx == 0:
                    return '<' + to_duration(time)
                timeA = to_duration(cluster[idx - 1])
                if idx + 1 >= len(cluster):
                    return '>' + timeA
                else:
                    return u'{} – {}'.format(timeA, to_duration(time))
            days = time // (60 * 24)
            time -= days * (60 * 24)
            L = localizeDic('duration')
            return ' '.join([
                pluralize(days, L['day'], L['days']),
                pluralize(time // 60, L['hour'], L['hours']),
                pluralize(time % 60, L['min'], L['mins'])]).strip()

        def ingredientsForRecipe(recipe):
            set = self.env.new_pad().get('settings', alt=self.alt)
            meaList = [x.strip() for x in set['measures'].lower().split(',')]
            repFrac = set['replace_frac']

            for line in recipe['ingredients']:
                line = line.strip()
                if not line:
                    continue
                elif line.endswith(':'):
                    yield {'group': line}
                else:
                    yield parseIngredientLine(line, meaList, repFrac)

        def groupByAttribute(recipeList, attribute):
            groups = dict()
            for recipe in recipeList:
                if attribute == 'ingredients':
                    for ing in ingredientsForRecipe(recipe):
                        updateSet_if(groups, ing, 'name', recipe)
                else:
                    updateSet_if(groups, recipe, attribute, recipe)
            # groups[undefinedKey].update(groups.pop('_undefined'))
            return groups.items()

        self.env.jinja_env.filters['duration'] = to_duration
        self.env.jinja_env.filters['rating'] = numFillWithText
        self.env.jinja_env.filters['replaceFractions'] = replaceFractions
        self.env.jinja_env.filters['enumIngredients'] = ingredientsForRecipe
        self.env.jinja_env.filters['groupByAttribute'] = groupByAttribute
        self.env.jinja_env.filters['groupSort'] = groupByDictSort
        self.env.jinja_env.filters['groupMergeCluster'] = groupByMergeCluster
        self.env.jinja_env.globals['localize'] = localizeDic
        self.env.jinja_env.globals['availableTags'] = self.availableTags
