"""
Purpose:
Provide the package boundary for the Home Assistant AI Analyzer service.

Input/Output:
Imported by the add-on runtime and test suite.

Important invariants:
Package metadata stays lightweight so imports remain cheap and predictable.

How to debug:
If module imports fail, start by verifying that the package was installed by pip inside the add-on image.
"""

__all__ = [
    "__version__",
]

__version__ = "0.3.3"
