User's Guide
============

Schemas are defined using the ``Schema`` class which returns a callable object that can then be used to validate and load data:

.. code-block:: python

    from schemable import Schema, SchemaResult

    schema = Schema([str])
    result = schema(['a', 'b', 'c'])

    assert isinstance(result, SchemaResult)
    assert hasattr(result, 'data')
    assert hasattr(result, 'error')


The return from a schema call is a ``SchemaResult`` instance that contains two attributes: ``data`` and ``errors``. The ``data`` object defaults to ``None`` when nothing could be successfully validated. It may also contain partially loaded data when some validation passed but other validation failed:

.. code-block:: python

    from schemable import Schema

    schema = Schema({str: {str: {str: int}}})
    schema({'a': {'b': {'c': 1}},
            'aa': {'bb': {'cc': 'dd'}}})
    # SchemaResult(
    #     data={'a': {'b': {'c': 1}}},
    #     errors={'aa': {'bb': {'cc': 'bad value: type error, expected int but found str'}}})


The ``errors`` attribute will either be a dictionary mapping of errors (when the top-level schema is a ``dict`` or ``list``) with keys corresponding to each point of failure or a string error message (when the top-level schema is *not* a ``dict`` or ``list``). If there are no errors, then ``SchemaResult.errors`` will be either ``{}`` or ``None``. The ``errors`` dictionary can span multiple "levels" and ``list`` indexes are treated as integer keys:

.. code-block:: python

    from schemable import Schema

    schema = Schema({str: [int]})
    schema({'a': [1, 2, '3', 4, '5'],
            'b': True})
    # SchemaResult(
    #     data={'a': [1, 2, 4]},
    #     errors={'a': {2: 'bad value: type error, expected int but found str',
    #                   4: 'bad value: type error, expected int but found str'},
    #             'b': 'bad value: type error, expected list but found bool'})


By default, schemas are evaulated in non-strict mode which always returns a ``SchemaResult`` instance whether validation passed or failed. However, in strict mode the exception ``SchemaError`` will be raised instead.

There are two ways to set strict mode:

1. Set ``strict=True`` when creating a ``Schema`` object (i.e., ``Schema(..., strict=True)``)
2. Set ``strict=True`` when evaulating a schema (i.e. ``schema(..., strict=True)``)

**TIP:** If ``Schema()`` was created with ``strict=True``, use ``schema(..., strict=False)`` to evaulate the schema in non-strict mode.

.. code-block:: python

    from schemable import Schema

    # Default to strict mode when evaulated.
    schema = Schema({str: [int]}, strict=True)
    schema({'a': [1, 2, '3', 4, '5'],
            'b': True})
    # Traceback (most recent call last):
    # ...
    # SchemaError: Schema validation failed: {'a': {2: 'bad value: type error, expected int but found str', 4: 'bad value: type error, expected int but found str'}, 'b': 'bad value: type error, expected list but found bool'}

    # disable with schema(..., strict=False)

    # Or use strict on a per-evaulation basis
    schema = Schema({str: [int]})
    schema({'a': [1, 2, '3', 4, '5'],
            'b': True},
           strict=True)


Validation
----------

Schemable is able to validate against the following:

- types (using ``type`` objects like ``str``, ``int``, ``bool``, etc.)
- raw values (like ``5``, ``'foo'``, etc.)
- dicts (using ``dict`` objects)
- lists (using ``list`` objects; applies schema object to all list items)
- nested schemas (using ``dict``, ``list``, or ``Schema()``)
- predicates (using callables that return a boolean value or raise an exception)
- all predicates (using ``schemable.All``)
- any predicate (using ``schemable.Any``)


Values
++++++

Validate against values:

.. code-block:: python

    from schemable import Schema

    schema = Schema(5)
    schema(5)
    # SchemaResult(data=5, errors=None)

    schema = Schema({'a': 5})
    schema({'a': 5})
    # SchemaResult(data={'a': 5}, errors=None)

    schema = Schema({'a': 5})
    schema({'a': 6})
    # SchemaResult(data=None, errors={'a': 'bad value: value error, '
    #                                      'expected 5 but found 6'})


Types
+++++

