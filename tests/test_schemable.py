
from collections import OrderedDict

import pytest

from schemable import (
    ALLOW_EXTRA,
    DENY_EXTRA,
    All,
    Any,
    As,
    Dict,
    List,
    Optional,
    Schema,
    SchemaError,
    Select,
    Type,
    Use,
    Validate
)

parametrize = pytest.mark.parametrize


def assert_schema_case(case):
    schema = Schema(case['schema'], **case.get('schema_opts', {}))
    result = schema(case['data'])

    assert result.data == case['expected_data']
    assert result.errors == case['expected_errors']


@parametrize('case', [
    dict(
        schema=1,
        data=2,
        expected_data=None,
        expected_errors='value error, expected 1 but found 2'
    ),
    dict(
        schema=5,
        data='a',
        expected_data=None,
        expected_errors="value error, expected 5 but found 'a'"
    ),
])
def test_value(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema=str,
        data='a',
        expected_data='a',
        expected_errors=None
    ),
    dict(
        schema=str,
        data=str,
        expected_data=None,
        expected_errors='type error, expected str but found type'
    ),
    dict(
        schema=str,
        data=1,
        expected_data=None,
        expected_errors='type error, expected str but found int'
    ),
    dict(
        schema=str,
        data=1,
        expected_data=None,
        expected_errors="type error, expected str but found int"
    ),
])
def test_type(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema=[str],
        data=[1, 2, 'a'],
        expected_data=['a'],
        expected_errors={
            0: 'bad value: type error, expected str but found int',
            1: 'bad value: type error, expected str but found int'
        }
    ),
    dict(
        schema=[str],
        data=[1, 2, 3],
        expected_data=None,
        expected_errors={
            0: 'bad value: type error, expected str but found int',
            1: 'bad value: type error, expected str but found int',
            2: 'bad value: type error, expected str but found int'
        }
    ),
    dict(
        schema=[None],
        data=[None],
        expected_data=[],
        expected_errors={}
    ),
    dict(
        schema=[{
            str: {
                'a': int,
                'b': bool,
                'c': [{int: str}]
            }
        }],
        data=[
            {'x': {
                'a': 1,
                'b': True,
                'c': [{1: '1'}, {2: '2'}, {3: '3'}]
            }},
            {'y': [1]},
            {'z': {
                'a': '1',
                'b': None,
                'c': [{1: '1'}, {'2': 2}, {3: '3'}]
            }}
        ],
        expected_data=[
            {'x': {
                'a': 1,
                'b': True,
                'c': [{1: '1'}, {2: '2'}, {3: '3'}]
            }},
            {'z': {
                'c': [{1: '1'}, {3: '3'}]
            }}
        ],
        expected_errors={
            1: {
                'y': 'bad value: type error, expected Mapping but found list'
            },
            2: {
                'z': {
                    'a': 'bad value: type error, expected int but found str',
                    'b': ('bad value: type error, '
                          'expected bool but found NoneType'),
                    'c': {1: {int: 'missing required key'}}
                }
            }
        }
    ),
    dict(
        schema=[list],
        data=[[1], []],
        expected_data=[[1], []],
        expected_errors={}
    ),
    dict(
        schema=[list, len],
        data=[[1], []],
        expected_data=[[1]],
        expected_errors={1: 'bad value: len([]) should evaluate to True'}
    ),
])
def test_list(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema={'a': list},
        data={'a': [1, 2, 3, 4]},
        expected_data={'a': [1, 2, 3, 4]},
        expected_errors={}
    ),
    dict(
        schema={'a': 1},
        data={'a': 1, 'b': 2},
        expected_data={'a': 1},
        expected_errors={}
    ),
    dict(
        schema={'a': []},
        data={'a': [1, 2, {}]},
        expected_data={'a': [1, 2, {}]},
        expected_errors={}
    ),
    dict(
        schema={'a': []},
        data={'a': []},
        expected_data={'a': []},
        expected_errors={}
    ),
    dict(
        schema={'a': {}},
        data={'a': {}},
        expected_data={'a': {}},
        expected_errors={}
    ),
    dict(
        schema={'a': str},
        data={},
        expected_data=None,
        expected_errors={'a': 'missing required key'}
    ),
    dict(
        schema={'a': 1},
        data=OrderedDict([('a', 1)]),
        expected_data=OrderedDict([('a', 1)]),
        expected_errors={}
    ),
    dict(
        schema={'a': 2},
        data={'a': 1},
        expected_data=None,
        expected_errors={'a': 'bad value: value error, expected 2 but found 1'}
    ),
    dict(
        schema={
            (str, int): str,
            (bool, float): int
        },
        data={
            'a': 'a',
            2: '2',
            True: 1,
            1.5: 2
        },
        expected_data={
            'a': 'a',
            2: '2',
            True: 1,
            1.5: 2
        },
        expected_errors={}
    ),
    dict(
        schema={str: (str, int, bool)},
        data={
            'x': 'a',
            'y': 1,
            'z': True,
            'm': None
        },
        expected_data={
            'x': 'a',
            'y': 1,
            'z': True
        },
        expected_errors={'m': ('bad value: type error, expected '
                               'bool or int or str but found NoneType')}
    ),
    dict(
        schema={
            str: {
                'a': int,
                'b': bool,
                'c': [{int: str}]
            }
        },
        data={
            'x': {
                'a': 1,
                'b': True,
                'c': [{1: '1'}, {2: '2'}, {3: '3'}]
            },
            'y': [1],
            'z': {
                'a': '1',
                'b': None,
                'c': [{1: '1'}, {'2': 2}, {3: '3'}]
            }
        },
        expected_data={
            'x': {
                'a': 1,
                'b': True,
                'c': [{1: '1'}, {2: '2'}, {3: '3'}]
            },
            'z': {
                'c': [{1: '1'}, {3: '3'}]
            }
        },
        expected_errors={
            'y': 'bad value: type error, expected Mapping but found list',
            'z': {
                'a': 'bad value: type error, expected int but found str',
                'b': 'bad value: type error, expected bool but found NoneType',
                'c': {1: {int: 'missing required key'}}
            }
        }
    ),
    dict(
        schema={str: [{str: str, int: int}]},
        data={'x': [{10: 20, 'a': 'b', (1,): (2,)}]},
        expected_data={'x': [{10: 20, 'a': 'b'}]},
        expected_errors={}
    ),
    dict(
        schema={
            'a': {
                'b': {
                    str: {
                        'c': str,
                        object: object
                    }
                }
            }
        },
        data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd',
                        5: None,
                        'ee': set()
                    }
                }
            }
        },
        expected_data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd',
                        5: None,
                        'ee': set()
                    }
                }
            }
        },
        expected_errors={}
    ),
    dict(
        schema={
            'a': {
                'b': {
                    str: {
                        'c': str
                    }
                }
            }
        },
        data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd',
                        5: None,
                        'ee': set()
                    }
                }
            }
        },
        expected_data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd'
                    }
                }
            }
        },
        expected_errors={}
    ),
    dict(
        schema={object: object},
        data={'a': 1, 'b': True},
        expected_data={'a': 1, 'b': True},
        expected_errors={}
    ),
    dict(
        schema={'a': int, object: object},
        data={'a': 1, 'b': True},
        expected_data={'a': 1, 'b': True},
        expected_errors={}
    ),
    dict(
        schema={object: str},
        data={'a': 'x'},
        expected_data={'a': 'x'},
        expected_errors={}
    ),
    dict(
        schema={int: int},
        data={1: 'a'},
        expected_data=None,
        expected_errors={1: ('bad value: type error, expected int '
                             'but found str')}
    ),
    dict(
        schema={int: int, bool: bool},
        data={1: 'a'},
        expected_data=None,
        expected_errors={
            bool: "missing required key",
            1: "bad value: type error, expected int but found str"
        }
    ),
    dict(
        schema={'a': int, str: str},
        data={'a': 'b'},
        expected_data=None,
        expected_errors={
            'a': "bad value: type error, expected int but found str",
            str: "missing required key"
        }
    ),
    dict(
        schema={str: str},
        data={},
        expected_data=None,
        expected_errors={str: "missing required key"}
    ),
    dict(
        schema={
            str: [{
                str: [{str: (str, int)}]
            }]
        },
        data={
            'x1': [{
                'x2': [{'x3': 'a'}, {'x4': 1}, {'x5': False}],
                'x6': [5],
                'x7': {'y': 'z'}
            }],
            'x8': {}
        },
        expected_data={
            'x1': [{
                'x2': [{'x3': 'a'}, {'x4': 1}, {'x5': False}]
            }]
        },
        expected_errors={
            'x1': {0: {
                'x6': {0: ('bad value: type error, expected Mapping '
                           'but found int')},
                'x7': 'bad value: type error, expected list but found dict'
            }},
            'x8': 'bad value: type error, expected list but found dict'
        }
    ),
    dict(
        schema={'a': []},
        data={'a': {}},
        expected_data=None,
        expected_errors={'a': ('bad value: type error, expected list '
                               'but found dict')}
    ),
    dict(
        schema={'a': {}},
        data={'a': []},
        expected_data=None,
        expected_errors={
            'a': 'bad value: type error, expected Mapping but found list'
        }
    ),
    dict(
        schema={'a': str},
        data={},
        expected_data=None,
        expected_errors={'a': 'missing required key'}
    ),
    dict(
        schema={'a': str, str: str},
        data={'b': 'c'},
        expected_data={'b': 'c'},
        expected_errors={'a': 'missing required key'}
    ),
])
def test_dict(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema={'a': {}},
        schema_opts={'extra': ALLOW_EXTRA},
        data={'a': {'b': 1, 'c': True}},
        expected_data={'a': {'b': 1, 'c': True}},
        expected_errors={}
    ),
    dict(
        schema={
            'a': {
                'b': {
                    str: {
                        'c': str
                    }
                }
            }
        },
        schema_opts={'extra': ALLOW_EXTRA},
        data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd',
                        5: None, 'ee': set()
                    }
                },
                'f': 5
            }
        },
        expected_data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd',
                        5: None,
                        'ee': set()
                    }
                },
                'f': 5
            }
        },
        expected_errors={}
    ),
    dict(
        schema={str: str},
        schema_opts={'extra': DENY_EXTRA},
        data={1: 'a'},
        expected_data=None,
        expected_errors={
            str: "missing required key",
            1: "bad key: not in [<class 'str'>]"
        }
    ),
    dict(
        schema={str: str, bool: bool},
        schema_opts={'extra': DENY_EXTRA},
        data={1: 'a'},
        expected_data=None,
        expected_errors={
            str: "missing required key",
            bool: "missing required key",
            1: "bad key: not in [<class 'bool'>, <class 'str'>]"
        }
    ),
    dict(
        schema={'a': 1},
        schema_opts={'extra': DENY_EXTRA},
        data={'b': 2},
        expected_data=None,
        expected_errors={
            'a': "missing required key",
            'b': "bad key: not in ['a']"
        }
    ),
    dict(
        schema={'a': 1, int: str},
        schema_opts={'extra': DENY_EXTRA},
        data={'b': 2},
        expected_data=None,
        expected_errors={
            'a': "missing required key",
            int: "missing required key",
            'b': "bad key: not in ['a', <class 'int'>]"
        }
    ),
    dict(
        schema={'a': {}},
        schema_opts={'extra': DENY_EXTRA},
        data={'a': {'b': 1, 'c': True}},
        expected_data=None,
        expected_errors={
            'a': {
                'b': 'bad key: not in []',
                'c': 'bad key: not in []'
            }
        }
    ),
])
def test_dict_extra(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema=OrderedDict([
            ('a', int),
            (str, str)
        ]),
        data={'a': 1, 'b': 'c'},
        expected_data={'a': 1, 'b': 'c'},
        expected_errors={}
    ),
    dict(
        schema=OrderedDict([
            ('a', int),
            (str, str)
        ]),
        data={'a': 'd', 'b': 'c'},
        expected_data={'b': 'c'},
        expected_errors={'a': ('bad value: type error, '
                               'expected int but found str')}
    ),
    dict(
        schema=OrderedDict([
            (str, str),
            ((str, int), int),
            ((int, str), bool),
            ((float, str), float)
        ]),
        data={
            'str': 'a',
            '(str, int)': 1,
            '(int, str)': True,
            '(float, str)': 2.5
        },
        expected_data={
            'str': 'a',
            '(str, int)': 1,
            '(int, str)': True,
            '(float, str)': 2.5
        },
        expected_errors={}
    ),
    dict(
        schema=OrderedDict([
            (str, str),
            ((str, int), int),
            ((int, str), bool),
            ((float, str), float)
        ]),
        data={'str': None},
        expected_data=None,
        expected_errors={'str': ('bad value: type error, '
                                 'expected float but found NoneType')}
    ),
    dict(
        schema=OrderedDict([
            ((str, int), int),
            ((int, str), bool),
            ((float, str), float),
            (str, {'a': int})
        ]),
        data={'str': {}},
        expected_data=None,
        expected_errors={'str': {'a': 'missing required key'}}
    ),
])
def test_dict_resolution_order(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema={Optional('x'): int, str: str},
        data={'x': 5, 'y': 'a'},
        expected_data={'x': 5, 'y': 'a'},
        expected_errors={}
    ),
    dict(
        schema={Optional('x', default=5): int},
        data={},
        expected_data={'x': 5},
        expected_errors={}
    ),
    dict(
        schema={Optional('x', default=lambda: 5): int},
        data={},
        expected_data={'x': 5},
        expected_errors={}
    ),
    dict(
        schema={Optional(object): object},
        data={},
        expected_data={},
        expected_errors={}
    ),
    dict(
        schema={'a': {Optional(object): object}},
        data={'a': {}},
        expected_data={'a': {}},
        expected_errors={}
    ),
    dict(
        schema={Optional(object): str},
        data={'a': 'x'},
        expected_data={'a': 'x'},
        expected_errors={}
    ),
])
def test_optional(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema=As(int),
        data='1',
        expected_data=1,
        expected_errors=None
    ),
    dict(
        schema=As(As(int)),
        data='1',
        expected_data=1,
        expected_errors=None
    ),
    dict(
        schema=As(int),
        data='a',
        expected_data=None,
        expected_errors=("int('a') should not raise an exception: ValueError: "
                         "invalid literal for int() with base 10: 'a'")
    ),
])
def test_as(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema=Select('a'),
        data={'a': 5},
        expected_data=5,
        expected_errors=None
    ),
    dict(
        schema=Select(lambda obj: obj['a']),
        data={'a': 5},
        expected_data=5,
        expected_errors=None
    ),
    dict(
        schema=Select('a', lambda a: a * 2),
        data={'a': 5},
        expected_data=10,
        expected_errors=None
    ),
    dict(
        schema=Select(1),
        data={1: 5},
        expected_data=5,
        expected_errors=None
    ),
    dict(
        schema={
            'a': Select('a'),
            'aa': Select('a'),
            'aaa': Select(lambda obj: obj['a'] + obj['b']),
            'aaaa': Select('a', lambda a: a)
        },
        data={'a': 5, 'b': 10},
        expected_data={
            'a': 5,
            'aa': 5,
            'aaa': 15,
            'aaaa': 5
        },
        expected_errors={}
    ),
    dict(
        schema=Select('a'),
        data=[],
        expected_data=None,
        expected_errors='type error, expected Mapping but found list'
    ),
    dict(
        schema={
            'a': Select('a'),
            'aa': Select('a'),
            'aaa': Select(lambda obj: obj['a'] + obj['b']),
            'aaaa': Select('a', lambda a: a)
        },
        data={'b': 10},
        expected_data=None,
        expected_errors={
            'a': ("bad value: itemgetter({'b': 10}) should not raise an "
                  "exception: KeyError: 'a'"),
            'aa': ("bad value: itemgetter({'b': 10}) should not raise an "
                   "exception: KeyError: 'a'"),
            'aaa': ("bad value: <lambda>({'b': 10}) should not raise an "
                    "exception: KeyError: 'a'"),
            'aaaa': ("bad value: itemgetter({'b': 10}) should not raise an "
                     "exception: KeyError: 'a'"),
        }
    ),
])
def test_select(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema=Use(5),
        data=10,
        expected_data=5,
        expected_errors=None
    ),
    dict(
        schema=Use(lambda: 5),
        data=10,
        expected_data=5,
        expected_errors=None
    ),
    dict(
        schema={'a': Use('b')},
        data={},
        expected_data={'a': 'b'},
        expected_errors={}
    ),
    dict(
        schema={'a': Use(dict)},
        data={},
        expected_data={'a': {}},
        expected_errors={}
    ),
])
def test_use(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema=Validate(int),
        data='a',
        expected_data=None,
        expected_errors="invalid literal for int() with base 10: 'a'"
    ),
])
def test_validate(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema={'x': All(int, lambda n: n < 10, As(str))},
        data={'x': 5},
        expected_data={'x': '5'},
        expected_errors={}
    ),
    dict(
        schema={'x': All(As(int), lambda n: n < 10)},
        data={'x': '5'},
        expected_data={'x': 5},
        expected_errors={}
    ),
    dict(
        schema={'x': All(Validate(int), str)},
        data={'x': '5'},
        expected_data={'x': '5'},
        expected_errors={}
    ),
    dict(
        schema=All(int, lambda n: n > 10),
        data=5,
        expected_data=None,
        expected_errors='<lambda>(5) should evaluate to True'
    ),
])
def test_all(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema={'x': Any(lambda x: x < 10, lambda x: x > 5)},
        data={'x': 7},
        expected_data={'x': 7},
        expected_errors={}
    ),
    dict(
        schema={'x': Any(lambda x: x < 10, lambda x: x > 5)},
        data={'x': 15},
        expected_data={'x': 15},
        expected_errors={}
    ),
    dict(
        schema={'x': Any(lambda x: x > 10, lambda x: x > 5)},
        data={'x': 4},
        expected_data=None,
        expected_errors={'x': 'bad value: <lambda>(4) should evaluate to True'}
    ),
])
def test_any(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema={
            'a': Schema({
                'b': Schema({
                    str: Schema({
                        'c': str
                    })
                })
            })
        },
        data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd',
                        5: None,
                        'ee': set()
                    }
                }
            }
        },
        expected_data={
            'a': {
                'b': {
                    'x': {
                        'c': 'd'
                    }
                }
            }
        },
        expected_errors={}
    ),
    dict(
        schema={str: Schema({'a': int, 'b': str}, strict=True)},
        data={
            'x': {'b': '1'},
            'y': {'a': 2, 'b': '2'}
        },
        expected_data={
            'x': {'b': '1'},
            'y': {'a': 2, 'b': '2'}
        },
        expected_errors={'x': {'a': 'missing required key'}}
    ),
])
def test_nested_schema(case):
    assert_schema_case(case)


