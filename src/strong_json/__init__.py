import warnings
import json
from collections import OrderedDict
from enum import Enum
from typing import List, Any, Type, Dict, Union
import inspect
from datetime import date, datetime

ClassMap = Dict[str, Type[Any]]
JSONPrimitive = Union[Dict[str, 'JSONPrimitive'], List['JSONPrimitive'], int, float, None, str]


class ClassMapLookUpFailWarning(Warning):
    pass
    pass


class ClassMapLookUpFailError(Exception):
    pass


class StrongJson:
    def __init__(self,
                 class_map: ClassMap,
                 type_key: str = '__type__',
                 data_key: str = '__data__',
                 treat_dict_as_ordered_dict: bool = True):
        """

        Args:
            class_map (ClassMap): Dictionary from string to Class
            type_key (str): Optional Default '__type__'.
            data_key (str): Optional Default '__data__'.
            treat_dict_as_ordered_dict (bool): Optional Default True.
                treat all dictionary as ordered dict(python 3.7)
        """
        self.class_map = class_map
        self.type_key = type_key
        self.data_key = data_key
        self.treat_dict_as_ordered_dict = treat_dict_as_ordered_dict

    def to_json(self, obj: Any, **kwd) -> str:
        """ Convert object to json string

        Args:
            obj (Any): object
            **kwd (): keyword arguments will be passed down to json.dumps

        Returns:
            str. Json String.

        """
        d = self.to_json_dict(obj)
        return json.dumps(d, **kwd)

    def from_json(self, s: str, **kwd) -> Any:
        """ Construct object from json string.

        Args:
            s (str): json string
            **kwd (): The rest of keyword arguments will be passed down to json.loads

        Returns:
            Any. Object constructed from json string.
        """
        d = json.loads(s, **kwd)
        return self.from_json_dict(d)

    def from_json_dict(self, d: JSONPrimitive) -> Any:
        """Construct object from json dictionary.
        This is the place to override if you want to add custom class.

        Args:
            d (JSONPrimitive): JSONPrimitive. Ex: dict.

        Returns:
            Any
        """

        return self.default_from_json_dict(d)

    def to_json_dict(self, v: Any) -> JSONPrimitive:
        """Create json dumps friendly object

        Args:
            v (Any): object.

        Returns:
            JSONPrimitive.

        """
        return self.default_to_json_dict(v)

    def default_from_json_dict(self, d: JSONPrimitive) -> Any:
        """Default from json dict. Useful for fallback when override the class.

        Args:
            d (JSONPrimitive): JSONPrimitive. Ex: dict.

        Returns:
            Any. Constructed Object.

        """
        type_key = self.type_key
        data_key = self.data_key

        if isinstance(d, dict):
            if type_key not in d:
                # assume string key dict
                return {k: self.from_json_dict(v) for k, v in d.items()}
            elif d[type_key] in self.class_map:
                obj_class = self.class_map[d[type_key]]
                if issubclass(obj_class, FromJsonable):
                    return obj_class.from_json_dict(d, decoder=self)
                elif issubclass(obj_class, Enum):
                    data = d[data_key]
                    return obj_class[data]  # trust me not pycharm
                else:
                    param = {a for a in inspect.signature(obj_class).parameters}
                    bad_keys = [p for p in param if p not in d]
                    if bad_keys:
                        warnings.warn('Param not found : %r' % (bad_keys,))
                    tmp = {k: self.from_json_dict(v) for k, v in d.items() if k != type_key and k in param}
                    return obj_class(**tmp)
            elif d[type_key] == 'dict':  # dict with non str key
                data = d[data_key]
                return {self.from_json_dict(item['key']): self.from_json_dict(item['value']) for
                        item in data}
            elif d[type_key] == 'tuple':
                data = d[data_key]
                return tuple([self.from_json_dict(item) for item in data])
            elif d[type_key] == 'date':
                return date(**{k: v for k, v in d.items() if k != self.type_key})
            elif d[type_key] == 'datetime':
                return datetime(**{k: v for k, v in d.items() if k != self.type_key})
            elif d[type_key] == 'set':
                data = d[data_key]
                return set(data)
            else:
                raise ClassMapLookUpFailError('Type not found for key %s' % d[type_key])
        elif isinstance(d, list):
            return [self.from_json_dict(item) for item in d]
        elif isinstance(d, (int, str, float)):
            return d
        elif d is None:
            return d
        else:
            raise NotImplementedError('Unknown type parse %s, %r' % (type(d), d))

    def default_to_json_dict(self, v: Any) -> JSONPrimitive:
        """Default Conversion from object v to json friendly JSONPrimitive
        Args:
            v (Any): object to convert to json dict
        Returns:
            JSONPrimitive (Dict unless it's primitive like List, int, float, boolean, str.)
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
                'year': v.year,
                'month': v.month,
                'day': v.day
            }
        elif isinstance(v, datetime):
            return {
                type_key: 'datetime',
                'year': v.year,
                'month': v.month,
                'day': v.day,
                'hour': v.hour,
                'minute': v.minute,
                'second': v.second,
                'microsecond': v.microsecond
            }
        elif isinstance(v, set):
            return {
                type_key: 'set',
                data_key: [self.to_json_dict(x) for x in v]
            }
        elif isinstance(v, list):
            return [self.to_json_dict(vv) for vv in v]
        else:
            return v


"""
Default encoder/decoder
"""
strong_json = StrongJson(class_map={})


class FromJsonable:
    """
    Interface for class that can be constructed from json
    """

    @classmethod
    def from_json_dict(cls, d: Dict[str, JSONPrimitive], decoder: StrongJson):
        """
        Construct object from dict
        Args:
            d (Dict[str, JSONPrimitive]): json dict
            decoder (StrongJson): decoder

        Returns:
            Object of this class.
        """
        raise NotImplementedError()

    @classmethod
    def from_json(cls, s: str, decoder: StrongJson = strong_json, **kwd):
        """Construct object from json string

        Args:
            s (str): json str
            decoder (StrongJson):
            **kwd (): the rest of keyword arguments are passed down to json.loads

        Returns:
            Object of this class.

        """
        d = json.loads(s, **kwd)
        return cls.from_json_dict(d, decoder)


class ToJsonable:

    def to_json_dict(self, encoder: StrongJson) -> Dict[str, JSONPrimitive]:
        """Convert object to json friendly dict.

        Args:
            encoder (StrongJson): encoder

        Returns:
            Dict[str, JSONPrimitive]

        """
        cls_name = self.__class__.__qualname__
        if cls_name not in encoder.class_map:
            warnings.warn(
                f"{cls_name} not found in class map. You will not be able to convert this back.",
                ClassMapLookUpFailWarning)
        tmp = {'__type__': self.__class__.__qualname__}
        for k, v in self.__dict__.items():
            if k not in {'__objclass__', }:
                tmp[k] = encoder.to_json_dict(v)
        return tmp

    def to_json(self, encoder: StrongJson = strong_json, **kwd) -> str:
        """Convert this object to json string.

        Args:
            encoder (StrongJson): encoder
            **kwd : keyword argument will be passed down to json.dumps

        Returns:
            str. Json string
        """
        return json.dumps(self.to_json_dict(encoder), **kwd)


class ClassMapBuilder:
    @classmethod
    def build_class_map(cls, classes: List[Type[Any]]) -> ClassMap:
        """Build class map dictionary from list of class
        Args:
            classes (List[Type[Any]]): list of classes

        Returns:
            ClassMap
        """
        return {cls.__name__: cls for cls in classes}
