"""The transforms module.
"""

from .base import SchemaABC, _CallableSchema


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
            raise AssertionError('{}({!r}) should not raise an exception: {}'
                                 .format(self.name, obj, exc))
