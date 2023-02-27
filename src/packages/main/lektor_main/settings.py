# -*- coding: utf-8 -*-
from lektor.context import get_ctx
from typing import TYPE_CHECKING, List, Dict, Optional, NamedTuple
if TYPE_CHECKING:
    from lektor.db import Pad, Page, Record


class IngredientConfig(NamedTuple):
    units: List[str]
    frac_map: Dict[str, str]

    @staticmethod
    def of(record: 'Record') -> 'IngredientConfig':
        return Settings.ingredient_config(record.pad, record.alt)


class Settings:
    @staticmethod
    def load(pad: Optional['Pad'] = None, alt: Optional[str] = None) -> 'Page':
        if not pad:
            ctx = get_ctx()
            if not ctx:
                raise RuntimeError('Should never happen, missing context.')
            pad = ctx.pad
            if not alt:
                alt = ctx.source.alt
        assert(pad is not None)
        # used for dependency tracking
        return pad.get('/settings', alt=alt)  # type: ignore[no-any-return]

    @staticmethod
    def ingredient_config(pad: 'Pad', alt: str) -> IngredientConfig:
        set = Settings.load(pad, alt)
        mea = set['measures'].split()
        frac = {}
        if set['replace_frac']:
            it = iter(set['replace_frac_map'].split())
            frac = dict(zip(it, it))
        return IngredientConfig(mea, frac)

    # def ingredient_config_old(record: 'Record') -> IngredientConfig:
    #     plugin = record.pad.env.plugins['main']  # type: MainPlugin
    #     cfg = plugin.get_config()  # used for dependency tracking
    #     mea = cfg.get('measures.' + alt, '').split()
    #     frac = {}
    #     if cfg.get_bool('general.replace_frac'):
    #         frac = cfg.section_as_dict('replace_frac')
    #     return IngredientConfig(mea, frac)

    @staticmethod
    def duration_cluster() -> List[int]:
        # split() without args takes care of double spaces and trims each item
        splits = Settings.load()['duration_cluster'].replace(',', ' ').split()
        return [int(x) for x in splits]
