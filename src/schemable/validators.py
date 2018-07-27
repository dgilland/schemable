"""The validators module.
"""

from collections import OrderedDict
from collections.abc import Mapping

import schemable

from .base import (
    ALLOW_EXTRA,
    DENY_EXTRA,
    IGNORE_EXTRA,
    NotSet,
    SchemaABC,
    SchemaResult,
    _HashableSchema
)


class Type(_HashableSchema, SchemaABC):
    """Schema helper that validates against types.

    Args:
        spec (type|tuple[type]): A type or tuple or tuple of types to validate
            against.
    """
    def compile(self):
        if isinstance(self.spec, type):
            schema = (self.spec,)
        elif (isinstance(self.spec, tuple) and
                all(isinstance(s, type) for s in self.spec)):
            schema = self.spec
        else:
            raise TypeError('{} schema spec must be a type or a tuple of types'
                            .format(self.__class__.__name__))
        return schema

    def __str__(self):
        if isinstance(self.spec, tuple):
            fmt = ['{}'] * len(self.spec)
            types = ', '.join(fmt).format(*(type_.__name__
                                            for type_ in self.spec))
            return '({})'.format(types)
        else:
            return self.spec.__name__

    def __call__(self, obj):
        if not isinstance(obj, self.schema):
            raise AssertionError(self._format_error(obj))

        return obj

    def _format_error(self, obj):
        expected = (
            ' or '.join(['{}'] * len(self.schema))
            .format(*sorted((t.__name__ for t in self.schema),
                            key=lambda n: n.lower())))

        return ('type error, expected {} but found {}'
                .format(expected, type(obj).__name__))


class Value(_HashableSchema, SchemaABC):
    """Schema helper that validates against value equality.

    Args:
        spec (object): Value to compare to.
    """
    def __call__(self, obj):
        if obj != self.schema:
            raise AssertionError('value error, expected {!r} but found {!r}'
                                 .format(self.schema, obj))

        return obj


class List(SchemaABC):
    """Schema helper that validates against list objects.

    Args:
        spec (list): List containing schema specification to validate each list
            item against.
    """
    _validate_obj = Type(list)

    def compile(self):
        if not isinstance(self.spec, list):
            raise TypeError('{} schema spec must be a list'
                            .format(self.__class__.__name__))

        return All(*self.spec)

    def __call__(self, obj):
        self._validate_obj(obj)

        data = []
        errors = {}

        for key, value in enumerate(obj):
            result = self.schema(value)

            if result.errors:
                error = result.errors
                if isinstance(error, str):
                    # If errors is a string, then we want to wrap it with
                    # custom message; otherwise, errors is a dict of other
                    # errors so just assign it.
                    error = 'bad value: {}'.format(result.errors)
                errors[key] = error

            if result.data is not None:
                data.append(result.data)

        if (not data and errors):
            data = None

        return SchemaResult(data, errors)


