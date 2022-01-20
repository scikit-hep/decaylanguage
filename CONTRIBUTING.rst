============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/scikit-hep/decaylanguage/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.

Documentation improvements
==========================

decaylanguage could always use more documentation, whether as part of the
official decaylanguage docs, in docstrings, or even on the web in blog posts,
articles, and such.

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://github.com/scikit-hep/decaylanguage/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

To set up ``decaylanguage`` for local development:

1. Fork `decaylanguage <https://github.com/scikit-hep/decaylanguage>`_
   (look for the "Fork" button).

2. Clone your fork locally::

    git clone git@github.com:your_name_here/decaylanguage.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes, run all the checks, doc builder and spell checker with `nox <https://nox.thea.codes/en/stable/>`_ one command::

    nox

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``nox``) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.md`` about the changes.
4. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available locally, you can run a specific nox session with  ``nox -s tests-3.9``, for example. GitHub Actions will run all the tests whenever a pull request is made, so testing all versions of Python locally is usually not necessary.

Tips
----

To run a subset of tests::

    nox -s tests-3.9 -- -k test_myfeature
