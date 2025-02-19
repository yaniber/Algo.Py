# docs/conf.py
import os
import sys

# Add your project to Python path (CRUCIAL for autodoc)
sys.path.insert(0, os.path.abspath('..'))

print("Python path:", sys.path) 

# -- Project information
project = 'Algo.Py'
copyright = '2025, Himanshu Rathore'
author = 'Himanshu Rathore'
release = '2025'  # Full version (e.g., "1.0.0")

# -- General configuration
extensions = [
    'sphinx.ext.autodoc',   # Auto-generate docs from docstrings
    'sphinx.ext.viewcode',  # Add "View Source" links
    'sphinx.ext.napoleon'   # Support Google-style docstrings
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- HTML Output
html_theme = 'sphinx_rtd_theme'  # Replace 'alabaster' with ReadTheDocs theme
html_static_path = ['_static']  # Can comment out if not using custom CSS/JS