class Dict(SchemaABC):
    """Schema helper that validates against dict or dict-like objects.

    Args:
        spec (dict): Dictionary containing schema specification to validate
            against.
        extra (bool|None, optional): Sets the extra keys policy. Defaults to
            :const:`.IGNORE_EXTRA`.
    """
    _validate_obj = Type(Mapping)

    def __init__(self, spec, extra=IGNORE_EXTRA):
        self.extra = extra

        super().__init__(spec)

    def compile(self):
        if not isinstance(self.spec, dict):
            raise TypeError('{} schema spec must be a dict'
                            .format(self.__class__.__name__))

        # Order schema by whether the schema key is a Value object or not so
        # that all Value objects are first in the schema. This way we favor
        # validating a key by Value schemas over Type schemas.
        schemas = sorted(
            ((schemable.Schema(key), schemable.Schema(value, extra=self.extra))
             for key, value in self.spec.items()),
            key=self._spec_priority_sort_key)
        schema = OrderedDict(schemas)

        self.keys = sorted(schema.keys(), key=str)
        self.required = set(k for k in schema
                            if not isinstance(k.schema, Optional))
        self.defaults = {k.schema.spec: k.schema.default
                         for k in schema
                         if isinstance(k.schema, Optional) and
                         k.schema.default is not NotSet}

        return schema

    def _spec_priority_sort_key(self, kv_schema):
        if isinstance(kv_schema[0].schema, Value):
            return -1
        else:
            return -2

    def __call__(self, obj):
        self._validate_obj(obj)

        data = {}
        errors = {}

        # Track obj keys that are validated.
        seen = set()
        self._extend_with_usables(obj, data, errors, seen)

        for key, value in obj.items():
            if key in seen:
                continue

            # It's possible that a key may apply to multiple key schemas (e.g.
            # {str: str, (str, int): int}). In most cases, these schemas should
            # be rewritten so that the schema key types are exclusive but we
            # can still handle this scenario by keeping track of all value
            # schemas whose key schema matches. We can then check each value
            # schema and if any of the value schemas match, then the key/value
            # will be considered valid.
            value_schemas = ()

            if key in self.schema:
                # The exception to the above about trying multiple value
                # schemas is when there is a named key schema
                # (e.g. {'a': str, str: int}) where only the named key schema
                # should apply (in this case, only check that key 'a' has type
                # `str` while ignoring the key `str` with type `int`).
                value_schemas += (self.schema[key],)
            else:
                # For all other key schemas, we'll compose a list of value
                # schemas to validate against. Basically, we'll treat it like
                # an Any() schema (e.g. {str: str, (str, int): int} would be
                # like {(str, int): Any(str, int)}.
                for key_schema, value_schema in self.schema.items():
                    if isinstance(value_schema.spec, schemable.Use):
                        continue

                    if not key_schema(key).errors:
                        # Don't add duplicate value schemas.
                        if value_schema not in value_schemas:
                            value_schemas += (value_schema,)
                        seen.add(key_schema)

            if not value_schemas:
                # None of the key schemas match this obj key so need to check
                # the "extra" policy to determine what to do with it. If the
                # extra policy is anything other than ALLOW or DENY, then we
                # ignore the extra key and don't add it as data or an error.
                if self.extra is ALLOW_EXTRA:
                    # Extra values are allowed when no key-schema can be found
                    # so store it as data.
                    data[key] = value
                elif self.extra is DENY_EXTRA:
                    # Extra values are denied when no key-schema can be found
                    # so store it as error.
                    errors[key] = ('bad key: not in {}'
                                   .format([k.schema.spec for k in self.keys]))
                continue  # pragma: no cover

            # In the event that we have multiple value schemas due to `key`
            # matching multiple key schemas, we will apply the Any() validator
            # and return its results; otherwise, we'll just validate against
            # the one value schema.
            # NOTE: We could just apply Any() in all cases but we'll get a
            # slight performance improvement by not wrapping it. Generally, the
            # multiple value schemas should be a rarity so better to use the
            # more direct route since it applies in most cases.
            if len(value_schemas) == 1:
                value_schema = value_schemas[0]
            else:
                value_schema = Any(*value_schemas)

            self._extend_with_result(
                key, value_schema(value), data, errors, seen)

        missing = self.required - seen

        if missing:
            for key in missing:
                errors[key.schema.spec] = 'missing required key'

        if self.defaults:
            for key, default in self.defaults.items():
                data.setdefault(key, default)

        # Ensure data is None when it's empty and there are errors or if no
        # errors, then when data doesn't equal `obj` (this covers the case when
        # data=={} and obj=={}).
        if not data and (errors or data != obj):
            data = None

        return SchemaResult(data, errors)

    def _extend_with_result(self, key, result, data, errors, seen):
        if result.errors:
            # If errors is a string, then we want to wrap it with a custom
            # message; otherwise, errors is a dict of other errors so we
            # just assign it.
            error = result.errors
            if isinstance(result.errors, str):
                error = 'bad value: {}'.format(error)
            errors[key] = error

        # Ensure data is partially/fullly loaded.
        if result.data is not None or not result.errors:
            data[key] = result.data

        # Keep track of seen keys so we can later check for any required
        # key violations.
        seen.add(key)

    def _extend_with_usables(self, obj, data, errors, seen):
        for key_schema, value_schema in self.schema.items():
            if not isinstance(value_schema.spec, schemable.Use):
                continue
            key = key_schema.spec
            seen.add(key_schema)
            self._extend_with_result(
                key, value_schema(obj), data, errors, seen)


class Optional(_HashableSchema, SchemaABC):
    """Schema helper used to mark a :class:`Dict` key as optional.

    Args:
        spec (object): :class:`Dict` key schema specification.
        default (object, optional): Default value or callable that returns a
            default to be used when a key isn't given.
    """
    def __init__(self, spec, default=NotSet):
        self._default = default
        super().__init__(spec)

    def compile(self):
        if (isinstance(self.spec, type) or
                (isinstance(self.spec, tuple) and
                 all(isinstance(s, type) for s in self.spec))):
            schema = Type(self.spec)
        else:
            schema = Value(self.spec)

        return schema

    @property
    def default(self):
        if callable(self._default):
            return self._default()
        return self._default

    def __call__(self, obj):
        return self.schema(obj)


class All(SchemaABC):
    """Schema helper that validates against a list of schemas where all schems
    must validate.

    Args:
        *specs (object): Schema specifications to validate against.
    """
    def __init__(self, *specs):
        super().__init__(specs)

    def compile(self):
        return tuple(schemable.Schema(s) for s in self.spec)

    def __call__(self, obj):
        result = SchemaResult(obj, None)

        for schema in self.schema:
            result = schema(result.data)

            if result.errors:
                break

        return result


class Any(SchemaABC):
    """Schema helper that validates against a list of schemas where at least
    one schema must validate.

    Args:
        *specs (object): Schema specifications to validate against.
    """
    def __init__(self, *specs):
        super().__init__(specs)

    def compile(self):
        return tuple(schemable.Schema(s) for s in self.spec)

    def __call__(self, obj):
        result = SchemaResult(obj, None)

        for schema in self.schema:
            data = result.data if result.data is not None else obj
            result = schema(data)

            if not result.errors:
                break

        return result


class Validate(SchemaABC):
    """Schema helper that validates against a callable.

    Validation passes if the callable returns ``None`` or a truthy value.
    Validation fails if the callable raises and exception or returns a non-None
    falsey value.

    Args:
        spec (callable): Callable to validate against.
    """
    def compile(self):
        if not callable(self.spec):
            raise TypeError('{} schema spec must be callable'
                            .format(self.__class__.__name__))

        return self.spec

    def __call__(self, obj):
        try:
            ret = self.schema(obj)
        except Exception:
            ret = False

        if not ret and ret is not None:
            raise AssertionError('{}({!r}) should evaluate to True'
                                 .format(self.spec_name, obj))

        return obj
