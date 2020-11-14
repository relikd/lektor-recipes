# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin  # , get_plugin
import os
import subprocess

my_dir = os.path.dirname(os.path.realpath(__file__))
f_sed_a = os.path.join(my_dir, 'html2latex.sed')


def sed_repl_content(f_sed, content):
    with subprocess.Popen(('echo', content), stdout=subprocess.PIPE) as ps:
        o = subprocess.check_output(['sed', '-f', f_sed], stdin=ps.stdout)
        ps.wait()
        return o.decode('utf-8')


def html_to_tex(html):
    return sed_repl_content(f_sed_a, html)


def raw_text_to_tex(text):
    text = text.replace('\\', '\\backslash ').replace(' ', '~')
    for c in '}{%$&#_~^':
        if c in text:
            text = text.replace(c, '\\' + c)
    return text
    # return sed_repl_content(f_sed_b, text)


class HtmlToTex(Plugin):
    name = u'HTML to TEX converter'
    description = u'Will convert html formatted text to (la)tex format.'

    def on_before_build_all(self, builder, **extra):
        # export current build dir
        dest_file = my_dir
        for x in range(3):
            dest_file = os.path.dirname(dest_file)
        dest_file = os.path.join(dest_file, 'extras', 'pdf-export',
                                 'setup-builddir.tex')
        with open(dest_file, 'w') as f:
            f.write('\\def\\builddir{' + builder.destination_path + '}')

    def on_setup_env(self, **extra):
        self.env.jinja_env.filters['html_to_tex'] = html_to_tex
        self.env.jinja_env.filters['raw_text_to_tex'] = raw_text_to_tex
