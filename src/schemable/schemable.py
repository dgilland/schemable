"""The schemable module.
"""

from abc import ABC, abstractmethod
from collections import OrderedDict, namedtuple


SchemaResult = namedtuple('SchemaResult', ['data', 'errors'])

ALLOW_EXTRA = True
DENY_EXTRA = False
IGNORE_EXTRA = None


class _NotSet(object):  # pragma: no cover
    def __bool__(self):
        return False

    def __repr__(self):
        return '<NotSet>'


NotSet = _NotSet()


class SchemaError(AssertionError):
    """Exception raised when schema validation fails during strict schema mode.
    """
    def __init__(self, message, errors, data, original_data):
        super().__init__(message)
        self.message = message
        self.errors = errors
        self.data = data
        self.original_data = original_data

    def __str__(self):  # pragma: no cover
        return '{}: {}'.format(self.message, self.errors)


class SchemaABC(ABC):
    """Abstract base class that implements the core interface for all schema
    classes.
    """
    def __init__(self, schema, strict=False, extra=IGNORE_EXTRA):
        self.spec = schema
        self.strict = strict
        self.extra = extra

        self.schema = self.compile(schema)

    def compile(self, schema):
        return schema

    @abstractmethod
    def __call__(self):  # pragma: no cover
        pass

    def __str__(self):  # pragma: no cover
        return str(self.spec)

    def __repr__(self):  # pragma: no cover
        return '{0}({1!r})'.format(self.__class__.__name__, self.spec)

    __hash__ = None


class _HashableSchema(object):
    def __hash__(self):  # pragma: no cover
        return hash(self.schema)

    def __eq__(self, other):  # pragma: no cover
        return self.schema == other

    def __ne__(self, other):  # pragma: no cover
        return not(self == other)


class _CallableSchema(object):
    def compile(self, schema):
        if not callable(schema):  # pragma: no cover
            raise TypeError('{} schema value must be callable'
                            .format(self.__class__.__name__))

        if hasattr(schema, '__name__'):
            name = schema.__name__
        elif (hasattr(schema, '__class__') and
                hasattr(schema.__class__, '__name__')):
            name = schema.__class__.__name__
        else:  # pragma: no cover
            name = repr(schema)

        self.name = name

        return schema


class Schema(_HashableSchema, SchemaABC):
    """Schema loader and validation class that accepts a schema spec that can
    load and validate objects.
    """
    def compile(self, schema):
        if isinstance(schema, Schema):
            schema = schema.schema
        elif isinstance(schema, SchemaABC):
            pass
        elif isinstance(schema, list):
            schema = Collection(schema, strict=self.strict)
        elif isinstance(schema, dict):
            schema = Object(schema, strict=self.strict, extra=self.extra)
        elif isinstance(schema, (tuple, type)):
            schema = Type(schema, strict=self.strict)
        elif callable(schema):
            schema = Validate(schema, strict=self.strict)
        else:
            schema = Value(schema, strict=self.strict)

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


class Type(_HashableSchema, SchemaABC):
    """Schema for type objects."""
    def compile(self, schema):
        if isinstance(schema, type):
            schema = (schema,)
        elif (isinstance(schema, tuple) and
                all(isinstance(sch, type) for sch in schema)):
            schema = schema
        else:  # pragma: no cover
            raise TypeError(
                'Type schema value must be a type or a tuple of types')
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
        if not isinstance(obj, type):
            obj_type = type(obj)
        else:
            obj_type = obj

        try:
            instance_of = isinstance(obj_type, self.schema)
        except TypeError:  # pragma: no cover
            instance_of = False

        is_valid = (obj_type == self.spec or
                    obj_type in self.schema or
                    instance_of)

        assert is_valid, self._format_error(obj_type)

        return obj

    def _format_error(self, obj_type):
        def _format_type_names(types):
            if not isinstance(types, tuple):  # pragma: no cover
                types = (types,)

            fmt = ['{}'] * len(types)
            return (' or '.join(fmt)
                    .format(*sorted((t.__name__ for t in types),
                                    key=lambda n: n.lower())))

        return ('type error, expected {} but found {}'
                .format(_format_type_names(self.schema),
                        obj_type.__name__))


class Value(_HashableSchema, SchemaABC):
    """Schema for raw value objects."""
    def __call__(self, obj):
        if obj != self.schema:
            raise AssertionError('value error, expected {!r} but found {!r}'
                                 .format(self.schema, obj))

        return obj