Validate against one (by using a single type, e.g. ``str``) or more (by using a tuple of types, e.g. ``(str, int, float)``) types:

.. code-block:: python

    from schemable import Schema

    schema = Schema(str)
    schema('a')
    # SchemaResult(data='a', errors=None)

    schema = Schema(int)
    schema('5')
    # SchemaResult(data=None, errors='type error, expected int but found str')

    schema = Schema((int, str))
    schema('5')
    # SchemaResult(data='5', errors=None)


Predicates
++++++++++

Predicates are simply callables that either return truthy or ``None`` (on successful validation) or falsey or raise an exception (on failed validation):

.. code-block:: python

    from schemable import Schema

    schema = Schema(lambda x: x > 5)
    schema(6)
    # SchemaResult(data=6, errors=None)

    schema = Schema(lambda x: x > 5)
    schema(4)
    # SchemaResult(data=None, errors='<lambda>(4) should evaluate to True')

    def gt_5(x): return x > 5
    schema = Schema(gt_5)
    schema(4)
    # SchemaResult(data=None, errors='gt_5(4) should evaluate to True')


All
+++

The ``All`` helper is used to validate against multiple predicates where all predicates must pass:

.. code-block:: python

    from schemable import Schema, All

    def lt_10(x): return x < 10
    def is_odd(x): return x % 2 == 1

    schema = Schema(All(lt_10, is_odd))
    schema(5)
    # SchemaResult(data=5, errors=None)

    schema = Schema(All(lt_10, is_odd))
    schema(6)
    # SchemaResult(data=None, errors='is_odd(6) should evaluate to True')


Any
+++

The ``Any`` helper is used to validate against multiple predicates where at least one predicate must pass:

.. code-block:: python

    from schemable import Schema, Any

    def is_float(x): return isinstance(x, float)
    def is_int(x): return isinstance(x, int)

    schema = Schema(Any(is_float, is_int))
    schema(5)
    # SchemaResult(data=5, errors=None)

    schema = Schema(Any(is_float, is_int))
    schema(5.2)
    # SchemaResult(data=5.2, errors=None)

    schema = Schema(Any(is_float, is_int))
    schema('a')
    # SchemaResult(data=None, errors="is_int('a') should evaluate to True"))


Lists
+++++

List validation is primarily used to validate each item in a list against a schema while also checking that the parent object is, in fact, a ``list``.

.. code-block:: python

    schema = Schema([str])

    schema(['a', 'b', 'c'])
    # SchemaResult(
    #     data=['a', 'b', 'c'],
    #     errors={})

    schema(['a', 'b', 'c', 3])
    # SchemaResult(
    #     data=['a', 'b', 'c'],
    #     errors={3: 'bad value: type error, expected str but found int'})

    schema = Schema([(int, float)])
    schema([1, 2.5, '3'])
    # SchemaResult(
    #     data=[1, 2.5],
    #     errors={2: 'bad value: type error, expected float or int but found str'})


Dictionaries
++++++++++++

Dictionary validation is one of the primary methods for creating schemas for validating things like JSON APIs, deserialized dictionaries, configuration objects, or any dict or dict-like object. These schemas are nestable and can be defined using dictionaries or lists or even other ``Schema`` instances defined elsewhere (i.e. ``Schema`` instances are reusable as part of a larger ``Schema``).

