# docs/conf.py
# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../'))  # Path to your Python code

# -- Project information -----------------------------------------------------

project = 'Therapeutic Text Adventure'
copyright = '2024, Your Name'
author = 'Your Name'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',  # Automatically generate documentation from docstrings
    'sphinx.ext.napoleon',  # Support for Google-style docstrings
    'sphinx.ext.viewcode',  # Add links to source code
    'sphinx.ext.intersphinx',  # Link to other Sphinx documentation
    'sphinx.ext.todo',      # Support for todo lists
    'sphinx_rtd_theme',     # Read the Docs theme (optional, but nice)
    'myst_parser',          # Support for Markdown files (optional)
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'  # Use the Read the Docs theme

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Options for autodoc ----------------------------------------------------
autodoc_default_options = {
    'members': True,          # Document members (methods, attributes)
    'member-order': 'bysource',  # Order members as they appear in the source code
    'undoc-members': True,      # Include undocumented members
    'show-inheritance': True,   # Show inheritance for classes
}
autodoc_typehints = "description" # Show type hints in the description, not the signature

# -- Options for intersphinx -------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'neo4j': ('https://neo4j.com/docs/api/python-driver/current/', None),
    'langchain': ('https://api.python.langchain.com/en/latest/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
    # Add other mappings as needed
}

# -- Options for todo --------------------------------------------------------
todo_include_todos = True # Set to False in production

# -- Options for MyST Parser (if using Markdown)----------------------------
myst_enable_extensions = [
  "amsmath",
  "colon_fence",
  "deflist",
  "dollarmath",
  "fieldlist",
  "html_admonition",
  "html_image",
  "replacements",
  "smartquotes",
  "strikethrough",
  "substitution",
  "tasklist",
]