# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""Command-line validation for EvtGen ``.dec`` files."""

from __future__ import annotations

import argparse
import os
import re
import sys
import warnings
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .dec import DecFileParser


@dataclass(frozen=True)
class DiagnosticRule:
    """A selectable validation diagnostic."""

    code: str
    name: str
    description: str
    pattern: re.Pattern[str] | None = None


@dataclass(frozen=True)
class Diagnostic:
    """One validation finding for a decay file."""

    code: str
    name: str
    path: Path
    message: str
    line: int | None = None
    column: int | None = None
    source_line: str | None = None


DLP001 = DiagnosticRule(
    "DLP001",
    "parse-error",
    "The file could not be parsed by DecFileParser.",
)
DLW001 = DiagnosticRule(
    "DLW001",
    "duplicate-decay",
    "A particle has multiple Decay blocks; only the first is retained.",
    re.compile(
        r"The following particle\(s\) is\(are\) redefined in the input \.dec file "
        r"with 'Decay': .* All but the first occurrence will be discarded/removed "
        r"\.\.\."
    ),
)
DLW002 = DiagnosticRule(
    "DLW002",
    "missing-copydecay-source",
    "A CopyDecay statement references a missing Decay source.",
    re.compile(
        r"Corresponding 'Decay' statement for 'CopyDecay' statement\(s\).* "
        r"Skipping creation of these copied decay trees\."
    ),
)
DLW003 = DiagnosticRule(
    "DLW003",
    "duplicate-cdecay",
    "A particle is defined with both Decay and CDecay; CDecay is ignored.",
    re.compile(
        r"The following particles are defined in the input \.dec file with both "
        r"'Decay' and 'CDecay': .* The 'CDecay' definition\(s\) will be ignored "
        r"\.\.\."
    ),
)
DLW004 = DiagnosticRule(
    "DLW004",
    "missing-cdecay-source",
    "A CDecay statement has no corresponding Decay source.",
    re.compile(
        r"Corresponding 'Decay' statement for 'CDecay' statement\(s\).* "
        r"Skipping creation of these charge-conjugate decay trees\."
    ),
)
DLW005 = DiagnosticRule(
    "DLW005",
    "self-conjugate-cdecay",
    "A CDecay statement targets a self-conjugate particle.",
    re.compile(
        r"Found 'CDecay' statement for self-conjugate particle .* "
        r"Skipping creation of charge-conjugate decay Tree\."
    ),
)
DLW999 = DiagnosticRule(
    "DLW999",
    "parser-warning",
    "An otherwise unclassified warning was emitted by DecFileParser.",
)

DIAGNOSTIC_RULES = (DLP001, DLW001, DLW002, DLW003, DLW004, DLW005, DLW999)
_RULES_BY_CODE = {rule.code: rule for rule in DIAGNOSTIC_RULES}
_DEFAULT_MAX_DIAGNOSTICS = 100


