schemable
*********

|version| |travis| |coveralls| |license|


Schemable is a schema parsing and validation library that let's you define schemas simply using dictionaries, lists, types, and callables.


Links
=====

- Project: https://github.com/dgilland/schemable
- Documentation: https://schemable.readthedocs.io
- PyPI: https://pypi.python.org/pypi/schemable/
- TravisCI: https://travis-ci.org/dgilland/schemable


Features
========

- Simple schema definitions using ``dict``, ``list``, and ``type`` objects
- Complex schema definitions using ``Any``, ``All``, ``As``, and predicates
- Detailed validation error messages
- Partial data loading on validation failure
- Strict and non-strict parsing modes
- Python 3.4+


Quickstart
==========

Install using pip:


::

    pip install schemable


Validate and load data using ``dict`` and ``list`` objects:

.. code-block:: python

    from schemable import Schema, All, Any, As, Optional, SchemaError

    user_schema = Schema({
        'name': str,
        'email': All(str, lambda email: len(email) > 3 and '@' in email),
        'active': bool,
        'settings': {
            Optional('theme'): str,
            Optional('language', default='en'): str,
            Optional('volume'): int,
            str: str
        },
        'aliases': [str],
        'phone': All(str,
                     As(lambda phone: ''.join(filter(str.isdigit, phone))),
                     lambda phone: 10 <= len(phone) <= 15),
        'addresses': [{
            'street_addr1': str,
            Optional('street_addr2', default=None): Any(str, None),
            'city': str,
            'state': str,
            'country': str,
            'zip_code': str
        }]
    })

    # Fail!
    result = user_schema({
        'name': 'Bob Barr',
        'email': 'bob.example.com',
        'active': 1,
        'settings': {
            'theme': False,
            'extra_setting1': 'val1',
            'extra_setting2': True
        },
        'phone': 1234567890,
        'addresses': [
            {'street_addr1': '123 Lane',
             'city': 'City',
             'state': 'ST',
             'country': 'US',
             'zip_code': 11000}
        ]
    })

    print(result)
    # SchemaResult(
    #     data={'name': 'Bob Barr',
    #           'settings': {'extra_setting1': 'val1',
    #                        'language': 'en'}
    #           'addresses': [{'street_addr1': '123 Lane',
    #                          'city': 'City',
    #                          'state': 'ST',
    #                          'country': 'US',
    #                          'street_addr2': None}]},
    #     errors={'email': "bad value: <lambda>('bob.example.com') should evaluate to True",
    #             'active': 'bad value: type error, expected bool but found int',
    #             'settings': {'theme': 'bad value: type error, expected str but found bool',
    #                          'extra_setting2': 'bad value: type error, expected str but found bool'},
    #             'phone': 'bad value: type error, expected str but found int',
    #             'addresses': {0: {'zip_code': 'bad value: type error, expected str but found int'}},
    #             'aliases': 'missing required key'})

    # Fail!
    result = user_schema({
        'name': 'Bob Barr',
        'email': 'bob@example.com',
        'active': True,
        'settings': {
            'theme': False,
            'extra_setting1': 'val1',
            'extra_setting2': 'val2'
        },
        'phone': '123-456-789',
        'addresses': [
            {'street_addr1': '123 Lane',
             'city': 'City',
             'state': 'ST',
             'country': 'US',
             'zip_code': '11000'}
        ]
    })

    print(result)
    # SchemaResult(
    #     data={'name': 'Bob Barr',
    #           'email': 'bob@example.com',
    #           'active': True,
    #           'settings': {'extra_setting1': 'val1',
    #                        'extra_setting2': 'val2',
    #                        'language': 'en'},
    #           'addresses': [{'street_addr1': '123 Lane',
    #                          'city': 'City',
    #                          'state': 'ST',
    #                          'country': 'US',
    #                          'zip_code': '11000',
    #                          'street_addr2': None}]},
    #     errors={'settings': {'theme': 'bad value: type error, expected str but found bool'},
    #             'phone': "bad value: <lambda>('123456789') should evaluate to True",
    #             'aliases': 'missing required key'})

    # Fail strictly!
    try:
        user_schema({
            'name': 'Bob Barr',
            'email': 'bob@example.com',
            'active': True,
            'settings': {
                'theme': False,
                'extra_setting1': 'val1',
                'extra_setting2': 'val2'
            },
            'phone': '123-456-789',
            'addresses': [
                {'street_addr1': '123 Lane',
                 'city': 'City',
                 'state': 'ST',
                 'country': 'US',
                 'zip_code': '11000'}
            ]
        }, strict=True)
    except SchemaError as exc:
        print(exc)
        # Schema validation failed: \ 
        # {'settings': {'theme': 'bad value: type error, expected str but found bool'}, \ 
        # 'phone': "bad value: <lambda>('123456789') should evaluate to True", \
        # 'aliases': 'missing required key'}

    # Pass!
    result = user_schema({
        'name': 'Bob Barr',
        'email': 'bob@example.com',
        'active': True,
        'settings': {
            'theme': 'dark',
            'extra_setting1': 'val1',
            'extra_setting2': 'val2'
        },
        'phone': '123-456-7890',
        'aliases': [],
        'addresses': [
            {'street_addr1': '123 Lane',
             'city': 'City',
             'state': 'ST',
             'country': 'US',
             'zip_code': '11000'}
        ]
    })

    print(result)
    # SchemaResult(
    #     data={'name': 'Bob Barr',
    #           'email': 'bob@example.com',
    #           'active': True,
    #           'settings': {'theme': 'dark',
    #                        'extra_setting1': 'val1',
    #                        'extra_setting2': 'val2',
    #                        'language': 'en'},
    #           'phone': '1234567890',
    #           'aliases': [],
    #           'addresses': [{'street_addr1': '123 Lane',
    #                          'city': 'City',
    #                          'state': 'ST',
    #                          'country': 'US',
    #                          'zip_code': '11000',
    #                          'street_addr2': None}]},
    #     errors={})


For more details, please see the full documentation at https://schemable.readthedocs.io.


.. |version| image:: https://img.shields.io/pypi/v/schemable.svg?style=flat-square
    :target: https://pypi.python.org/pypi/schemable/

.. |travis| image:: https://img.shields.io/travis/dgilland/schemable/master.svg?style=flat-square
    :target: https://travis-ci.org/dgilland/schemable

.. |coveralls| image:: https://img.shields.io/coveralls/dgilland/schemable/master.svg?style=flat-square
    :target: https://coveralls.io/r/dgilland/schemable

.. |license| image:: https://img.shields.io/pypi/l/schemable.svg?style=flat-square
    :target: https://pypi.python.org/pypi/schemable/