.. code-block:: python

    from schemable import Schema, Optional

    schema = Schema({
        'a': str,
        'b': int,
        Optional('c'): dict,
        'd': [{
            'e': str,
            'f': bool,
            'g': {
                'h': (int, float),
                'i': (int, bool)
            }
        }]
    })

    schema({
        'a': 'j',
        'b': 1,
        'd': [
            {'e': 'k', 'f': True, 'g': {'h': 1, 'i': False}},
            {'e': 'l', 'f': False, 'g': {'h': 1.5, 'i': 0}},
        ]
    })
    # SchemaResult(
    #     data={'a': 'j',
    #           'b': 1,
    #           'd': [{'e': 'k', 'f': True, 'g': {'h': 1, 'i': False}},
    #                 {'e': 'l', 'f': False, 'g': {'h': 1.5, 'i': 0}}]},
    #     errors={})

    schema({
        'a': 'j',
        'b': 1,
        'c': {'x': 1, 'y': 2},
        'd': [
            {'e': 'k', 'f': True, 'g': {'h': 1, 'i': False}},
            {'e': 'l', 'f': False, 'g': {'h': 1.5, 'i': 0}},
        ]
    })
    # SchemaResult(
    #     data={'a': 'j',
    #           'b': 1,
    #           'c': {'x': 1, 'y': 2},
    #           'd': [{'e': 'k', 'f': True, 'g': {'h': 1, 'i': False}},
    #                 {'e': 'l', 'f': False, 'g': {'h': 1.5, 'i': 0}}]},
    #     errors={})

    schema({
        'a': 'j',
        'b': 1,
        'c': [1, 2, 3],
        'd': [
            {'e': 'k', 'f': True, 'g': {'h': False, 'i': False}},
            {'e': 10, 'f': False, 'g': {'h': 1.5, 'i': 1.5}},
        ]
    })
    # SchemaResult(
    #     data={'a': 'j',
    #           'b': 1,
    #           'd': [{'e': 'k', 'f': True, 'g': {'i': False}},
    #                 {'f': False, 'g': {'h': 1.5}}]},
    #     errors={'c': 'bad value: type error, expected dict but found list',
    #             'd': {0: {'g': {'h': 'bad value: type error, expected float '
    #                                  'or int but found bool'}},
    #                   1: {'e': 'bad value: type error, expected str but '
    #                            'found int',
    #                       'g': {'i': 'bad value: type error, expected bool '
    #                                  'or int but found float'}}}})


By default all keys are required unless wrapped with ``Optional``. This includes key types like ``Schema({str: str})`` where that at least one data key must match all non-optional schema keys:

.. code-block:: python

    from schema import Schema, Optional

    # Fails due to missing at least one integer key.
    Schema({str: str, int: int})({'a': 'b'})
    # SchemaResult(data={'a': 'b'}, errors={<class 'int'>: 'missing required key'})

    # But this passes.
    Schema({str: str, Optional(int): int})({'a': 'b'})
    # SchemaResult(data={'a': 'b'}, errors={})


Optional keys can define a default using the ``default`` argument:

.. code-block:: python

    from schemable import Schema, Optional

    schema = Schema({
        Optional('a'): str,
        Optional('b', default=5): str,
        Optional('c', default=dict): str
    })

    schema({})
    # SchemaResult(data={'b': 5, 'c': {}}, errors={})


**TIP:** For mutable defaults, always use a callable that returns a new instance. For example, for ``{}`` use ``dict``, for ``[]`` use ``list``, etc. This prevents bugs where the same object is used for separate schema results that results in changes to one affecting all the others.

When determining how to handle extra keys (i.e. keys in the data but not matched in the schema), there are three modes:

- ``ALLOW_EXTRA``: Any extra keys are passed to ``SchemaResult`` as-is.
- ``DENY_EXTRA``: Any extra keys result in failed validation.
- ``IGNORE_EXTRA`` (the default): All extra keys are ignored and won't appear in ``SchemaResult``.

The "extra" mode is set via ``Schema(..., extra=ALLOW_EXTRA|DENY_EXTRA|IGNORE_EXTRA)``:

.. code-block:: python

    from schemable import ALLOW_EXTRA, DENY_EXTRA, IGNORE_EXTRA, Schema, Optional

    Schema({int: int})({1: 1, 'a': 'a'})
    # SchemaResult(data={1: 1}, errors={})

    # Same as above.
    Schema({int: int}, extra=IGNORE_EXTRA)({1: 1, 'a': 'a'})
    # SchemaResult(data={1: 1}, errors={})

    Schema({int: int}, extra=ALLOW_EXTRA)({1: 1, 'a': 'a'})
    # SchemaResult(data={1: 1, 'a': 'a'}, errors={})

    Schema({int: int}, extra=DENY_EXTRA)({1: 1, 'a': 'a'})
    # SchemaResult(data={1: 1}, errors={'a': "bad key: not in [<class 'int'>]"})


