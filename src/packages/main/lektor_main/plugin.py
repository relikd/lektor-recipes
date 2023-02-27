# -*- coding: utf-8 -*-
from lektor.databags import Databags
from lektor.db import Page  # isinstance
from lektor.pluginsystem import Plugin
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Dict, Tuple, Set, Iterator
if TYPE_CHECKING:
    from lektor.builder import Builder
    from lektor.db import Record

from .durationcluster import (
    int_to_cluster, cluster_as_str, human_readable_duration
)
from .ingredients import IngredientsListType
from .latex import TexSources, raw_text_to_tex, html_to_tex
from .settings import Settings
from .utils import (
    fillupText, replace_atref_urls, sorted_images, title_image, noUmlauts
)


class MainPlugin(Plugin):
    name = 'Main Plugin'
    description = 'Code snippets for recipe lekture.'

    def on_setup_env(self, **extra: Any) -> None:
        # Register custom field type
        self.env.add_type(IngredientsListType)
        # Add jinja filter & globals
        self.env.jinja_env.filters.update({
            'asDuration': self.as_duration,  # needs alt
            'asRating': self.as_rating,
            'replaceAtRefURLs': replace_atref_urls,
            'performGroupBy': self.performGroupBy,

            'sorted_images': sorted_images,
            'title_image': title_image,

            'latexStr': raw_text_to_tex,
            'latexHtml': html_to_tex,
        })
        # self.env.jinja_env.globals.update({
        #     'str': str,
        #     'dir': dir,
        #     'type': type,
        #     'len': len,
        #     'now': datetime.now
        # })
        # Latex -> PDF Build program
        make_pdf = extra.get('extra_flags', {}).get('ENABLE_PDF_EXPORT', False)
        TexSources.registerBuilder(self.env, enabled=make_pdf)

    def on_after_build(
        self, builder: 'Builder', source: 'Record', **extra: Any
    ) -> None:
        if not isinstance(source, Page):
            return  # ignore Asset, Directory, etc.
        if source.path.endswith('.tex'):  # type: ignore[attr-defined]
            TexSources.add(builder, source)

    def on_after_build_all(self, builder: 'Builder', **extra: Any) -> None:
        # must run after all sources are built
        # or else latex fails because it cannot find referenced images
        TexSources.build(builder)

    ##############
    #  Duration  #
    ##############

    def _i18n(self, alt: str, key: str) -> Dict[str, str]:
        # used for dependency tracking
        return Databags(self.env).lookup(  # type: ignore[no-any-return]
            f'i18n+{alt}.{key}')

    def as_duration(self, time: int, alt: str) -> str:
        return human_readable_duration(time, self._i18n(alt, 'duration'))

    def as_rating(self, x: str) -> str:
        return fillupText(x, u'☆', u'★', 3)

    #####################
    #  Group by filter  #
    #####################

    def performGroupBy(
        self,
        recipes: List['Page'],
        attribute: str,
        reverse: bool = False,
        alt: str = 'en',
    ) -> Iterator[Tuple[str, Set['Page']]]:
        # Pre-Processing
        if attribute == 'time':
            time_clusters = Settings.duration_cluster()
            time_translations = self._i18n(alt, 'duration')
        elif attribute == 'difficulty':
            difficulty_translations = self._i18n(alt, 'difficulty')

        # Grouping
        ret = dict()  # type: Dict[Any, Set[Page]]
        for recipe in recipes:
            try:
                data = recipe[attribute] or None
            except KeyError:
                continue
            if attribute == 'time':
                data = [int_to_cluster(data, time_clusters)]
            elif attribute == 'ingredients' and data:
                data = [x.name for x in data or [] if x.isIngredient]
            else:
                data = [data]
            for x in data:
                if x not in ret:
                    ret[x] = set()
                ret[x].add(recipe)

        # Sorting
        reverse = bool(reverse)
        if attribute == 'difficulty':
            order = ['easy', 'medium', 'hard']
            none_diff = -1 if reverse else 99

            def _fn(x: Tuple) -> Any:
                return order.index(x[0]) if x[0] in order else none_diff
        elif attribute == 'ingredients':  # sort by: str
            none_ingr = 'aaaa' if reverse else 'zzzz'

            def _fn(x: Tuple) -> Any:
                return noUmlauts(x[0]).lower() if x[0] else none_ingr
        else:  # sort by: int
            none_int = 0 if reverse else 999999999

            def _fn(x: Tuple) -> Any:
                return int(x[0]) if x[0] else none_int

        result = sorted(ret.items(), reverse=bool(reverse), key=_fn)

        # Post-Processing
        for group, recipe_list in result:
            if attribute == 'time':
                group = cluster_as_str(group, time_clusters, time_translations)
            elif attribute == 'rating':
                group = self.as_rating(group)
            elif attribute == 'difficulty':
                group = difficulty_translations.get(group)

            yield group, recipe_list
