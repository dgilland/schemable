
from abc import ABC, abstractmethod
from collections import namedtuple


#: Flag value for ``extra`` argument in :class:`.Schema` that allows extra dict
#: keys. Any extra key not defined in the schema will be included in the parsed
#: data.
ALLOW_EXTRA = True

#: Flag value for ``extra`` argument in :class:`.Schema` that denies extra dict
#: keys. Any extra key not defined in the schema will result in a schema error.
DENY_EXTRA = False

#: Flag value for ``extra`` argument in :class:`.Schema` that ignores extra
#: dict keys. Any extra key not defined in the schema will be ignored. This is
#: the default.
IGNORE_EXTRA = None


class _NotSet(object):  # pragma: no cover
    def __bool__(self):
        return False

    def __repr__(self):
        return '<NotSet>'


NotSet = _NotSet()


class SchemaResult(namedtuple('SchemaResult', ['data', 'errors'])):
    """The result returned from schema evaluation.

    Attributes:
        data (object): Parsed data that passed schema validation.
        errors (object): Schema errors as ``None``, ``dict``, or ``str``
            depending on whethere there were any errors and what kind of
            schema was defined.
    """
    pass


class SchemaError(AssertionError):
    """Exception raised when schema validation fails during strict schema mode.

    Attributes:
        message (str): Generic error message.
        errors (str|dict): Schema validation error string or dictionary.
        data (list|dict|None): Partially parsed data or ``None``.
        original_data (object): Original data being validated.
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
    related classes.
    """
    def __init__(self, spec):
        self.spec = spec
        self.spec_name = _get_spec_name(spec)
        self.schema = self.compile()

    def compile(self):
        return self.spec

    @abstractmethod
    def __call__(self):  # pragma: no cover
        pass

    def __str__(self):  # pragma: no cover
        return str(self.spec)

    def __repr__(self):  # pragma: no cover
        return '{0}({1!r})'.format(self.__class__.__name__, self.spec)

    __hash__ = None


class _HashableSchema(object):
    def __hash__(self):
        return hash(self.schema)

    def __eq__(self, other):
        return self.schema == other

    def __ne__(self, other):  # pragma: no cover
        return not (self == other)


def _get_spec_name(spec):
    if hasattr(spec, '__name__'):
        name = spec.__name__
    elif (hasattr(spec, '__class__') and
            hasattr(spec.__class__, '__name__')):
        name = spec.__class__.__name__
    else:  # pragma: no cover
        name = repr(spec)

    return name
