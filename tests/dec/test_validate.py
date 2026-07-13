# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

import decaylanguage.dec.validate as validate_module
from decaylanguage.dec.dec import (
    DuplicateCDecayWarning,
    DuplicateDecayWarning,
    MissingCDecaySourceWarning,
    MissingCopyDecaySourceWarning,
    SelfConjugateCDecayWarning,
)
from decaylanguage.dec.validate import (
    Diagnostic,
    _diagnostic_from_exception,
    _diagnostic_from_warning,
    _print_diagnostics,
    main,
    validate_files,
)

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
        (
            UserWarning,
            "An unclassified parser warning.",
            "DLW999",
            "An unclassified parser warning.",
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


def test_known_warning_with_unrecognized_message_is_not_rewritten() -> None:
    message = "A future version of this warning with different wording."
    warning = warnings.WarningMessage(
        DuplicateDecayWarning(message), DuplicateDecayWarning, "test.dec", 1
    )

    diagnostic = _diagnostic_from_warning(Path("test.dec"), warning)

    assert diagnostic.code == "DLW001"
    assert diagnostic.message == message


def test_validate_files_reports_duplicate_decay() -> None:
    diagnostics = validate_files([DIR / "../data/duplicate-decays.dec"])

    assert [diagnostic.code for diagnostic in diagnostics] == ["DLW001", "DLW003"]
    assert diagnostics[0].message.startswith("duplicate Decay block")


def test_validate_files_reports_self_conjugate_cdecay(tmp_path: Path) -> None:
    path = tmp_path / "self-conjugate-cdecay.dec"
    path.write_text(
        """Alias MyPi0 pi0
ChargeConj MyPi0 pi0
Decay pi0
1.0 gamma gamma PHSP;
Enddecay
CDecay MyPi0
End
""",
        encoding="utf_8",
    )

    diagnostics = validate_files([path])

    assert [diagnostic.code for diagnostic in diagnostics] == ["DLW005"]
    assert diagnostics[0].message == "CDecay targets self-conjugate particle: pi0"


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


def test_validate_files_reuses_additional_decay_model_generator() -> None:
    path = DIR / "../data/test_custom_decay_model.dec"
    models = (model for model in ("CUSTOM_MODEL1", "CUSTOM_MODEL2"))

    diagnostics = validate_files(
        [path, path],
        additional_decay_models=models,
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


@pytest.mark.parametrize("message", ["", "\n \t"])
def test_diagnostic_from_exception_accepts_empty_message(message: str) -> None:
    diagnostic = _diagnostic_from_exception(Path("broken.dec"), AssertionError(message))

    assert diagnostic.message == "AssertionError"


def test_validate_files_reports_missing_files(tmp_path: Path) -> None:
    diagnostics = validate_files([tmp_path / "missing.dec"])

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "DLP001"
    assert diagnostics[0].message == "file does not exist or is not a regular file"


def test_main_returns_failure_for_diagnostics() -> None:
    assert main(["--color=never", str(DIR / "../data/duplicate-decays.dec")]) == 1


def test_main_can_force_colored_output(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--color=always", str(DIR / "../data/duplicate-decays.dec")]) == 1

    assert "\033[" in capsys.readouterr().err


def test_automatic_color_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(
        validate_module.sys, "stderr", SimpleNamespace(isatty=lambda: True)
    )

    assert validate_module._use_color("auto") is True

    monkeypatch.setenv("NO_COLOR", "1")
    assert validate_module._use_color("auto") is False


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


def test_print_diagnostics_aligns_column_pointer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    diagnostic = Diagnostic(
        code="DLP001",
        name="parse-error",
        path=Path("broken.dec"),
        message="bad input",
        line=12,
        column=3,
        source_line="abcdef",
    )

    _print_diagnostics(
        [diagnostic],
        files=[diagnostic.path],
        show_ok=False,
        color="never",
        max_diagnostics=100,
    )

    lines = capsys.readouterr().err.splitlines()
    source_line = next(line for line in lines if line.endswith("abcdef"))
    pointer_line = next(line for line in lines if line.endswith("^"))
    assert pointer_line.index("^") == source_line.index("c")


def test_print_diagnostics_aligns_column_pointer_after_tab(
    capsys: pytest.CaptureFixture[str],
) -> None:
    diagnostic = Diagnostic(
        code="DLP001",
        name="parse-error",
        path=Path("broken.dec"),
        message="bad input",
        line=1,
        column=3,
        source_line="a\tb",
    )

    _print_diagnostics(
        [diagnostic],
        files=[diagnostic.path],
        show_ok=False,
        color="never",
        max_diagnostics=100,
    )

    lines = capsys.readouterr().err.splitlines()
    source_line = next(line for line in lines if line.endswith("b"))
    pointer_line = next(line for line in lines if line.endswith("^"))
    assert "\t" not in source_line
    assert pointer_line.index("^") == source_line.index("b")


@pytest.mark.parametrize("number_of_files", [0, 2])
def test_main_show_ok_counts_expanded_directory_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    number_of_files: int,
) -> None:
    for index in range(number_of_files):
        (tmp_path / f"valid-{index}.dec").write_text("End\n", encoding="utf_8")

    assert main(["--color=never", "--show-ok", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert f"DecayLanguage: {number_of_files} file(s) passed" in captured.err


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


def test_main_lists_diagnostics(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--list-diagnostics"]) == 0

    output = capsys.readouterr().out
    assert "DLP001 parse-error" in output
    assert "DLW999 parser-warning" in output


def test_main_rejects_missing_files_argument() -> None:
    with pytest.raises(SystemExit, match="at least one decay file"):
        main([])


def test_main_rejects_negative_max_diagnostics() -> None:
    with pytest.raises(SystemExit, match="must be non-negative"):
        main(["--max-diagnostics=-1", "example.dec"])


def test_display_path_handles_cross_drive_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = Path("D:/decays/example.dec")

    def raise_value_error(_: Path) -> str:
        raise ValueError

    monkeypatch.setattr(validate_module.os.path, "relpath", raise_value_error)

    assert validate_module._display_path(path) == str(path)
