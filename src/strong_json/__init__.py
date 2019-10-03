import math
import warnings
import json
from collections import OrderedDict
from enum import Enum
from typing import List, Any, Type, Dict
import inspect
from datetime import date, datetime

ClassMap = Dict[str, Type[Any]]


class StrongJson:
    def __init__(self,
                 type_key: str = '__type__',
                 data_key: str = '__data__',
                 treat_dict_as_ordered_dict: bool = True):
        self.type_key = type_key
        self.data_key = data_key
        self.treat_dict_as_ordered_dict = treat_dict_as_ordered_dict

    def to_json(self, obj: Any, **kwd) -> str:
        d = self.to_json_dict(obj)
        return json.dumps(d, **kwd)

    def from_json(self, s: str, class_map: ClassMap, **kwd) -> Any:
        d = json.loads(s, **kwd)
        return self.from_json_dict(d, class_map)

    def from_json_dict(self, d: Dict[str, Any], class_map: ClassMap):
        """override this for custom type"""
        return self.default_from_json_dict(d, class_map)

    def to_json_dict(self, v: Any) -> Any:
        return self.default_to_json_dict(v)

    def default_from_json_dict(self, d: Dict[str, Any], class_map: ClassMap) -> Any:
        type_key = self.type_key
        data_key = self.data_key

        if isinstance(d, dict):
            if type_key not in d:
                # assume string key dict
                return {k: self.from_json_dict(v, class_map) for k, v in d.items()}
            elif d[type_key] in class_map:
                obj_class = class_map[d[type_key]]
                if issubclass(obj_class, FromJsonable):
                    return obj_class.from_json_dict(d, class_map, self)
                elif issubclass(obj_class, Enum):
                    data = d[data_key]
                    return obj_class[data]  # trust me not pycharm
                else:
                    param = {a for a in inspect.signature(obj_class).parameters}
                    bad_keys = [p for p in param if p not in d]
                    if bad_keys:
                        warnings.warn('Param not found : %r' % (bad_keys,))
                    tmp = {k: self.from_json_dict(v, class_map) for k, v in d.items() if k != type_key and k in param}
                    return obj_class(**tmp)
            elif d[type_key] == 'dict':  # dict with non str key
                data = d[data_key]
                return {self.from_json_dict(item['key'], class_map): self.from_json_dict(item['value'], class_map) for
                        item in data}
            elif d[type_key] == 'tuple':
                data = d[data_key]
                return tuple([self.from_json_dict(item, class_map) for item in data])
            elif d[type_key] == 'date':
                data = d[data_key]
                return date(**data)
            elif d[type_key] == 'datetime':
                data = d[data_key]
                return datetime(**data)
            else:
                raise ValueError('Type not found for key %s' % d[type_key])
        elif isinstance(d, list):
            return [self.from_json_dict(item, class_map) for item in d]
        elif isinstance(d, (int, str, float)):
            return d
        elif d is None:
            return d
        else:
            raise NotImplementedError('Unknown type parse %s, %r' % (type(d), d))

    def default_to_json_dict(self, v: Any) -> Any:
        """Convert object v to json friendly dict/any
        Args:
            v (Any): object to convert to json dict
        Returns:
            Any (Dict unless it's primitive like List, int, float, boolean, str.)
        """
        type_key = self.type_key
        data_key = self.data_key
        if isinstance(v, ToJsonable):
            return v.to_json_dict(encoder=self)
        elif isinstance(v, (dict, OrderedDict)) and len(v) != 0:
            if self.treat_dict_as_ordered_dict or \
                    isinstance(v, OrderedDict) or \
                    not isinstance(next(iter(v.keys())), str):  # non str key normal dict
                return {
                    type_key: 'dict',
                    data_key: [{'key': self.to_json_dict(kv), 'value': self.to_json_dict(vv)} for kv, vv in v.items()]
                }
            else:  # assume str key
                return {kv: self.to_json_dict(vv) for kv, vv in v.items()}
        elif isinstance(v, Enum):
            return {
                type_key: v.__class__.__name__,
                data_key: v.name
            }
        elif isinstance(v, tuple):
            return {
                type_key: 'tuple',
                data_key: [self.to_json_dict(vv) for vv in v]
            }
        elif isinstance(v, date):
            return {
                type_key: 'date',
                data_key: {'year': v.year, 'month': v.month, 'day': v.day}
            }
        elif isinstance(v, datetime):
            return {
                type_key: 'datetime',
                data_key: {
                    'year': v.year,
                    'month': v.month,
                    'day': v.day,
                    'hour': v.hour,
                    'minute': v.minute,
                    'second': v.second,
                    'microsecond': v.microsecond
                }
            }
        elif isinstance(v, list):
            return [self.to_json_dict(vv) for vv in v]
        else:
            return v


strong_json = StrongJson()


class FromJsonable:
    @classmethod
    def from_json_dict(cls, d: Dict, class_map: Dict[str, Type[Any]], decoder: 'StrongJson'):
        raise NotImplementedError()


class ToJsonable:

    def to_json_dict(self, encoder: 'StrongJson') -> Dict[str, Any]:
        tmp = {'__type__': self.__class__.__qualname__}
        for k, v in self.__dict__.items():
            if k not in {'__objclass__', }:
                tmp[k] = encoder.to_json_dict(v)
        return tmp

    def to_json(self, encoder=strong_json, **kwd) -> str:
        return json.dumps(self.to_json_dict(encoder), **kwd)


# class JsonableEnum(ToJsonable, FromJsonable, Enum):
#     @classmethod
#     def from_json_dict(cls, d: Dict, class_map: Dict[str, Type[Any]], decoder: 'StrongJson'):
#         data = d[decoder.data_key]
#         return cls[data]
#
#     def to_json_dict(self, encoder: 'StrongJson') -> Dict[str, Any]:
#         return {
#             encoder.type_key: self.__class__.__name__,
#             encoder.data_key: self.name
#         }


class ClassMapBuilder:
    @classmethod
    def build_class_map(cls, classes: List[Type[Any]]) -> ClassMap:
        return {cls.__name__: cls for cls in classes}


class User(ToJsonable):
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def __hash__(self):
        return hash((self.first_name, self.last_name))
