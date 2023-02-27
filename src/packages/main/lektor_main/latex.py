# -*- coding: utf-8 -*-
from lektor.build_programs import BuildProgram  # subclass
from lektor.reporter import reporter  # build, verbosity
from lektor.sourceobj import VirtualSourceObject  # subclass
import click
import os
import re
import shutil  # which, copyfile, rmtree
import subprocess as shell  # run, DEVNULL
from weakref import ref
from typing import TYPE_CHECKING, List, Tuple, Generator
if TYPE_CHECKING:
    from lektor.builder import Artifact, Builder, BuildState
    from lektor.db import Record
    from lektor.environment import Environment
from .utils import lookup_template_path

VPATH = 'LatexPDF'
TEXER = 'lualatex'
PDF_OUT_DIR = 'out'

# ----------------------------------------------------
#  Sed re-format html as latex
# ----------------------------------------------------

HTML_TO_LATEX_RULES = [
    # character set translations for LaTex special chars
    (r'&gt.', r'>'),
    (r'&lt.', r'<'),
    (r'\\', r'\\backslash '),
    (r'{', r'\\{'),
    (r'}', r'\\}'),
    (r'%', r'\\%'),
    (r'\$', r'\\$'),
    (r'&', r'\\&'),
    (r'#', r'\\#'),
    (r'_', r'\\_'),
    (r'~', r'\\~'),
    (r'\^', r'\\^'),
    (r' ', r'~'),
    # Paragraph borders
    (r'<p>', r'\\par '),
    (r'</p>', r''),
    # Headings
    (r'<title>([^<]*)</title>', r'\\section*{\1}'),
    (r'<hn>', r'\\part{'),
    (r'</hn>', r'}'),
    (r'<h1>', r'\\section*{'),
    (r'</h[0-9]>', r'}'),
    (r'<h2>', r'\\subsection*{'),
    (r'<h3>', r'\\subsubsection*{'),
    (r'<h4>', r'\\paragraph*{'),
    (r'<h5>', r'\\paragraph*{'),
    (r'<h6>', r'\\subparagraph*{'),
    # UL is itemize
    (r'<ul>', r'\\begin{itemize}'),
    (r'</ul>', r'\\end{itemize}'),
    (r'<ol>', r'\\begin{enumerate}'),
    (r'</ol>', r'\\end{enumerate}'),
    (r'<li>', r'\\item '),
    (r'</li>', r''),
    # DL is description
    (r'<dl>', r'\\begin{description}'),
    (r'</dl>', r'\\end{description}'),
    # closing delimiter for DT is first < or end of line which ever comes first
    # (r'<dt>([^<]*)<', r'\\item[\1]<'),
    # (r'<dt>([^<]*)$', r'\\item[\1]'),
    # (r'<dd>', r''),
    # (r'<dt>', r'\\item['),
    # (r'<dd>', r']'),
    (r'<dt>([^<]*)</dt>', r'\\item[\1]'),
    (r'<dd>', r''),
    (r'</dd>', r''),
    # Italics
    (r'<it>([^<]*)</it>', r'{\\it \1}'),
    (r'<em>([^<]*)</em>', r'{\\it \1}'),
    (r'<b>([^<]*)</b>', r'{\\bf \1}'),
    (r'<strong>([^<]*)</strong>', r'{\\bf \1}'),
    # recipe specific
    (r'<a href="\.\./([^"/]*)/*">([^<]*)</a>', r'\\recipelink{\1}{\2}'),
    # Get rid of Anchors
    (r'<a href="(http[^"]*)">([^<]*)</a>', r'\\external{\1}{\2}'),
    (r'<a[^>]*>', r''),
    (r'</a>', r''),
    # quotes (replace after href)
    (r'(\s)"([^\s])', r'\1``\2'),
    (r'"', r"''"),
]


def __test__() -> None:
    TEST_DATA = '''
        Hello &gt; is &lt; for
        chars: " " & # _ ~ ^ % $ { }
        \\.

        <p>paragraph</p>

        <title>this is a title</title>
        <hn>this is a part</hn>
        <h1>this is a section</h1>
        <h2>this is a subsection</h2>
        <h3>this is a subsubsection</h3>
        <h4>this is a paragraph</h4>
        <h5>this is a paragraph</h5>
        <h6>this is a subparagraph</h6>

        <ul>
        <li>unordered one</li>
        <li>unordered two</li>
        </ul>

        <ol>
        <li>ordered one</li>
        <li>ordered two</li>
        </ol>

        <dl>
        <dt>definition title</dt>
        <dd>definition value</dd>
        </dl>

        <it>this is it</it>
        <em>this is em</em>
        <b>this is b</b>
        <strong>this is strong</strong>

        <a href="http://example.org">external anchor</a>
        <a href="../recipe">recipe anchor</a>
        <a href="language">other anchor</a>

        between "some" text

        <p class="name">test</p>
        '''
    print(Sed.apply(HTML_TO_LATEX_RULES, TEST_DATA))
    exit(0)


