"""
Invoke tasks to help with pytest development and release process.
"""

import invoke

from . import generate, vendoring


ns = invoke.Collection(
    generate,
    vendoring
)
