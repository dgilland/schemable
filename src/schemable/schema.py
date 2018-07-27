"""The schema module.
"""

import schemable

from .base import (
    IGNORE_EXTRA,
    NotSet,
    SchemaABC,
    SchemaError,
    SchemaResult,
    _HashableSchema
)


class Schema(_HashableSchema, SchemaABC):
    """The primary schema class that defines the validation and loading
    specification of a schema.

    This class is used to create a top-level schema object that can be called
    on input data to validation and load it according to the specification.

    Args:
        spec (object): Schema specification.
        strict (bool, optional): Whether to evaluate schema in strict mode that
            will raise an exception on failed validation. Defaults to
            ``False``.
        extra (bool|None, optional): Sets the extra keys policy when validating
            :class:`.Dict` schemas. Defaults to :const:`.IGNORE_EXTRA`.
    """
    def __init__(self, spec, strict=False, extra=IGNORE_EXTRA):
        self.strict = strict
        self.extra = extra

        super().__init__(spec)

    def compile(self):
        # Compile `spec` into one of the available :class:`SchemaABC` dervied
        # classes based on type.
        if isinstance(self.spec, Schema):
            schema = self.spec.schema
        elif isinstance(self.spec, SchemaABC):
            schema = self.spec
        elif isinstance(self.spec, list):
            schema = schemable.List(self.spec)
        elif isinstance(self.spec, dict):
            schema = schemable.Dict(self.spec, extra=self.extra)
        elif isinstance(self.spec, (tuple, type)):
            schema = schemable.Type(self.spec)
        elif callable(self.spec):
            schema = schemable.Validate(self.spec)
        else:
            schema = schemable.Value(self.spec)

        return schema

    def __str__(self):
        return str(self.schema)

    def __repr__(self):  # pragma: no cover
        return '<{} {!r}>'.format(self.__class__.__name__, self.schema)

    def __call__(self, obj, strict=NotSet):
        if strict is NotSet:
            strict = self.strict

        try:
            result = self.schema(obj)
        except AssertionError as exc:
            result = SchemaResult(None, str(exc))

        if not isinstance(result, SchemaResult):
            result = SchemaResult(result, None)

        if strict and result.errors:
            raise SchemaError('Schema validation failed',
                              errors=result.errors,
                              data=result.data,
                              original_data=obj)

        return result
