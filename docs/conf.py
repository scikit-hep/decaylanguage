from __future__ import annotations

import shutil
from importlib.metadata import version as get_version
from pathlib import Path

DIR = Path(__file__).parent.resolve()
BASEDIR = DIR.parent

# -- Project information -----------------------------------------------------

project = "DecayLanguage"
author = "Scikit-HEP"
copyright = "2018, Scikit-HEP developers"
version = release = get_version("decaylanguage")

# -- General configuration ---------------------------------------------------

extensions = [
    "jupyter_sphinx",
    "myst_parser",
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
]

exclude_patterns = [
    "_build",
    "**.ipynb_checkpoints",
    "readme.md",
    "changelog.md",
    # Linked/copied repo directories (created by build hooks for notebook path resolution)
    "examples/images",
    "examples/models",
    "examples/tests",
]
nitpicky = True
nitpick_ignore = [
    ("py:class", "graphviz.graphs.Digraph"),
    ("py:class", "graphviz.sources.Source"),
    ("py:class", "lark.tree.Tree"),
    ("py:class", "pandas.core.frame.DataFrame"),
    ("py:class", "particle.particle.particle.Particle"),
    ("py:class", "pd.DataFrame"),
    ("py:mod", "decaylanguage.dec"),
    ("py:mod", "decaylanguage.decay"),
    ("py:mod", "decaylanguage.modeling"),
    ("py:mod", "decaylanguage.utils"),
]

# -- Extension configuration -------------------------------------------------

extlinks = {
    "issue": ("https://github.com/scikit-hep/decaylanguage/issues/%s", "#%s"),
    "pr": ("https://github.com/scikit-hep/decaylanguage/pull/%s", "PR #%s"),
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False

autodoc_member_order = "bysource"
autodoc_typehints = "description"

nbsphinx_kernel_name = "python3"
nbsphinx_execute = "always"

# -- Options for HTML output -------------------------------------------------

html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "github_url": "https://github.com/scikit-hep/decaylanguage",
    "logo": {
        "text": "DecayLanguage",
    },
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "header_links_before_dropdown": 4,
    "navigation_with_keys": False,
    "show_nav_level": 2,
    "show_prev_next": True,
}

html_show_sourcelink = False

# -- Build hooks: copy files into docs tree ----------------------------------


def _copy_files(_app):
    """Copy README.md, CHANGELOG.md, and notebooks into docs/ at build time.

    Notebooks use relative paths like ``../models/...`` and ``../tests/data/...``.
    To preserve these paths when notebooks are copied into ``docs/examples/notebooks/``,
    we create symlinks under ``docs/examples/`` pointing back to the repo-root directories.
    """
    for name, dst_name in [
        ("README.md", "readme.md"),
        ("CHANGELOG.md", "changelog.md"),
    ]:
        src = BASEDIR / name
        dst = DIR / dst_name
        if src.exists():
            shutil.copy2(src, dst)

    # Copy notebooks into docs tree
    nb_src = BASEDIR / "notebooks"
    nb_dst = DIR / "examples" / "notebooks"
    nb_dst.mkdir(parents=True, exist_ok=True)
    if nb_src.exists():
        for f in nb_src.iterdir():
            if f.suffix in (".ipynb", ".txt", ".cu"):
                shutil.copy2(f, nb_dst / f.name)

    # Link repo directories so notebook relative paths (../<dir>) resolve correctly.
    # Use symlinks where possible, fall back to copying (e.g. on Windows without dev mode).
    examples_dir = DIR / "examples"
    for name in ("images", "models", "tests"):
        link = examples_dir / name
        target = BASEDIR / name
        if target.exists() and not link.exists():
            try:
                link.symlink_to(target.resolve())
            except OSError:
                shutil.copytree(target, link)


def _cleanup_files(_app, _exception):
    """Remove copied files and symlinks after build."""
    for name in ("readme.md", "changelog.md"):
        f = DIR / name
        if f.exists():
            f.unlink()

    nb_dst = DIR / "examples" / "notebooks"
    if nb_dst.exists():
        for f in nb_dst.iterdir():
            if f.is_file() and f.name != "index.rst":
                f.unlink()

    # Remove symlinks or copied directories created for notebook path resolution
    examples_dir = DIR / "examples"
    for name in ("images", "models", "tests"):
        link = examples_dir / name
        if link.is_symlink():
            link.unlink()
        elif link.is_dir():
            shutil.rmtree(link)


def setup(app):
    app.connect("builder-inited", _copy_files)
    app.connect("build-finished", _cleanup_files)
