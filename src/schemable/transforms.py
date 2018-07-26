"""The transforms module.
"""

from collections.abc import Mapping
from operator import itemgetter

from .base import NotSet, SchemaABC, _CallableSchema
from .validators import All, Type


class Select(SchemaABC):
    """Schema helper that selects and optionally modifies source data.

    There are three ways to use:

    1. ``Select('<field>')``: Returns ``data['<field>']``.
    2. ``Select(<callable>)``: Passes source data to ``<callable>`` and
       returned value is the schema result.
    3. ``Select('<field>', <callable>)``: Passes ``data['<field>']`` to
       <callable> and returned value is the schema result.

    Args:
        spec (str|callable): The string field name to select from the source or
            a callable that accepts the source as its only argument.
        iteratee (callable, optional): A callable that modifies a source object
            field value. Is used when `spec` is a string that selects a field
            from the source and `iteratee` then modifies the field value.
    """
    _validate_obj = Type(Mapping)

    def __init__(self, spec, iteratee=None):
        spec = (spec, iteratee)
        super().__init__(spec)

    def compile(self, spec):
        key, iteratee = spec

        if callable(key):
            iteratee = key
            key = None

        if (key is not None and
                not callable(key) and
                (not isinstance(key, str) or not key)):
            raise TypeError('Schema spec must must be a callable or non-empty '
                            'string but found {!r}'.format(key))

        if iteratee is not None and not callable(iteratee):
            raise TypeError('Schema iteratee must be callable or None but '
                            'found {!r}'.format(iteratee))

        if isinstance(key, str):
            key = itemgetter(key)

        return All(*(As(fn) for fn in (key, iteratee) if fn))

    def __call__(self, obj):
        self._validate_obj(obj)

        return self.schema(obj)


class As(_CallableSchema, SchemaABC):
    """Schema helper that modifies a parsed schema value using a callable.

    Unlike :class:`.Validate` the return value from the callable will replace
    the parsed value. However, if an exception occurs, validation will fail.

    Args:
        spec (callable): Callable that transforms a value.
    """
    def __call__(self, obj):
        try:
            return self.schema(obj)
        except Exception as exc:
            raise AssertionError(
                '{}({!r}) should not raise an exception: {}: {}'
                .format(self.name, obj, exc.__class__.__name__, exc))