class Style:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def color(self, text: str, code: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def fail(self, text: str) -> str:
        return self.color(text, "31")

    def ok(self, text: str) -> str:
        return self.color(text, "32")

    def bold(self, text: str) -> str:
        return self.color(text, "1")

    def muted(self, text: str) -> str:
        return self.color(text, "2")


def validate_files(
    paths: Iterable[Path],
    *,
    ignore: Iterable[str] = (),
    additional_decay_models: Iterable[str] = (),
) -> list[Diagnostic]:
    """Validate decay files and return non-ignored diagnostics."""

    ignored = tuple(ignore)
    diagnostics: list[Diagnostic] = []
    for path in _iter_decay_files(paths):
        diagnostics.extend(
            diagnostic
            for diagnostic in _validate_file(path, additional_decay_models)
            if not _is_ignored(diagnostic.code, ignored)
        )
    return diagnostics


def _iter_decay_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(
                item for item in path.rglob("*") if item.suffix.lower() == ".dec"
            )
        else:
            yield path


def _validate_file(
    path: Path,
    additional_decay_models: Iterable[str],
) -> list[Diagnostic]:
    caught_warnings: list[warnings.WarningMessage]
    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            parser = DecFileParser(path)
            parser.load_additional_decay_models(*additional_decay_models)
            parser.parse()
    except Exception as exc:
        return [_diagnostic_from_exception(path, exc)]

    return [_diagnostic_from_warning(path, warning) for warning in caught_warnings]


def _diagnostic_from_exception(path: Path, exc: Exception) -> Diagnostic:
    line = getattr(exc, "line", None)
    column = getattr(exc, "column", None)
    source_line = None
    if isinstance(line, int):
        try:
            source_line = path.read_text(encoding="utf_8").splitlines()[line - 1]
        except Exception:
            source_line = None

    return Diagnostic(
        code=DLP001.code,
        name=DLP001.name,
        path=path,
        message=f"{exc.__class__.__name__}: {str(exc).splitlines()[0]}",
        line=line if isinstance(line, int) else None,
        column=column if isinstance(column, int) else None,
        source_line=source_line,
    )


def _diagnostic_from_warning(
    path: Path,
    warning: warnings.WarningMessage,
) -> Diagnostic:
    message = _normalize_warning_message(warning)
    rule = next(
        (
            candidate
            for candidate in DIAGNOSTIC_RULES
            if candidate.pattern is not None and candidate.pattern.fullmatch(message)
        ),
        DLW999,
    )
    return Diagnostic(
        code=rule.code,
        name=rule.name,
        path=path,
        message=_compact_warning_message(rule, message),
    )


def _normalize_warning_message(warning: warnings.WarningMessage) -> str:
    return " ".join(str(warning.message).split())


def _compact_warning_message(rule: DiagnosticRule, message: str) -> str:
    if rule is DLW001:
        particles = _search_message(message, r"with 'Decay': (?P<particles>.*?)!")
        if particles is not None:
            return f"duplicate Decay block(s): {particles}; later definitions ignored"
    if rule is DLW002:
        particles = _search_message(message, r"not found: (?P<particles>.*?)\.")
        if particles is not None:
            return f"missing Decay source for CopyDecay: {particles}"
    if rule is DLW003:
        particles = _search_message(message, r"'CDecay': (?P<particles>.*?)!")
        if particles is not None:
            return f"both Decay and CDecay defined: {particles}; CDecay ignored"
    if rule is DLW004:
        particles = _search_message(message, r"not found: (?P<particles>.*?)\.")
        if particles is not None:
            return f"missing Decay source for CDecay: {particles}"
    if rule is DLW005:
        particle = _search_message(
            message,
            r"self-conjugate particle (?P<particles>.*?)\.",
        )
        if particle is not None:
            return f"CDecay targets self-conjugate particle: {particle}"
    return message


def _search_message(message: str, pattern: str) -> str | None:
    match = re.search(pattern, message)
    if match is None:
        return None
    return match.group("particles")


def _is_ignored(code: str, ignored: Sequence[str]) -> bool:
    return any(code == item or code.startswith(item) for item in ignored)


def _validate_ignore_codes(codes: Iterable[str]) -> list[str]:
    prefixes = {rule.code[:3] for rule in DIAGNOSTIC_RULES}
    valid_codes = set(_RULES_BY_CODE)
    invalid = [
        code for code in codes if code not in valid_codes and code not in prefixes
    ]
    if invalid:
        known = ", ".join(sorted(valid_codes | prefixes))
        msg = f"unknown diagnostic code(s): {', '.join(invalid)}. Known codes: {known}"
        raise SystemExit(msg)
    return list(codes)


def _use_color(color: str) -> bool:
    if color == "always":
        return True
    if color == "never":
        return False
    return sys.stderr.isatty() and "NO_COLOR" not in os.environ


def _print_diagnostics(
    diagnostics: list[Diagnostic],
    *,
    files: Sequence[Path],
    show_ok: bool,
    color: str,
    max_diagnostics: int,
) -> None:
    style = Style(_use_color(color))
    if diagnostics:
        shown_diagnostics = (
            diagnostics if max_diagnostics == 0 else diagnostics[:max_diagnostics]
        )
        sys.stderr.write(
            style.fail(
                style.bold(
                    f"DecayLanguage: {len(diagnostics)} diagnostic(s) in "
                    f"{len({diagnostic.path for diagnostic in diagnostics})} file(s)"
                )
            )
            + "\n"
        )
        for diagnostic in shown_diagnostics:
            sys.stderr.write(
                f"{_format_location(diagnostic)}: "
                f"{style.fail(diagnostic.code)} "
                f"{diagnostic.name}: {diagnostic.message}\n"
            )
            if diagnostic.line is not None and diagnostic.source_line is not None:
                sys.stderr.write(
                    style.muted(f"       {diagnostic.line}: {diagnostic.source_line}")
                    + "\n"
                )
                if diagnostic.column is not None:
                    pointer = " " * max(diagnostic.column - 1, 0) + "^"
                    sys.stderr.write(style.muted(f"          {pointer}") + "\n")
        hidden = len(diagnostics) - len(shown_diagnostics)
        if hidden:
            sys.stderr.write(
                style.muted(
                    f"... {hidden} additional diagnostic(s) hidden; "
                    "use --max-diagnostics=0 to show all"
                )
                + "\n"
            )
        stats = ", ".join(
            f"{code}={count}"
            for code, count in sorted(Counter(d.code for d in diagnostics).items())
        )
        sys.stderr.write(style.muted(f"summary: {stats}") + "\n")
        return

    if show_ok:
        sys.stderr.write(style.ok(f"DecayLanguage: {len(files)} file(s) passed") + "\n")


def _format_location(diagnostic: Diagnostic) -> str:
    parts = [_display_path(diagnostic.path)]
    if diagnostic.line is not None:
        parts.append(str(diagnostic.line))
        if diagnostic.column is not None:
            parts.append(str(diagnostic.column))
    return ":".join(parts)


def _display_path(path: Path) -> str:
    try:
        return os.path.relpath(path)
    except ValueError:
        return str(path)


def _print_rules() -> None:
    for rule in DIAGNOSTIC_RULES:
        sys.stdout.write(f"{rule.code} {rule.name}: {rule.description}\n")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate EvtGen decay files with decaylanguage.DecFileParser.",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="CODE",
        help=(
            "ignore a diagnostic code or code prefix, for example DLW004 or DLW; "
            "may be used more than once"
        ),
    )
    parser.add_argument(
        "--additional-decay-model",
        action="append",
        default=[],
        metavar="NAME",
        help="allow an experiment-specific EvtGen decay model name",
    )
    parser.add_argument(
        "--show-ok",
        action="store_true",
        help="print a message when all files pass",
    )
    parser.add_argument(
        "--max-diagnostics",
        type=int,
        default=_DEFAULT_MAX_DIAGNOSTICS,
        metavar="N",
        help=(
            "maximum diagnostics to print before summarising; "
            "use 0 to print all diagnostics"
        ),
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="control colored output",
    )
    parser.add_argument(
        "--list-diagnostics",
        action="store_true",
        help="list available diagnostic codes and exit",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        metavar="PATH",
        help="decay files or directories containing .dec/.DEC files",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.list_diagnostics:
        _print_rules()
        return 0
    if not args.files:
        raise SystemExit("at least one decay file must be provided")

    ignored = _validate_ignore_codes(args.ignore)
    if args.max_diagnostics < 0:
        raise SystemExit("--max-diagnostics must be non-negative")
    diagnostics = validate_files(
        args.files,
        ignore=ignored,
        additional_decay_models=args.additional_decay_model,
    )
    _print_diagnostics(
        diagnostics,
        files=args.files,
        show_ok=args.show_ok,
        color=args.color,
        max_diagnostics=args.max_diagnostics,
    )
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
