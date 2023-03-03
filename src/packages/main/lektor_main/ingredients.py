# -*- coding: utf-8 -*-
from lektor.types import Type
from typing import TYPE_CHECKING, List, Optional, Any, Iterator, Tuple
if TYPE_CHECKING:
    from lektor.builder import Builder
    from lektor.db import Record
    from lektor.types.base import RawValue
from .settings import IngredientConfig
from .utils import replaceFractions


class IngredientEntry:
    @property
    def isGroup(self) -> bool:
        return False

    @property
    def isIngredient(self) -> bool:
        return False


class IngredientGroup(IngredientEntry):
    @property
    def isGroup(self) -> bool:
        return True

    def __init__(self, line: str) -> None:
        self.name = line

    def __repr__(self) -> str:
        return '<IngredientGroup name="{}">'.format(self.name)


class Ingredient(IngredientEntry):
    @property
    def isIngredient(self) -> bool:
        return True

    def __init__(self, line: str, conf: IngredientConfig) -> None:
        idx = Ingredient.split_raw(line)
        # parse quantity
        self.quantity = line[:idx[0]]
        if conf.frac_map:
            self.quantity = replaceFractions(self.quantity, conf.frac_map)
        # parse unit
        unit = line[idx[0]:idx[1]].lstrip()
        if unit in conf.units:
            name = line[idx[1]:].lstrip()
        else:
            unit, name = '', line[idx[0]:].lstrip()
        self.unit = unit
        # parse ingredient name + note
        note = ''
        name_note = name.split(',', 1)
        if len(name_note) > 1:
            name, note = [x.strip() for x in name_note]
        self.name = name
        self.note = note

    @staticmethod
    def split_raw(line: str) -> List[int]:
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

    def __repr__(self) -> str:
        return '<Ingredient "{}" qty="{}" unit="{}" note="{}">'.format(
            self.name, self.quantity, self.unit, self.note)


class IngredientsDescriptor:
    def __init__(self, raw: Optional[str]) -> None:
        self.raw = raw

    def parse(self, raw: str, record: 'Record') -> List[IngredientEntry]:
        conf = IngredientConfig.of(record)
        ret = []  # type: List[IngredientEntry]
        for line in raw.splitlines(True):  # we need to strip anyway
            line = line.strip()
            if line:
                if line.endswith(':'):
                    ret.append(IngredientGroup(line.rstrip(':')))
                else:
                    ret.append(Ingredient(line, conf))
        return ret

    def __get__(self, record: 'Record', _: Any = None) -> Any:
        if record is None:
            return self
        if not self.raw:
            return []
        return self.parse(self.raw, record)


class IngredientsListType(Type):
    widget = 'multiline-text'

    def value_from_raw(self, raw: 'RawValue') -> IngredientsDescriptor:
        return IngredientsDescriptor(raw.value or None)


##############################
#  Check cross-recipe links  #
##############################

def _detect_atref_urls(recipe: 'Record') -> Iterator[str]:
    ''' Internal method to iterate over recipe-links in ingredient notes. '''
    for ing in recipe['ingredients']:
        if ing.isIngredient and '@' in ing.note:
            for part in ing.note.split():
                if part.startswith('@../'):
                    yield part[4:].rstrip('/')


def check_dead_links(builder: 'Builder') -> Iterator[Tuple['Record', str]]:
    '''
    Iterate over all recipes and all ingredients notes.
    If a note contains a recipe link, check if the link is a valid target.
    If not, print to log but continue building (soft error).

    returns: [recipe, ref-link]
     '''
    for alt in builder.pad.config.iter_alternatives():
        # funny enough, .query('/recipes') does not populate ingredients
        all_recipes = builder.pad.get('/recipes', alt=alt).children
        all_ids = set(x['_slug'] for x in all_recipes)
        for recipe in all_recipes:
            for ref in _detect_atref_urls(recipe):
                if ref not in all_ids:
                    yield recipe, f'@../{ref}/'
