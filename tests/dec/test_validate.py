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
    DecayAndCDecayWarning,
    DecFileParser,
    DuplicateCDecayWarning,
    DuplicateDecayWarning,
    MisconfiguredAliasWarning,
    MisconfiguredChargeConjWarning,
    MissingCDecaySourceWarning,
    MissingCopyDecaySourceWarning,
    SelfChargeConjWarning,
    SelfConjugateCDecayWarning,
    UnknownDecayModelError,
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
            (
                "The following particle(s) is(are) redefined in the input .dec file "
                "with 'Decay': D0! All but the first occurrence(s) will be "
                "discarded/removed ..."
            ),
            "DLW001",
            "duplicate Decay block(s): D0; later definitions ignored",
        ),
        (
            MissingCopyDecaySourceWarning,
            (
                "Corresponding 'Decay' statement for 'CopyDecay' statement(s) of "
                "following particle(s) not found: D0. Skipping creation of these "
                "copied decay trees."
            ),
            "DLW006",
            "missing Decay source for CopyDecay: D0",
        ),
        (
            DecayAndCDecayWarning,
            (
                "The following particles are defined in the input .dec file with both "
                "'Decay' and 'CDecay': D0! The 'CDecay' definition(s) will be ignored ..."
            ),
            "DLW003",
            "both Decay and CDecay defined: D0; CDecay ignored",
        ),
        (
            DuplicateCDecayWarning,
            (
                "The following particle(s) is(are) redefined in the input .dec file "
                "with 'CDecay': D0! All but the first occurrence(s) will be "
                "discarded/removed ..."
            ),
            "DLW002",
            "duplicate CDecay statement(s): D0; later statements ignored",
        ),
        (
            MissingCDecaySourceWarning,
            (
                "Corresponding 'Decay' statement for 'CDecay' statement(s) of following "
                "particle(s) not found: D0. Skipping creation of these charge-conjugate "
                "decay trees."
            ),
            "DLW004",
            "missing Decay source for CDecay: D0",
        ),
        (
            SelfConjugateCDecayWarning,
            (
                "Found 'CDecay' statement for self-conjugate particle pi0. This is a bug! "
                "Skipping creation of charge-conjugate decay Tree."
            ),
            "DLW005",
            "CDecay targets self-conjugate particle: pi0",
        ),
        (
            MisconfiguredAliasWarning,
            (
                "Found 'Alias' misleading/misconfigured statements for the following alias names: pi0! "
                "Continuing but be warned of possible side effects ..."
            ),
            "DLW010",
            "Alias statement is misleading/misconfigured: pi0",
        ),
        (
            MisconfiguredChargeConjWarning,
            (
                "Found 'ChargeConj' misleading/misconfigured statements for the following particle names: pi0! "
                "Continuing but be warned of possible side effects ..."
            ),
            "DLW011",
            "ChargeConj statement is misleading/misconfigured: pi0",
        ),
        (
            SelfChargeConjWarning,
            (
                "Found 'ChargeConj' statements for the following non-alias "
                "self-conjugate particles: pi0! "
                "The 'ChargeConj' definition(s) will be ignored ..."
            ),
            "DLW012",
            "ChargeConj targets non-alias self-conjugate particles: pi0",
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

    assert [diagnostic.code for diagnostic in diagnostics] == ["DLW003", "DLW001"]
    assert diagnostics[0].message.startswith("both Decay and CDecay defined")


def test_validate_files_reports_self_conjugate_cdecay(tmp_path: Path) -> None:
    """
    This file is for testing purposes only, the mismatches are awkward/wrong.
    In short, such a decay file does not really make sense the way it configures things.
    """
    path = tmp_path / "self-conjugate-cdecay.dec"
    path.write_text(
        """
Alias MyPi0 pi0
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

    assert [diagnostic.code for diagnostic in diagnostics] == [
        "DLW011",
        "DLW005",
    ]
    assert (
        diagnostics[0].message
        == "ChargeConj statement is misleading/misconfigured: MyPi0"
    )


def test_validate_files_reports_duplicate_cdecay(tmp_path: Path) -> None:
    path = tmp_path / "duplicate-cdecay.dec"
    path.write_text(
        """Decay D0
1.0 K- pi+ PHSP;
Enddecay
CDecay anti-D0
CDecay anti-D0
End
""",
        encoding="utf_8",
    )

    diagnostics = validate_files([path])

    assert [diagnostic.code for diagnostic in diagnostics] == ["DLW002"]
    assert diagnostics[0].message == (
        "duplicate CDecay statement(s): anti-D0; later statements ignored"
    )


@pytest.mark.parametrize(
    ("decay_file", "codes"),
    [
        (
            """Decay D0
1.0 K- pi+ PHSP;
Enddecay
Decay anti-D0
1.0 K+ pi- PHSP;
Enddecay
CDecay anti-D0
CDecay anti-D0
End
""",
            ["DLW002", "DLW003"],
        ),
        (
            """Decay D0
1.0 K- pi+ PHSP;
Enddecay
CDecay B0
CDecay B0
End
""",
            ["DLW002", "DLW004"],
        ),
    ],
)
def test_duplicate_cdecay_is_independent_of_other_cdecay_diagnostics(
    tmp_path: Path, decay_file: str, codes: list[str]
) -> None:
    path = tmp_path / "combined-cdecay-errors.dec"
    path.write_text(decay_file, encoding="utf_8")

    diagnostics = validate_files([path])

    assert [diagnostic.code for diagnostic in diagnostics] == codes


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


def test_unknown_model_diagnostic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "unknown-model.dec"
    source_line = "1.0 gamma gamma UNKNOWN_MODEL;"
    path.write_text(f"Decay pi0\n{source_line}\nEnddecay\nEnd\n", encoding="utf_8")

    diagnostics = validate_files([path])

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert (diagnostic.code, diagnostic.name) == ("DLP001", "parse-error")
    assert (diagnostic.line, diagnostic.column) == (2, 17)
    assert diagnostic.source_line == source_line
    assert "Unknown decay model or undefined ModelAlias 'UNKNOWN_MODEL'" in (
        diagnostic.message
    )

    assert main(["--color=never", str(path)]) == 1
    output = capsys.readouterr().err
    assert "unknown-model.dec:2:17: DLP001 parse-error" in output
    assert "VisitError" not in output
    assert "--additional-decay-model=UNKNOWN_MODEL" in output
    assert "src/decaylanguage/dec/enums.py" in output
    lines = output.splitlines()
    rendered_source = next(line for line in lines if source_line in line)
    pointer = next(line for line in lines if line.endswith("^"))
    assert pointer.index("^") == rendered_source.index("UNKNOWN_MODEL")

    assert main(["--additional-decay-model=UNKNOWN_MODEL", str(path)]) == 0
    assert capsys.readouterr().err == ""


def test_model_diagnostic_preserves_intermediate_end_location(tmp_path: Path) -> None:
    path = tmp_path / "intermediate-end.dec"
    source = "1.0 gamma gamma XYZ;"
    path.write_text(f"End\nDecay pi0\n{source}\nEnddecay\nEnd\n", encoding="utf_8")
    diagnostic = validate_files([path])[0]
    assert (diagnostic.line, diagnostic.column) == (3, 17)
    assert diagnostic.source_line == source


@pytest.mark.parametrize("used", [False, True])
def test_validator_rejects_unknown_model_alias_target(
    tmp_path: Path, used: bool
) -> None:
    path = tmp_path / "unknown-alias-target.dec"
    content = "ModelAlias A XYZ 1 2;\n"
    if used:
        content += "Decay pi0\n1.0 gamma gamma A;\nEnddecay\n"
    path.write_text(content, encoding="utf_8")
    diagnostic = validate_files([path])[0]
    assert diagnostic.code == "DLP001"
    assert "'XYZ'" in diagnostic.message
    assert (diagnostic.line, diagnostic.column) == (1, 14)


def test_ambiguous_model_diagnostic_does_not_suggest_registering_parameter(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ambiguous-model.dec"
    path.write_text("Decay pi0\n1.0 gamma gamma XYZ 1 2;\nEnddecay\n", encoding="utf_8")
    diagnostic = validate_files([path])[0]
    assert "Cannot identify the decay model" in diagnostic.message
    assert "--additional-decay-model=2" not in diagnostic.message
    assert (diagnostic.line, diagnostic.column) == (2, 17)
    assert validate_files([path], additional_decay_models=["XYZ"]) == []


def test_exception_diagnostic_uses_originating_file(tmp_path: Path) -> None:
    first = tmp_path / "first.dec"
    second = tmp_path / "second.dec"
    first.write_text("End\n", encoding="utf_8")
    second.write_text("Decay pi0\n1.0 gamma gamma XYZ;\nEnddecay\n", encoding="utf_8")
    with pytest.raises(UnknownDecayModelError) as caught:
        DecFileParser(first, second).parse()
    diagnostic = _diagnostic_from_exception(first, caught.value)
    assert diagnostic.path == second
    assert diagnostic.line == 2
    assert diagnostic.source_line == "1.0 gamma gamma XYZ;"


@pytest.mark.parametrize("message", ["", "\n \t"])
def test_diagnostic_from_exception_accepts_empty_message(message: str) -> None:
    diagnostic = _diagnostic_from_exception(Path("broken.dec"), AssertionError(message))

    assert diagnostic.message == "AssertionError"


def test_validate_files_reports_missing_files(tmp_path: Path) -> None:
    diagnostics = validate_files([tmp_path / "missing.dec"])

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "DLP001"
    assert diagnostics[0].message == "file does not exist or is not a regular file"


def test_main_returns_failure_for_diagnostics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--color=never", str(DIR / "../data/duplicate-decays.dec")]) == 1

    assert "\033[" not in capsys.readouterr().err


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