@parametrize('case', [
    dict(
        schema={},
        data=[],
        expected_data=None,
        expected_errors='type error, expected Mapping but found list'
    ),
    dict(
        schema={'a': int},
        data={'b': 'c'},
        expected_data=None,
        expected_errors={'a': "missing required key"}
    ),
    dict(
        schema={
            str: {
                'a': int,
                str: str
            }
        },
        data={
            'x': {},
            'y': {'b': '1'},
            'z': {'a': 1},
            'm': {'a': 1, 'b': 2},
            'n': {'a': 1, 'b': '3'}
        },
        expected_data={
            'y': {'b': '1'},
            'z': {'a': 1},
            'm': {'a': 1},
            'n': {'a': 1, 'b': '3'}
        },
        expected_errors={
            'x': {'a': "missing required key", str: "missing required key"},
            'y': {'a': "missing required key"},
            'z': {str: "missing required key"},
            'm': {'b': 'bad value: type error, expected str but found int'}
        }
    ),
    dict(
        schema=[{str: str}],
        data=[
            {'a': '1'},
            {'b': 2},
            {'c': 3},
            {'d': '4'}
        ],
        expected_data=[
            {'a': '1'},
            {'d': '4'}
        ],
        expected_errors={
            1: {'b': 'bad value: type error, expected str but found int'},
            2: {'c': 'bad value: type error, expected str but found int'}
        }
    ),
])
def test_strict_exception(case):
    with pytest.raises(SchemaError) as exc_info1:
        Schema(case['schema'], strict=True)(case['data'])

    with pytest.raises(SchemaError) as exc_info2:
        Schema(case['schema'])(case['data'], strict=True)

    exc1 = exc_info1.value
    exc2 = exc_info2.value

    assert exc1.errors == case['expected_errors']
    assert exc1.data == case['expected_data']
    assert exc1.original_data == case['data']

    assert exc2.errors == case['expected_errors']
    assert exc2.data == case['expected_data']
    assert exc2.original_data == case['data']


@parametrize('schema_class, args, exception', [
    (Type, (1,), TypeError),
    (List, ({},), TypeError),
    (Dict, ([],), TypeError),
    (Validate, (1,), TypeError),
    (Select, ('a', 1), TypeError),
    (Select, (None, None), TypeError),
    (As, (1,), TypeError),
    (dict, ((Use('a'), 'a'),), TypeError),
    (dict, ((Select('a'), 'a'),), TypeError),
    (dict, ((As(list), 'a'),), TypeError),
])
def test_invalid_schema(schema_class, args, exception):
    with pytest.raises(exception):
        schema_class(*args)
