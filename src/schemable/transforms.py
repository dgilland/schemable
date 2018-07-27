"""The transforms module.
"""

from collections.abc import Mapping
from operator import itemgetter

from .base import NotSet, SchemaABC
from .validators import All, Type


class Use(SchemaABC):
    """Schema helper that returns a constant value or the return from a
    callable while ignoring the source data.

    Args:
        spec (object): Any object or callable.
    """
    def __call__(self, *args):
        if callable(self.schema):
            return self.schema()
        return self.schema


class Select(Use):
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

    def __init__(self, spec, iteratee=NotSet):
        spec = (spec, iteratee)
        super().__init__(spec)

    def compile(self):
        key, iteratee = self.spec

        if callable(key):
            iteratee = key
            key = NotSet

        if iteratee is not NotSet and not callable(iteratee):
            raise TypeError('Schema iteratee must be callable but found {!r}'
                            .format(iteratee))

        if key is not NotSet and not callable(key):
            key = itemgetter(key)

        return All(*(As(fn) for fn in (key, iteratee) if fn))

    def __call__(self, obj):
        self._validate_obj(obj)

        return self.schema(obj)


class As(SchemaABC):
    """Schema helper that modifies a parsed schema value using a callable.

    Unlike :class:`.Validate` the return value from the callable will replace
    the parsed value. However, if an exception occurs, validation will fail.

    Args:
        spec (callable): Callable that transforms a value.
    """
    def compile(self):
        if not callable(self.spec):
            raise TypeError('{} schema spec must be callable'
                            .format(self.__class__.__name__))

        return self.spec

    def __call__(self, obj):
        try:
            return self.schema(obj)
        except Exception as exc:
            raise AssertionError(
                '{}({!r}) should not raise an exception: {}: {}'
                .format(self.spec_name, obj, exc.__class__.__name__, exc))
