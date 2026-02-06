from __future__ import annotations

from pathlib import Path

import nox

nox.needs_version = ">=2024.4.15"
nox.options.default_venv_backend = "uv|virtualenv"

ALL_PYTHONS = [
    c.split()[-1]
    for c in nox.project.load_toml("pyproject.toml")["project"]["classifiers"]
    if c.startswith("Programming Language :: Python :: 3.")
]


@nox.session
def lint(session):
    session.install("prek")
    session.run("prek", "run", "--all-files", *session.posargs)


@nox.session
def pylint(session: nox.Session) -> None:
    """
    Run pylint.
    """
    session.install("-e.", "--group=dev", "pylint")
    session.run("pylint", "src", *session.posargs)


@nox.session(python=ALL_PYTHONS)
def tests(session):
    session.install(".", "--group=test")
    session.run("pytest", *session.posargs)


@nox.session(default=False)
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
