import doctest
import os
import sys

import scitacean

sys.path.insert(0, os.path.abspath("."))

# General information about the project.
project = "scitacean"
copyright = "2023 SciCat Project"
author = "Scitacean contributors"

html_show_sourcelink = True

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.autodoc_pydantic",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "nbsphinx",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pyscicat": ("https://scicatproject.github.io/pyscicat/", None),
}

# autodocs includes everything, even irrelevant API internals. autosummary
# looks more suitable in the long run when the API grows.
# For a nice example see how xarray handles its API documentation.
autosummary_generate = True

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = False
napoleon_preprocess_types = True
napoleon_type_aliases = {}
typehints_defaults = "comma"
typehints_use_rtype = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"
html_sourcelink_suffix = ""  # Avoid .ipynb.txt extensions in sources

# The master toctree document.
master_doc = "index"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = scitacean.__version__
# The full version, including alpha/beta/rc tags.
release = scitacean.__version__

warning_is_error = True

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "primary_sidebar_end": ["edit-this-page", "sourcelink"],
    "secondary_sidebar_items": [],
    "show_nav_level": 1,
    "header_links_before_dropdown": 4,
    "external_links": [
        {"name": "SciCat", "url": "https://scicatproject.github.io/"},
        {
            "name": "SciCat backend",
            "url": "https://scicatproject.github.io/documentation/",
        },
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/SciCatProject/scitacean",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/scitacean/",
            "icon": "fa-brands fa-python",
            "type": "fontawesome",
        },
    ],
}
html_context = {
    "doc_path": "docs",
}
html_sidebars = {
    "**": ["sidebar-nav-bs", "page-toc"],
}

html_title = "Scitacean"
html_logo = "_static/logo.svg"
html_favicon = "_static/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "scitaceandoc"

# -- Options for doctest --------------------------------------------------

# sc.plot returns a Figure object and doctest compares that against the
# output written in the docstring. But we only want to show an image of the
# figure, not its `repr`.
# In addition, there is no need to make plots in doctest as the documentation
# build already tests if those plots can be made.
# So we simply disable plots in doctests.
doctest_global_setup = """
"""

doctest_default_flags = (
    doctest.ELLIPSIS
    | doctest.IGNORE_EXCEPTION_DETAIL
    | doctest.DONT_ACCEPT_TRUE_FOR_1
    | doctest.NORMALIZE_WHITESPACE
)

# -- Options for linkcheck ------------------------------------------------

linkcheck_ignore = [
    # Specific lines in GitHub blobs cannot be found by linkcheck.
    r"https?://github\.com/.*?/blob/[a-f0-9]+/.+?#",
    # Many links for PRs from our release notes. Slow and unlikely to cause issues.
    "https://github.com/SciCatProject/scitacean/pulls/[0-9]+",
]

# -- Options for autodoc_pydantic -----------------------------------------

# Doesn't work because some types (e.g. PID) are not serializable.
autodoc_pydantic_model_show_json = False

# These mess up the index page.
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_model_show_validator_summary = False
