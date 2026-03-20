============
Installation
============

From PyPI:

.. code-block:: bash

   pip install decaylanguage

Dependencies
------------

DecayLanguage depends on the following packages, which are installed automatically:

- `NumPy <https://numpy.org/>`_ — the numerical library for Python
- `pandas <https://pandas.pydata.org/>`_ — tabular data in Python
- `attrs <https://www.attrs.org/>`_ — dataclass utilities
- `graphviz (Python) <https://github.com/xflr6/graphviz>`_ — decay chain visualization
- `lark <https://github.com/lark-parser/lark>`_ — grammar-based parsing for ``.dec`` files
- `plumbum <https://plumbum.readthedocs.io/>`_ — CLI toolkit
- `hepunits <https://github.com/scikit-hep/hepunits>`_ — HEP units and constants
- `particle <https://github.com/scikit-hep/particle>`_ — PDG particle data and identification codes

To render decay chain visualizations, you also need the
`Graphviz <https://graphviz.org/download/>`_ system package installed.
