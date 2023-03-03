# -*- coding: utf-8 -*-
from lektor.types import Type
from typing import TYPE_CHECKING, List, Optional, Any
if TYPE_CHECKING:
    from lektor.db import Record
    from lektor.types.base import RawValue
from .utils import replaceFractions
from .settings import IngredientConfig


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
