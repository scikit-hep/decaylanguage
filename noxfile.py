from __future__ import annotations

from pathlib import Path

import nox

nox.options.sessions = ["lint", "pylint", "tests"]

PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]

nox.needs_version = ">=2024.4.15"
nox.options.default_venv_backend = "uv|virtualenv"


@nox.session
def lint(session):
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def pylint(session: nox.Session) -> None:
    """
    Run pylint.
    """

    session.install("pylint")
    session.install("-e.[dev]")
    session.run("pylint", "src", *session.posargs)


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    session.install("-y.[test]")
    session.run("pytest", *session.posargs)


@nox.session
def build(session):
    """
    Build an SDist and wheel.
    """

    session.install("build", "twine", "check-wheel-contents")
    session.run("python", "-m", "build")
    session.run("twine", "check", "--strict", "dist/*")
    session.run(
        "check-wheel-contents", str(*Path("dist").glob("*.whl")), "--ignore=W002"
    )