class Sed:
    def __init__(self, rules: List[Tuple[str, str]]) -> None:
        self._rules = [(re.compile(pattern), sub) for pattern, sub in rules]

    def replace(self, data: str) -> str:
        ret = data
        for regx, repl in self._rules:
            ret = regx.sub(repl, ret)
        return ret

    @staticmethod
    def apply(rules: List[Tuple[str, str]], data: str) -> str:
        ret = data
        for pattern, repl in rules:
            ret = re.sub(pattern, repl, ret)
        return ret


def html_to_tex(html: str) -> str:
    return Sed.apply(HTML_TO_LATEX_RULES, html)


def raw_text_to_tex(text: str) -> str:
    if not text:
        return ''
    text = text.replace('\\', '\\backslash ')
    for c in '}{%$&#_~^':
        text = text.replace(c, '\\' + c)
    return text.replace(' ', '~')


# ----------------------------------------------------
#  Helper methods
# ----------------------------------------------------

def _report_updated(msg: str) -> None:
    click.echo('{} {}'.format(click.style('U', fg='green'), msg))


def _report_error(msg: str) -> None:
    click.echo('{} {}'.format(click.style('E', fg='red'), msg))


# ----------------------------------------------------
#  PDF Build Program & Source
# ----------------------------------------------------

class TexSources:
    enabled: bool = False

    @staticmethod
    def registerBuilder(env: 'Environment', enabled: bool) -> None:
        TexSources.enabled = enabled
        env.add_build_program(PdfSource, PdfBuildProgram)

        @env.virtualpathresolver(VPATH)
        def resolvePDF(record: 'Record', pieces: List[str]) \
                -> PdfSource:
            return PdfSource(record)

    @staticmethod
    def add(builder: 'Builder', record: 'Record') -> None:
        if TexSources.enabled:
            try:
                refs = builder.__tex_files  # type: ignore[attr-defined]
            except AttributeError:
                refs = list()
                builder.__tex_files = refs  # type: ignore[attr-defined]
            refs.append(ref(record))

    @staticmethod
    def build(builder: 'Builder') -> None:
        if not TexSources.enabled:
            print(' * PDF Export: DISABLED')
            return
        try:
            sources = builder.__tex_files  # type: ignore[attr-defined]
            del builder.__tex_files  # type: ignore[attr-defined]
        except AttributeError:
            sources = []

        if sources:
            msg = f'PDF builder ({TEXER})'
            with reporter.build(msg, builder):  # type: ignore[attr-defined]
                for rec_ref in sources:
                    builder.build(PdfSource(rec_ref()))


# ----------------------------------------------------
#  PDF Build Program & Source
# ----------------------------------------------------

class PdfBuildProgram(BuildProgram):
    source: 'PdfSource'

    def produce_artifacts(self) -> None:
        self.declare_artifact(
            self.source.url_path,
            sources=list(self.source.iter_source_filenames()))

    def build_artifact(self, artifact: 'Artifact') -> None:
        self.source.build(self.build_state)


class PdfSource(VirtualSourceObject):
    @property
    def path(self) -> str:  # type: ignore[override]
        return self.record.path + '@' + VPATH  # type: ignore[no-any-return]

    @property
    def url_path(self) -> str:  # type: ignore[override]
        return self.record.url_path[:-4] + '.pdf'  # type:ignore[no-any-return]

    def iter_source_filenames(self) -> Generator[str, None, None]:
        template = lookup_template_path(self.record['_template'], self.pad.env)
        if template:
            yield template
        yield from self.record.iter_source_filenames()

    def build(self, build_state: 'BuildState') -> None:
        cmd_tex = shutil.which(TEXER)
        if not cmd_tex:
            _report_error(f'Skip PDF export. {TEXER} not found.')
            return

        # filename / path variables
        tex_src = build_state.get_destination_filename(self.record.url_path)
        pdf_dest = build_state.get_destination_filename(self.url_path)
        build_dir = build_state.builder.destination_path
        tex_root = os.path.join(build_state.env.root_path, '_tex-to-pdf')
        tmp_dir = os.path.join(tex_root, PDF_OUT_DIR)
        pdf_src = os.path.join(tmp_dir, os.path.basename(tex_src)[:-3] + 'pdf')

        # create temporary output directory
        os.makedirs(tmp_dir, exist_ok=True)

        # store build destination to resolve image paths in setup.tex
        with open(os.path.join(tmp_dir, 'builddir.tex'), 'w') as fp:
            fp.write('\\def\\buildDir{' + build_dir + '}')

        # run lualatex
        silent = reporter.verbosity == 0  # type: ignore[attr-defined]
        for i in range(1, 3):
            if i > 1:
                _report_updated(self.url_path.lstrip('/') + f' [{i}/2]')
            p = shell.run([
                cmd_tex,  # lualatex
                '--halt-on-error',
                '--output-directory', tmp_dir,
                tex_src  # tex file
            ],
                cwd=tex_root,  # change work dir so lualatex can find setup.tex
                stdout=shell.DEVNULL if silent else None,  # dont spam console
                input=b'')  # auto-reply to stdin on error

            if p.returncode == 0:
                shutil.copyfile(pdf_src, pdf_dest)
            else:
                _report_error(f'{TEXER} returned error code {p.returncode}')
                break

        # cleanup
        shutil.rmtree(tmp_dir, ignore_errors=True)
