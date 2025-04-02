# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import tomllib

# Add the source code directory to sys.path
sys.path.insert(0, os.path.abspath("../../src"))

with open("../../pyproject.toml", "rb") as f:
    pyproject_data = tomllib.load(f)

project_version = pyproject_data.get("project", {}).get("version", "-")

project = 'MABLE'
copyright = 'All rights reserved, 2024, Jan Buermann'
author = 'Jan Buermann'
release = project_version

rst_epilog = f"""
.. |project_version| replace:: {project_version}
.. |project_version_bold| replace:: **{project_version}**
.. |project_version_it| replace:: *{project_version}*
"""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx_paramlinks',
    'myst_parser',
    # "sphinx.ext.viewcode",
]

autosummary_generate = True
autodoc_default_options = {
    'special-members': '__init__',
}

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {'navigation_depth': 10}

html_logo = "_static/mable_logo.png"
html_favicon = "_static/mable_favicon.png"
