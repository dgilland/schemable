"""The schemable package.

A schema loading and validation library
"""

from .__version__ import __version__

from .schemable import (
    ALLOW_EXTRA,
    DENY_EXTRA,
    IGNORE_EXTRA,
    All,
    Any,
    As,
    Dict,
    List,
    Optional,
    Schema,
    SchemaError,
    SchemaResult,
    Type,
    Validate,
    Value
)
