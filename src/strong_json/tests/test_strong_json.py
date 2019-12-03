import math
from datetime import date, datetime
from enum import Enum, IntEnum
from typing import Dict

import numpy as np
import pandas as pd
import pytest
from strong_json import strong_json, ToJsonable, ClassMapBuilder, StrongJson, MissingParameterError, JSONPrimitive, \
    FromJsonable, ClassMapLookUpFailError


class User(ToJsonable):
    def __init__(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name

    def __hash__(self):
        return hash((self.first_name, self.last_name))

    def __eq__(self, other: 'User'):
        return self.first_name == other.first_name and self.last_name == other.last_name

    def __str__(self) -> str:
        return f"{self.first_name}_{self.last_name}"  # pragma: no cover


class SimpleClass:
    def __init__(self, msg: str):
        self.msg = msg


class Color(Enum):
    RED = 'reddd'
    Blue = 'blue'


class Food(IntEnum):
    NOODLES = 1
    RICE = 2


basic_tests = [
    ('hello', 'hello'),
    ([1, 2, 3], [1, 2, 3]),
    (None, None),
    (
        {'a': 'b', 'c': 'd'},
        {
            '__type__': 'dict',
            '__data__': [{'key': 'a', 'value': 'b'}, {'key': 'c', 'value': 'd'}]
        }  # assume treat dict as ordered dict
    ),
    ({}, {}),
    (555, 555),
    (float('nan'), {'__type__': 'float', '__data__': 'nan'}),
    (float('inf'), {'__type__': 'float', '__data__': 'inf'}),
    (float('-inf'), {'__type__': 'float', '__data__': '-inf'}),
    ((1, 2, 3), {'__type__': 'tuple', '__data__': [1, 2, 3]}),
    (date(2019, 8, 23), {'__type__': 'date', 'year': 2019, 'month': 8, 'day': 23}),
    (np.array([1, 2, 3]), {'__type__': 'numpy.ndarray', '__data__': [1, 2, 3]}),
    ({1, 2, 3}, {'__type__': 'set', '__data__': [1, 2, 3]}),
    (datetime(2019, 8, 23, 12, 0, 3), {'__type__': 'datetime',
                                       'year': 2019,
                                       'month': 8,
                                       'day': 23,
                                       'hour': 12,
                                       'minute': 0,
                                       'second': 3,
                                       'microsecond': 0})
]

custom_class_tests = [
    (User('f', 'l'), {'__type__': 'User', 'first_name': 'f', 'last_name': 'l'}),
    (SimpleClass('hello'), {'__type__': 'SimpleClass', 'msg': 'hello'}),
]

non_standard_dict_tests = [
    (
        {User('f', 'l'): 1, User('a', 'b'): 2},
        {
            '__type__': 'dict',
            '__data__': [
                {
                    'key': {'__type__': 'User', 'first_name': 'f', 'last_name': 'l'},
                    'value': 1
                },
                {
                    'key': {'__type__': 'User', 'first_name': 'a', 'last_name': 'b'},
                    'value': 2
                },
            ]
        }
    )
]

enum_test = [
    (Color.RED, {'__type__': 'Color', '__data__': 'RED'}),
    (Food.NOODLES, {'__type__': 'Food', '__data__': 'NOODLES'})
]

all_encoder_tests = basic_tests + custom_class_tests + non_standard_dict_tests + enum_test


@pytest.mark.parametrize("test_input,expected", all_encoder_tests)
def test_to_json_dict(test_input, expected):
    got = strong_json.to_json_dict(test_input)
    assert got == expected


def test_convert_nan():
    got = strong_json.from_json_dict({'__type__': 'float', '__data__': 'nan'})
    assert math.isnan(got)


def test_convert_inf():
    got = strong_json.from_json_dict({'__type__': 'float', '__data__': 'inf'})
    assert math.isinf(got) and got > 0


def test_convert_neg_inf():
    got = strong_json.from_json_dict({'__type__': 'float', '__data__': '-inf'})
    assert math.isinf(got) and got < 0


simple_decoder_tests = [
    ('hello', 'hello'),
    (123, 123),
    (123.0, 123.0),
    (True, True),
    (False, False),
    ([1, 2, 3], [1, 2, 3]),
    (
        {'__type__': 'tuple', '__data__': [1, 2, 3]},
        tuple([1, 2, 3])
    ),
    (
        {'a': 'b', 'c': 'd'},
        {'a': 'b', 'c': 'd'},
    ),
    ({}, {}),
    (
        {
            '__type__': 'dict',
            '__data__': [{'key': 'a', 'value': 'b'}, {'key': 'c', 'value': 'd'}]
        },
        {'a': 'b', 'c': 'd'}
    ),
    (None, None),
    (
        {'__type__': 'set', '__data__': [1, 2, 3]},
        {1, 2, 3}
    ),
    (
        {'__type__': 'date', 'year': 2019, 'month': 8, 'day': 23},
        date(2019, 8, 23)
    ),
    (
        {'__type__': 'datetime', 'year': 2019, 'month': 8, 'day': 23, 'hour': 12, 'minute': 34, 'second': 56,
         'microsecond': 0},
        datetime(2019, 8, 23, 12, 34, 56, 0)
    )
]

enum_decoder_tests = [
    (
        {'__type__': 'Color', '__data__': 'RED'},
        Color.RED
    ),
    (
        {'__type__': 'Food', '__data__': 'RICE'},
        Food.RICE
    )
]

class_decoder_tests = [
    (
        {'__type__': 'User', 'first_name': 'f', 'last_name': 'l'},
        User('f', 'l')
    )
]

complex_dict_tests = [
    (
        {
            '__type__': 'dict',
            '__data__': [
                {
                    'key': {'__type__': 'User', 'first_name': 'f', 'last_name': 'l'},
                    'value': 'f'
                },
                {
                    'key': {'__type__': 'User', 'first_name': 'a', 'last_name': 'b'},
                    'value': 'a'
                },
            ]
        },
        {User('f', 'l'): 'f', User('a', 'b'): 'a'}
    )
]

all_decoder_tests = simple_decoder_tests + \
                    enum_decoder_tests + \
                    class_decoder_tests + \
                    complex_dict_tests


@pytest.mark.parametrize('test_input, expected', all_decoder_tests)
def test_from_json_dict(test_input, expected):
    class_map = ClassMapBuilder.build_class_map([
        Color, Food, User
    ])
    custom_json = StrongJson(class_map=class_map)
    got = custom_json.from_json_dict(test_input)
    assert got == expected


def test_pandas_decode():
    s = {'__type__': 'pandas.DataFrame', '__data__': {'__type__': 'dict', '__data__': [
        {'key': 'a', 'value': {'__type__': 'dict', '__data__': [{'key': 0, 'value': 1}, {'key': 1, 'value': 2}]}},
        {'key': 'b', 'value': {'__type__': 'dict', '__data__': [{'key': 0, 'value': 3}, {'key': 1, 'value': 4}]}}]}}
    got = strong_json.from_json_dict(s)

    expected = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    assert got.equals(expected)


def test_pandas_encode():
    s = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    got = strong_json.to_json_dict(s)

    expected = {'__type__': 'pandas.DataFrame', '__data__': {'__type__': 'dict', '__data__': [
        {'key': 'a', 'value': {'__type__': 'dict', '__data__': [{'key': 0, 'value': 1}, {'key': 1, 'value': 2}]}},
        {'key': 'b', 'value': {'__type__': 'dict', '__data__': [{'key': 0, 'value': 3}, {'key': 1, 'value': 4}]}}]}}

    assert got == expected


def test_numpy_decode():
    from numpy.testing import assert_array_equal
    s = {'__type__': 'numpy.ndarray', '__data__': [1, 2, 3]}
    got = strong_json.from_json_dict(s)
    expected = np.array([1, 2, 3])
    assert_array_equal(got, expected)


def test_dict_equal():
    a = {'a': 1, 'b': {'c': 1}}
    b = {'a': 1, 'b': {'c': 1}}
    c = {'a': 1, 'b': {'c': 3}}
    d = {'a': 1, 'b': {'c': User('f', 'l')}}
    e = {'a': 1, 'b': {'c': User('f', 'l')}}
    f = {User('f', 'l'): 'xxx'}
    g = {User('f', 'l'): 'xxx'}
    assert a == b
    assert a != c
    assert d == e
    assert f == g


def test_to_json():
    got = strong_json.to_json({'a': 'b', 'c': 'd'}, indent=2)
    expected = """{
  "__type__": "dict",
  "__data__": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    }
  ]
}"""
    assert got == expected


def test_from_json():
    raw = """{
      "__type__": "dict",
      "__data__": [
        {
          "key": "a",
          "value": "b"
        },
        {
          "key": "c",
          "value": "d"
        }
      ]
    }"""
    d = strong_json.from_json(raw)
    assert d == {'a': 'b', 'c': 'd'}


def test_treat_as_normal_dict():
    jsoner = StrongJson(class_map={}, treat_dict_as_ordered_dict=False)
    got = jsoner.to_json_dict({'a': 'b', 'c': 'd'})
    expected = {'a': 'b', 'c': 'd'}
    assert got == expected


def test_is_subclass():
    assert issubclass(User, ToJsonable)


def test_missing_param():
    class BadUser(ToJsonable):
        def __init__(self, first: str, last: str):
            self.first = first  # pragma: no cover
            self.last = last  # pragma: no cover

    with pytest.raises(MissingParameterError):
        jsoner = StrongJson({'BadUser': BadUser})
        jsoner.from_json_dict({'__type__': 'BadUser', 'first': 'hello'})


def test_optional_param():
    class BadUser(ToJsonable):
        def __init__(self, first: str, last: str = 'default last'):
            self.first = first
            self.last = last

        def __eq__(self, other: 'BadUser'):
            return self.first == other.first and self.last == other.last

    jsoner = StrongJson({'BadUser': BadUser})
    got = jsoner.from_json_dict({'__type__': 'BadUser', 'first': 'hello'})
    expected = BadUser('hello')
    assert got == expected


def test_from_jsonable():
    class BadUser(FromJsonable):
        def __init__(self, first: str, last: str):
            self.first = first
            self.last = last

        @classmethod
        def from_json_dict(cls, d: Dict[str, JSONPrimitive], decoder: StrongJson):
            return BadUser(d['firstname'], d['lastname'])

        def __eq__(self, other: 'BadUser'):
            return self.first == other.first and self.last == other.last

    jsoner = StrongJson({'BadUser': BadUser})
    got = jsoner.from_json_dict({'__type__': 'BadUser',
                                 'firstname': 'hello',
                                 'lastname': 'world'})
    expected = BadUser('hello', 'world')
    assert got == expected


def test_lookup_fail():
    with pytest.raises(ClassMapLookUpFailError):
        got = strong_json.from_json_dict({'__type__': 'BadUser',
                                          'first': 'hello',
                                          'last': 'world'})


def test_to_jsonable_to_json():
    got = User('f', 'l').to_json()
    expected = '{"__type__": "User", "first_name": "f", "last_name": "l"}'
    assert got == expected


def test_from_jsonable_from_json():
    class BadUser(FromJsonable):
        def __init__(self, first: str, last: str):
            self.first = first
            self.last = last

        @classmethod
        def from_json_dict(cls, d: Dict[str, JSONPrimitive], decoder: StrongJson):
            return BadUser(d['first'], d['last'])

        def __eq__(self, other: 'BadUser'):
            return self.first == other.first and self.last == other.last

    s = '{"__type__": "BadUser", "first": "f", "last": "l"}'
    jsoner = StrongJson({'BadUser': BadUser})
    got = BadUser.from_json(s, jsoner)
    expected = BadUser('f', 'l')
    assert got == expected
