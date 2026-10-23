# Configuration file for the Sphinx documentation builder.
import os
import sys

sys.path.insert(0, os.path.abspath("../../src/braidpy"))

# -- Project information

project = "braidpy"
copyright = ""
author = "Baptiste Labat"

# The version is the package's own, read from pyproject.toml.
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
with open(os.path.join(os.path.dirname(__file__), "../../pyproject.toml"), "rb") as f:
    release = version = tomllib.load(f)["project"]["version"]

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "myst_parser",
]

# $...$ for inline maths, and the aligned environments the geometry
# pages use.  Without these, the formulas render as literal dollars.
myst_enable_extensions = ["dollarmath", "amsmath"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

# -- Options for EPUB output
epub_show_urls = "footnote"

# A docstring's "Attributes:" section as fields of its class, not as
# attributes of their own: autodoc documents the attributes already.
napoleon_use_ivar = True

# Optional but helpful:
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "show-inheritance": True,
}
