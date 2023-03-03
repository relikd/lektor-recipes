# -*- coding: utf-8 -*-
from lektor.reporter import reporter  # build, verbosity
from click import echo as c_echo, style as c_style  # type:ignore[attr-defined]
from contextlib import contextmanager
import time
from typing import TYPE_CHECKING, Any, Optional
if TYPE_CHECKING:
    from lektor.builder import Builder


class Log:
    class Style:
        @staticmethod
        def red(msg: str) -> str:
            return c_style(msg, fg='red', bold=True)  # type: ignore

    @staticmethod
    def verbosity() -> int:
        return reporter.verbosity  # type: ignore[attr-defined, no-any-return]

    @staticmethod
    def isVerbose() -> bool:
        return Log.verbosity() > 0

    @staticmethod
    def updated(msg: str) -> None:
        c_echo('{} {}'.format(c_style('U', fg='green'), msg))

    @staticmethod
    def error(msg: str) -> None:
        c_echo('{} {}'.format(c_style('E', fg='red'), msg))

    @staticmethod
    def generic(msg: str) -> None:
        c_echo(c_style(msg, fg='cyan'))

    @staticmethod
    def group(msg: str, builder: Optional['Builder'] = None) -> Any:
        if builder:
            return reporter.build(msg, builder)  # type: ignore[attr-defined]
        else:
            return _fallback_grouping(msg)


@contextmanager
def _fallback_grouping(msg: str) -> Any:
    start_time = time.time()
    Log.generic('Started {}'.format(msg))
    try:
        yield
    finally:
        Log.generic('Finished {} in {:.2f} sec'.format(
            msg, time.time() - start_time))
