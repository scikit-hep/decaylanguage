# -*- coding: utf-8 -*-
import nox

PYTHON_VERSIONS = ["2.7", "3.6", "3.7", "3.8", "3.9", "3.10"]


@nox.session
def lint(session):
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    session.install(".[test]")
    session.run("pytest", *session.posargs)


@nox.session
def build(session):
    """
    Build an SDist and wheel.
    """

    session.install("build")
    session.run("python", "-m", "build")
