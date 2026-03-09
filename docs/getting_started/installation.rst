============
Installation
============

From PyPI (recommended):

.. code-block:: bash

   pip install decaylanguage

From the GitHub repository:

.. code-block:: bash

   pip install git+https://github.com/scikit-hep/decaylanguage.git

DecayLanguage requires Python 3.10 or later.

Dependencies
------------

DecayLanguage depends on the following packages, which are installed automatically:

- `particle <https://github.com/scikit-hep/particle>`_ — PDG particle data and identification codes
- `lark <https://github.com/lark-parser/lark>`_ — grammar-based parsing for ``.dec`` files
- `graphviz (Python) <https://github.com/xflr6/graphviz>`_ — decay chain visualization
- `attrs <https://www.attrs.org/>`_ — dataclass utilities
- `NumPy <https://numpy.org/>`_, `pandas <https://pandas.pydata.org/>`_
- `hepunits <https://github.com/scikit-hep/hepunits>`_ — HEP units and constants
- `plumbum <https://plumbum.readthedocs.io/>`_ — CLI toolkit

To render decay chain visualizations, you also need the
`Graphviz <https://graphviz.org/download/>`_ system package installed.
