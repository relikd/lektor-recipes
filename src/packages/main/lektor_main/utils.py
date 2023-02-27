# -*- coding: utf-8 -*-
from jinja2.loaders import split_template_path  # lookup_template_name()
from markupsafe import Markup
import os
import unicodedata
from typing import TYPE_CHECKING, Dict, Union, Optional, List
if TYPE_CHECKING:
    from lektor.db import Page, Image
    from lektor.environment import Environment


def fillupText(
    numerator: Union[str, int, None],
    empty: str = u'☆',
    filled: str = u'★',
    total: int = 3
) -> str:
    '''
    Create a progress-bar-like string from int or number string.
    0 -> "☆☆☆", 1 -> "★☆☆", 2 -> "★★☆", 3 -> "★★★", etc.
    '''
    x = int(numerator) if numerator else 0
    return filled * x + empty * (total - x)


def replaceFractions(txt: str, repl_map: Dict[str, str]) -> str:
    ''' Replace `1 1/2 - 3/4` with `1½–¾`, etc. '''
    res = ' '
    for c in u'-–—':
        txt = txt.replace(c, ' – ')
    # NOTE: `split(' ')` can contain empty values but `split()` does not!
    for x in txt.split():
        if x == '–':
            res += x
        else:
            res += repl_map.get(x) or (x if res[-1] == '–' else ' ' + x)
    return res.lstrip(' ')


def replace_atref_urls(text: str, label: Optional[str] = None) -> str:
    ''' Replace `@../recipe/` with `<a href="../recipe/">label</a>` '''
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


def sorted_images(obj: 'Page', attr: str = 'record_label') -> List['Image']:
    return sorted(obj.attachments.images,
                  key=lambda x: getattr(x, attr))  # type:ignore[no-any-return]


def title_image(obj: 'Page', attr: str = 'record_label', small: bool = False) \
        -> Optional['Image']:
    imgs = sorted_images(obj, attr)
    img = imgs[0] if imgs else None
    if img and small:
        img = img.thumbnail(200, 150, mode='crop')
    return img


def noUmlauts(text: str) -> str:
    # try:
    #     data = unicode(text, 'utf-8')
    # except (TypeError, NameError):
    #     pass
    text = unicodedata.normalize('NFD', text)
    data = text.encode('ascii', 'ignore')
    text = data.decode('utf-8')
    return str(text)


def lookup_template_path(name: str, env: 'Environment') -> Optional[str]:
    pieces = split_template_path(name)
    for base in env.jinja_env.loader.searchpath:
        path = os.path.join(base, *pieces)
        if os.path.isfile(path):
            return path
    return None
