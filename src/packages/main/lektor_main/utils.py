# -*- coding: utf-8 -*-
from lektor.context import get_ctx
from jinja2.loaders import split_template_path  # lookup_template_path()
from markupsafe import Markup
import os
import unicodedata
from typing import TYPE_CHECKING, Dict, Union, Optional, Tuple
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


def cover_image(obj: 'Page') -> Optional['Image']:
    ''' Find cover image (cov.jpg or sorted first) and apply thumbnail. '''
    best = None
    for img in obj.attachments.images:  # type: Image
        if img['_id'].rsplit('.')[0] == 'cov':
            best = img
            break
        if not best or img['_id'] < best['_id']:
            best = img
    if best:
        ctx = get_ctx()
        if ctx:
            ctx.pad.db.track_record_dependency(best)
        return retina_thumbnail(best, w=200, h=150, mode='crop')[0]
    return None


def noUmlauts(text: str) -> str:
    ''' Remove umlauts and other unix-path incompatible characters. '''
    # try:
    #     data = unicode(text, 'utf-8')
    # except (TypeError, NameError):
    #     pass
    text = unicodedata.normalize('NFD', text)
    data = text.encode('ascii', 'ignore')
    text = data.decode('utf-8')
    return str(text)


def lookup_template_path(name: str, env: 'Environment') -> Optional[str]:
    ''' Find path to template with name. '''
    pieces = split_template_path(name)
    for base in env.jinja_env.loader.searchpath:
        path = os.path.join(base, *pieces)
        if os.path.isfile(path):
            return path
    return None


def retina_thumbnail(
    image: 'Image',
    w: Optional[int] = None,
    h: Optional[int] = None,
    *,
    mode: Optional[str] = None,
    maxwidth: int = 99999999,
    retina: int = 2,
) -> Tuple['Image', int, int]:
    ''' Constraint an image size with the least possible params. '''
    if mode:
        assert w and h, 'if using a crop mode, width and height are mandatory.'
    else:
        w = min(w, maxwidth * retina) if (w and w < image.width) else None
        h = h if (h and h < image.height) else None
        if w and h:
            if h >= w / image.width * image.height:
                h = None
            else:
                w = None
        if w:
            other = round(w / image.width * image.height)
        elif h:
            other = round(h / image.height * image.width)
        else:
            return image, image.width, image.height

    ew, eh = w or other, h or other
    w = (w * retina) if w and (w * retina < image.width) else None
    h = (h * retina) if h and (h * retina < image.height) else None
    if not w and not h:
        return image, ew, eh
    else:
        img = image.thumbnail(width=w, height=h, mode=mode, upscale=False)
        return img, ew, eh
