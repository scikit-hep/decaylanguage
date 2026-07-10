# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from decaylanguage.dec.dec import (
    DuplicateCDecayWarning,
    DuplicateDecayWarning,
    MissingCDecaySourceWarning,
    MissingCopyDecaySourceWarning,
    SelfConjugateCDecayWarning,
)
from decaylanguage.dec.validate import _diagnostic_from_warning, main, validate_files

DIR = Path(__file__).parent.resolve()


@pytest.mark.parametrize(
    ("category", "message", "code", "compact_message"),
    [
        (
            DuplicateDecayWarning,
            "The following particle(s) is(are) redefined in the input .dec file "
            "with 'Decay': D0! All but the first occurrence will be "
            "discarded/removed ...",
            "DLW001",
            "duplicate Decay block(s): D0; later definitions ignored",
        ),
        (
            MissingCopyDecaySourceWarning,
            "Corresponding 'Decay' statement for 'CopyDecay' statement(s) of "
            "following particle(s) not found: D0. Skipping creation of these "
            "copied decay trees.",
            "DLW002",
            "missing Decay source for CopyDecay: D0",
        ),
        (
            DuplicateCDecayWarning,
            "The following particles are defined in the input .dec file with both "
            "'Decay' and 'CDecay': D0! The 'CDecay' definition(s) will be ignored ...",
            "DLW003",
            "both Decay and CDecay defined: D0; CDecay ignored",
        ),
        (
            MissingCDecaySourceWarning,
            "Corresponding 'Decay' statement for 'CDecay' statement(s) of following "
            "particle(s) not found: D0. Skipping creation of these charge-conjugate "
            "decay trees.",
            "DLW004",
            "missing Decay source for CDecay: D0",
        ),
        (
            SelfConjugateCDecayWarning,
            "Found 'CDecay' statement for self-conjugate particle pi0. This is a bug! "
            "Skipping creation of charge-conjugate decay Tree.",
            "DLW005",
            "CDecay targets self-conjugate particle: pi0",
        ),
    ],
)
def test_warning_categories_map_to_diagnostics(
    category: type[Warning], message: str, code: str, compact_message: str
) -> None:
    warning = warnings.WarningMessage(category(message), category, "test.dec", 1)

    diagnostic = _diagnostic_from_warning(Path("test.dec"), warning)

    assert diagnostic.code == code
    assert diagnostic.message == compact_message


def test_validate_files_reports_duplicate_decay() -> None:
    diagnostics = validate_files([DIR / "../data/duplicate-decays.dec"])

    assert [diagnostic.code for diagnostic in diagnostics] == ["DLW001", "DLW003"]
    assert diagnostics[0].message.startswith("duplicate Decay block")


def test_validate_files_can_ignore_exact_code() -> None:
    diagnostics = validate_files(
        [DIR / "../data/duplicate-decays.dec"],
        ignore=["DLW001", "DLW003"],
    )

    assert diagnostics == []


def test_validate_files_can_ignore_code_prefix() -> None:
    diagnostics = validate_files(
        [DIR / "../data/duplicate-decays.dec"],
        ignore=["DLW"],
    )

    assert diagnostics == []


def test_validate_files_accepts_directories() -> None:
    diagnostics = validate_files(
        [DIR / "../data"],
        ignore=["DLW", "DLP"],
    )

    assert diagnostics == []


def test_validate_files_reports_parse_errors(tmp_path: Path) -> None:
    path = tmp_path / "broken.dec"
    path.write_text(
        """Decay pi0
1.0 gamma gamma PHSP;
""",
        encoding="utf_8",
    )

    diagnostics = validate_files([path])

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "DLP001"
    assert diagnostics[0].line is not None


def test_validate_files_reports_missing_files(tmp_path: Path) -> None:
    diagnostics = validate_files([tmp_path / "missing.dec"])

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "DLP001"
    assert diagnostics[0].message == "file does not exist or is not a regular file"


def test_main_returns_failure_for_diagnostics() -> None:
    assert main(["--color=never", str(DIR / "../data/duplicate-decays.dec")]) == 1


def test_main_limits_displayed_diagnostics(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(
            [
                "--color=never",
                "--max-diagnostics=1",
                str(DIR / "../data/duplicate-decays.dec"),
            ]
        )
        == 1
    )

    captured = capsys.readouterr()
    assert "additional diagnostic(s) hidden" in captured.err
    assert "summary: DLW001=1, DLW003=1" in captured.err


def test_main_returns_success_for_ignored_diagnostics() -> None:
    assert (
        main(
            [
                "--color=never",
                "--ignore=DLW001",
                "--ignore=DLW003",
                str(DIR / "../data/duplicate-decays.dec"),
            ]
        )
        == 0
    )


def test_main_rejects_unknown_ignore_code() -> None:
    with pytest.raises(SystemExit, match="unknown diagnostic code"):
        main(["--ignore=NOPE", str(DIR / "../data/duplicate-decays.dec")])