class Collection(SchemaABC):
    """Schema for collections."""
    _validate_obj = Type(list)

    def compile(self, schema):
        if not isinstance(schema, list):  # pragma: no cover
            raise TypeError('{} schema value must be a list'
                            .format(self.__class__.__name__))

        return All(*schema)

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


class Object(SchemaABC):
    """Schema for objects."""
    _validate_obj = Type((dict, OrderedDict))

    def compile(self, schema):
        if not isinstance(schema, dict):  # pragma: no cover
            raise TypeError('{} schema value must be a dict'
                            .format(self.__class__.__name__))

        schema = self._prioritize_schema(schema)

        self.keys = sorted(schema.keys(), key=str)
        self.required = set(k for k in schema
                            if not isinstance(k.schema, Optional))
        self.defaults = {k.schema.spec: k.schema.default
                         for k in schema
                         if isinstance(k.schema, Optional) and
                         k.schema.default is not NotSet}

        return schema

    def _prioritize_schema(self, schema):
        # Order schema by whether the schema key is a Value object or not so
        # that all Value objects are first in the schema. This way we favor
        # validating a key by Value schemas over Type schemas.
        schemas = sorted(((Schema(key), Schema(value, extra=self.extra))
                          for key, value in schema.items()),
                         key=self._priority_sort_key)

        return OrderedDict(schemas)

    def _priority_sort_key(self, kv_schema):
        if isinstance(kv_schema[0].schema, Value):
            return -1
        else:
            return -2

    def __call__(self, obj):
        self._validate_obj(obj)

        # As type(obj) to create data so that data's type is the same as obj
        # since we support multiple types for obj.
        data = type(obj)()
        errors = {}

        # Track obj keys that are validated.
        seen = set()

        for key, value in obj.items():
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
                for key_schema in self.schema:
                    if not key_schema(key).errors:
                        # Don't add duplicate value schemas.
                        if self.schema[key_schema] not in value_schemas:
                            value_schemas += (self.schema[key_schema],)
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

            # Keep track of seen keys so we can later check for any required
            # key violations.
            seen.add(key)

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

            value_result = value_schema(value)

            if value_result.errors:
                # If errors is a string, then we want to wrap it with a custom
                # message; otherwise, errors is a dict of other errors so we
                # just assign it.
                error = value_result.errors
                if isinstance(value_result.errors, str):
                    error = 'bad value: {}'.format(error)
                errors[key] = error

            # Ensure data is partially/fullly loaded.
            if value_result.data is not None or not value_result.errors:
                data[key] = value_result.data

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


class Optional(_HashableSchema, SchemaABC):
    """Schema used to mark a ``dict`` key as optional."""
    def __init__(self, schema, default=NotSet):
        super().__init__(schema)
        self._default = default

    @property
    def default(self):
        if callable(self._default):
            return self._default()
        return self._default

    def compile(self, schema):
        if (isinstance(schema, type) or
                (isinstance(schema, tuple) and
                 all(isinstance(sch, type) for sch in schema))):
            schema = Type(schema)
        else:
            schema = Value(schema)

        return schema

    def __call__(self, obj):
        return self.schema(obj)


class All(SchemaABC):
    """Schema for applying a list of schemas to an object and requiring that no
    schemas have any errors.
    """
    def __init__(self, *schemas):
        super().__init__(schemas)

    def compile(self, schema):
        return tuple(Schema(value) for value in schema)

    def __call__(self, obj):
        result = SchemaResult(obj, None)

        for schema in self.schema:
            result = schema(result.data)

            if result.errors:
                break

        return result


class Any(SchemaABC):
    """Schema for applying a list of schemas to an object and requiring that at
    least one schema has no errors.
    """
    def __init__(self, *schemas):
        super().__init__(schemas)

    def compile(self, schema):
        return tuple(Schema(value) for value in schema)

    def __call__(self, obj):
        result = SchemaResult(obj, None)

        for schema in self.schema:
            data = result.data if result.data is not None else obj
            result = schema(data)

            if not result.errors:
                break

        return result


class Validate(_CallableSchema, SchemaABC):
    """Schema to validate an object using a callable."""
    def __call__(self, obj):
        try:
            ret = self.schema(obj)
        except Exception:
            ret = False

        if not ret and ret is not None:
            raise AssertionError('{}({!r}) should evaluate to True'
                                 .format(self.name, obj))

        return obj


class As(_CallableSchema, SchemaABC):
    """Schema to modify an object using a callable."""
    def __call__(self, obj):
        try:
            return self.schema(obj)
        except Exception as exc:
            raise AssertionError('{}({!r}) should not raise an exception: {}'
                                 .format(self.name, obj, exc))
