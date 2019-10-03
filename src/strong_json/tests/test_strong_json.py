import math

import pytest
from strong_json import strong_json, ToJsonable, ClassMapBuilder
from datetime import date
from enum import Enum, IntEnum


class User(ToJsonable):
    def __init__(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name

    def __hash__(self):
        return hash((self.first_name, self.last_name))

    def __eq__(self, other: 'User'):
        return self.first_name == other.first_name and self.last_name == other.last_name

    def __str__(self) -> str:
        return f"{self.first_name}_{self.last_name}"


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
    (555, 555),
    ((1, 2, 3), {'__type__': 'tuple', '__data__': [1, 2, 3]}),
    (date(2019, 8, 23), {'__type__': 'date', '__data__': {'year': 2019, 'month': 8, 'day': 23}})
]

custom_class_tests = [
    (User('f', 'l'), {'__type__': 'User', 'first_name': 'f', 'last_name': 'l'})
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
    got = strong_json.to_json_dict(float('nan'))
    assert math.isnan(got)


simple_decoder_tests = [
    ('hello', 'hello'),
    (123, 123),
    (123.0, 123.0),
    ([1, 2, 3], [1, 2, 3]),
    (
        {'__type__': 'tuple', '__data__': [1, 2, 3]},
        tuple([1, 2, 3])
    ),
    (
        {'a': 'b', 'c': 'd'},
        {'a': 'b', 'c': 'd'},
    ),
    (
        {
            '__type__': 'dict',
            '__data__': [{'key': 'a', 'value': 'b'}, {'key': 'c', 'value': 'd'}]
        },
        {'a': 'b', 'c': 'd'}
    ),
    (None, None)
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
    got = strong_json.from_json_dict(test_input, class_map)
    assert got == expected


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


def test_is_subclass():
    assert issubclass(User, ToJsonable)