For some schemas, data keys may logically match multiple schema keys (e.g. ``{'a': int, str: str, (str, int): bool}``). However, value-based key schemas are treated differently than type-based or other key schemas when it comes to validation resolution. The value-based key schemas will take precedence over all others and will essentially "swallow" a key-value pair so that the value-based key schema must pass (while other key-schemas are ignored for a particular data key):

.. code-block:: python

    from schemable import Schema

    schema = Schema({
        'a': int,
        str: str,
    })

    # Value-based key schema takes precedence
    schema({'a': 'foo', 'x': 'y'})
    # SchemaResult(
    #     data={'x': 'y'},
    #     errors={'a': 'bad value: type error, expected int but found str'})

    schema({'a': 1, 'x': 'y'})
    # SchemaResult(data={'a': 1, 'x': 'y'}, errors={})


For non-value-based key schemas (in the absence of a value-based key match) *all* key schemas will be checked. Each matching key schema's value schema will then be used with ``Any()`` when evaluating the data value. As long as at least one of the data-value schemas match, the data key-value will validate. However, be aware that multiple matching key schemas likely indicates that the schema can be rewritten so that keys will only match a single key schema. Generally, this is preferrable since it makes the schema more deterministic and probably more "correct".

.. code-block:: python

    from schemable import Schema

    item = {'a': 1, 'x': 'y', 1: False, 2.5: 10.0, 'b': True}

    # Instead of this.
    Schema({
        'a': int,
        str: str,
        (str, int): bool,
        (int, float): float
    })(item)
    # SchemaResult(data={'a': 1, 'x': 'y', 1: False, 2.5: 10.0, 'b': True}, errors={})

    # Rewrite the schema to this.
    Schema({
        'a': int,
        str: (str, bool),
        int: (bool, float),
        float: float
    })(item)
    # SchemaResult(data={'a': 1, 'x': 'y', 1: False, 2.5: 10.0, 'b': True}, errors={})


Transformation
--------------

In addition to validation, Schemable can transform data into computed values. Transformations can also be combined with validation using ``All`` to ensure data is only transformed after passing validation.

.. code-block:: python

    from schemable import Schema, All, As

    # Validated that object is an integer or float.
    # Then transform it to a float.
    schema = Schema(All((int, float), As(float)))

    schema(1)
    # SchemaResult(data=1.0, errors=None)

    schema('a')
    # SchemaResult(data=None, errors='type error, expected float or int but found str')


As
+++

The ``As`` helper is used to transform data into another value using a callable. Unlike predicate callables, the return value from an ``As`` instance call is used to set the schema value.

.. code-block:: python

    from schemable import Schema, All, As

    schema = Schema({
        'a': As(int),
        'b': All(int, As(float))
    })

    schema({'a': '5', 'b': 3})
    # SchemaResult(data={'a': 5, 'b': 3.0}, errors={})

    schema({'a': '5', 'b': 3.5})
    # SchemaResult(
    #     data={'a': 5},
    #     errors={'b': 'bad value: type error, expected int but found float'})

    schema({'a': 'x', 'b': 3})
    # SchemaResult(
    #     data={'b': 3.0},
    #     errors={'a': "bad value: int('x') should not raise an exception: "
    #                  "invalid literal for int() with base 10: 'x'"})


``As`` can be used with ``All`` to perform validation and transformation. Each argument to ``All`` will be evaulated in series and composed so that multiple usage of ``As`` will simply transform the previous result.

.. code-block:: python

    schema = Schema(All(As(int), As(float)))
    schema(1.5)
    # SchemaResult(data=1.0, errors=None)


Related Libraries
-----------------

Schemable borrows featues from several other schema libraries:

- ``schema``: https://github.com/keleshev/schema
- ``voluptuous``: https://github.com/alecthomas/voluptuous
- ``marshmallow``: https://github.com/marshmallow-code/marshmallow

However, the main difference with Schemable is that it provides an interface similar to ``schema`` and ``voluptuous`` (i.e. simple object schema declartions using dicts/lists instead of classes) but supports partial data loading like ``marshmallow``. But unlike ``marshamallow``, there is no concept of loading/dumping or deserialization/serialization; there's just validation, transformation, and parsing (the de/serialization is left up to the developer).