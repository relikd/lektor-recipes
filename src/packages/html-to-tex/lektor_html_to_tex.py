# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin  # , get_plugin
import mistune
import os
import time
import subprocess as shell
import lektor_helper as helper
import lektor_time_duration as timedur

my_dir = os.path.dirname(os.path.realpath(__file__))
f_sed_a = os.path.join(my_dir, 'html2latex.sed')


def sed_repl_tex(f_sed, content):
    with shell.Popen(('echo', content), stdout=shell.PIPE) as ps:
        o = shell.check_output(['sed', '-f', f_sed], stdin=ps.stdout)
        ps.wait()
        return o.decode('utf-8')


def html_to_tex(html):
    return sed_repl_tex(f_sed_a, html)


def raw_text_to_tex(text):
    text = text.replace('\\', '\\backslash ').replace(' ', '~')
    for c in '}{%$&#_~^':
        if c in text:
            text = text.replace(c, '\\' + c)
    return text
    # return sed_repl_tex(f_sed_b, text)


class RecipeToTex(object):
    def __init__(self, enumerator):
        super(RecipeToTex, self).__init__()
        bases = tuple([]) + (mistune.Renderer,)
        renderer_cls = type('renderer_cls', bases, {})
        renderer = renderer_cls(escape=False)
        self.mdparser = mistune.Markdown(renderer, escape=False)
        self.enumerator = enumerator

    def make(self, recipe, alt):
        ingredients = ''
        for x in self.enumerator(recipe, alt, mode='tex'):
            ingredients += '\n' + self.process_ingredient(x, alt)
        ingredients = ingredients[1:] or '\\item '
        self.mdparser.renderer.record = recipe
        instructions_html = self.mdparser(recipe['directions'].source)
        instructions = sed_repl_tex(f_sed_a, instructions_html)
        return self.process_recipe(recipe, alt, ingredients, instructions)
        pass

    def process_recipe(self, recipe, alt, ingredients, instructions):
        img = helper.title_image(recipe)
        if img:
            img = img.path[:-4] + '@200x150_crop' + img.path[-4:]
        duration = recipe['time']
        host = recipe['source'].host
        time = timedur.to_duration(duration, alt) if duration else ''
        srcUrl = raw_text_to_tex(str(recipe['source'])) or ''
        srcHost = raw_text_to_tex(host) if host else ''
        return f'''
\\newrecipe{{{recipe['_slug']}}}{{{raw_text_to_tex(recipe['name'])}}}
\\meta{{{time}}}{{{recipe['yield'] or ''}}}
\\footer{{{srcUrl}}}{{{srcHost}}}

\\begin{{ingredients}}{{{img or ''}}}
{ingredients}
\\end{{ingredients}}

{instructions}
'''

    def process_ingredient(self, ing, alt):
        grp = ing.get('group')
        if grp:
            return f'\\ingGroup{{{grp}}}'

        ret = ''
        val = ing['value']
        meas = ing['measure']
        note = ing['note']
        ret += '\\item'
        if val or meas:
            sep = '~' if val and meas else ''
            ret += '[{}{}{}]'.format(val or '', sep, meas or '')
        ret += f' \\ingName{{{ ing["name"] }}}'  # keep space in front
        if note:
            ret += '\\ingDetail{'
            for prt in note.split():
                if prt.startswith('@../'):
                    ret += f' \\pagelink{{{ prt[4:].rstrip("/") }}}'
                else:
                    ret += ' ' + prt
            ret += '}'
        return ret


class HtmlToTex(Plugin):
    name = u'HTML to TEX converter'
    description = u'Will convert html formatted text to (la)tex format.'

    def on_after_prune(self, builder, **extra):
        maketex = bool(builder.extra_flags.get('ENABLE_PDF_EXPORT'))
        print('PDF Export: ' + ('ENABLED' if maketex else 'DISABLED'))
        if not maketex:
            return

        dest_dir = my_dir
        for x in range(3):
            dest_dir = os.path.dirname(dest_dir)
        dest_dir = os.path.join(dest_dir, 'extras', 'pdf-export')

        start_time = time.time()
        print('PDF Export: generate tex files')
        with open(os.path.join(dest_dir, 'dyn-builddir.tex'), 'w') as f:
            # Export current build dir (for image search)
            f.write('\\def\\builddir{' + builder.destination_path + '}')
        parser = RecipeToTex(self.env.jinja_env.filters['enumIngredients'])
        for alt in self.env.load_config().list_alternatives():
            tex = ''
            for recipe in builder.pad.get('/recipes', alt=alt).children:
                tex += parser.make(recipe, alt)
            fname = os.path.join(dest_dir, f'dyn-recipes-{alt}.tex')
            with open(fname, 'w') as f:
                f.write(tex)
        print('PDF Export: done in %.2f sec' % (time.time() - start_time))

    def on_setup_env(self, **extra):
        self.env.jinja_env.filters['raw_text_to_tex'] = raw_text_to_tex
