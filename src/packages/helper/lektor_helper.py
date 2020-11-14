# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin, get_plugin
from lektor.databags import Databags
from markupsafe import Markup
from datetime import datetime
import unicodedata
import lektor_html_to_tex as tex

# -------
# Sorting


def sorted_images(obj, attr='record_label'):
    return sorted(obj.attachments.images, key=lambda x: getattr(x, attr))


def title_image(self, attr='record_label', small=False):
    img = (sorted_images(self, attr) or [None])[0]
    if img and small:
        img = img.thumbnail(200, 150, mode='crop')
    return img


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


def replaceFractions(txt):
    res = ' '
    for c in u'-–—':
        if c in txt:
            txt = txt.replace(c, ' – ')
    for x in txt.split():
        if x == '':
            continue
        try:
            i = ['1/2', '1/3', '2/3', '1/4', '3/4', '1/8'].index(x)
            res += [u'½', u'⅓', u'⅔', u'¼', u'¾', u'⅛'][i]
        except ValueError:
            if x == '–':
                res += '–'
            elif res[-1:] == '–':
                res += x
            else:
                res += ' ' + x
    return res.lstrip(' ')


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

# --------------------
# Ingredient splitting


def splitIngredientLine(line):
    state = 1
    capture = False
    indices = [0, len(line)]
    for i, char in enumerate(line):
        if char.isspace():
            if capture:
                capture = False
                indices[state] = i
                state += 1
            continue
        elif capture:
            continue
        elif state == 1 and char in u'0123456789-–—.,':
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
        # if name.startswith('of '):
        #     measure += ' of'
        #     name = name[3:]
    else:
        measure = ''
        name = line[idx[0]:].lstrip()
    note = ''
    name_note = name.split(',', 1)
    if len(name_note) > 1:
        name, note = [x.strip() for x in name_note]
    return {'value': val, 'measure': measure, 'name': name, 'note': note}


def replace_atref_urls(text, label=None):
    if '@' not in text:
        return text
    result = list()
    for x in text.split():
        if x[0] == '@':
            x = x[1:]
            result.append(u'<a href="{}">{}</a>'.format(x, label or x))
        else:
            result.append(x)
    return Markup(' '.join(result))

# ----------------
# Main entry point


class HelperPlugin(Plugin):
    name = u'Helper'
    description = u'Some helper methods, filters, and templates.'
    buildTime = None
    settings = dict()
    translations = dict()

    # -----------
    # Event hooks
    # -----------

    def processCLI(self, extra_flags):
        useCache = bool(extra_flags.get('ENABLE_APPCACHE'))
        plugin = get_plugin('force-update', self.env)
        if plugin.enabled and not useCache:
            plugin.enabled = False
        print('AppCache: ' + ('ENABLED' if useCache else 'DISABLED'))
        self.env.jinja_env.globals['ENABLE_APPCACHE'] = useCache

    def processSettings(self):
        bag = Databags(self.env)
        pad = self.env.new_pad()
        for alt in self.env.load_config().iter_alternatives():
            set = pad.get('settings', alt=alt)
            self.translations[alt] = bag.lookup('i18n+' + alt)
            self.settings[alt] = {
                'measures': set['measures'].lower().split(),
                'replFrac': set['replace_frac']
            }

    def on_before_build_all(self, builder, **extra):
        build_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('Build time: ' + build_time)
        self.env.jinja_env.globals['DATE_NOW'] = build_time
        # update project settings once per build
        self.processCLI(getattr(builder, 'extra_flags'))
        self.processSettings()

    # def on_process_template_context(self, context, **extra):
    #     pass

    def on_setup_env(self, **extra):
        def localizeDic(alt, partA, partB=None):
            if alt not in self.translations:
                raise RuntimeError(
                    'localize() expects first parameter to be an alternate')
            if partB is None:
                partA, partB = partA.split('.', 1)
            return self.translations[alt][partA][partB]

        def ingredientsForRecipe(recipe, alt='en', mode='raw'):
            meaList = self.settings[alt]['measures']
            repFrac = self.settings[alt]['replFrac']

            for line in recipe['ingredients']:
                line = tex.raw_text_to_tex(line).strip()
                if not line:
                    continue
                elif line.endswith(':'):
                    yield {'group': line}
                else:
                    yield parseIngredientLine(line, meaList, repFrac)

        def groupByAttribute(recipeList, attribute, alt='en'):
            groups = dict()
            for recipe in recipeList:
                if attribute == 'ingredients':
                    for ing in ingredientsForRecipe(recipe, alt):
                        updateSet_if(groups, ing, 'name', recipe)
                else:
                    updateSet_if(groups, recipe, attribute, recipe)
            # groups[undefinedKey].update(groups.pop('_undefined'))
            return groups.items()

        self.env.jinja_env.filters['sorted_images'] = sorted_images
        self.env.jinja_env.filters['title_image'] = title_image
        self.env.jinja_env.filters['rating'] = numFillWithText
        self.env.jinja_env.filters['replaceFractions'] = replaceFractions
        self.env.jinja_env.filters['enumIngredients'] = ingredientsForRecipe
        self.env.jinja_env.filters['replaceAtRefURLs'] = replace_atref_urls
        self.env.jinja_env.filters['groupByAttribute'] = groupByAttribute
        self.env.jinja_env.filters['groupSort'] = groupByDictSort
        self.env.jinja_env.globals['localize'] = localizeDic
