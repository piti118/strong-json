# StrongJson
![PyPI](https://img.shields.io/pypi/v/strong_json)
[![Build Status](https://travis-ci.com/piti118/strong-json.svg?branch=master)](https://travis-ci.org/piti118/strong-json)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/piti118/strong_json_notebook/master)


A more faithful python json encoder/decoder.

# Install

```
pip install strong_json
```
or directly from this repository
```
pip install git+git://github.com/piti118/strong-json.git
```

## Features
In addition to the standard json.dumps/loads, this module offer the following additonal behavior.

- Simple interface to allow class to dump to json.
    - ```
      class User(ToJsonable):
          def __init__(self, first, last):
              self.first = first
              self.last = last
      ```
- Preserve type information.
    - ```User('f', 'l')``` -> ```{'__type__': 'User', 'first':'f', 'last':'l'}```
    
    
- More faithful dictionary dumps/loads
    - Treat dictionary as OrderedDictionary when encode. See [Python 3.6 Release Note](https://docs.python.org/3/whatsnew/3.6.html#new-dict-implementation).
        - ```{'a':'b', 'c':'d'}``` ->
            ```
            {
                '__type__':'dict'
                '__data__':[
                    {'key': 'a', 'value': 'b'},
                    {'key': 'c', 'value': 'd'},
                ]
            }
            ```
        - Decoder will accept both traditional form(```{'a':'b','c':'d'}```) and the form above.
    - Allow any hashable object as key
        - ```{User('f', 'l'): 1, User('a','b'):2}``` ->
            ```
            {
                '__type__': 'dict'
                '__data__': [
                    {
                        'key': {'__type__': 'User', 'first': 'f', 'last':'l'}, 
                        'value: 1
                    },
                    {
                        'key': {'__type__': 'User', 'first': 'a', 'last':'b'}, 
                        'value: 2
                    }
                ]
            }        
            ```
- Distinguish tuple from List
    - ```[1,2,3]``` -> ```[1,2,3]```
    - ```(1,2,3)``` -> ```{'__type__':'tuple', '__data__':[1,2,3]}```
    
- Custom class decoder whitelist via class_map
    - ```python
      from strong_json import StrongJson
      s = {'__type__': 'User', 'first':'f', 'last':'l'}
      class_map = {'User', User}
      custom_json = StrongJson(class_map=class_map)
      custom_json.from_json(s)
      ```
    - By default, strong json pass all the argument by name to the constructor.
    - You could also override ```StrongJson``` or implement interface ```FromJsonable``` for custom decoder.
    - You could also use strong_json.ClassMapBuilder to save some typing.
- Support for date and datetime.
    - ```datetime.date(2019,8,23)``` -> 
    ```
    {
        '__type__': 'date', 
        'year': 2019, 
        'month': 8, 
        'day': 23
    }
    ```
- Support for Enum.
    - ```
      class Color(Enum):
        RED='redd'
        BLUE='blueee'
      strong_json.to_json(Color.RED)
      ``` 
      ->
      ```
      {'__type__': 'Color' '__data__':'RED'}
      ```
      
# Basic Usage
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/piti118/strong_json_notebook/master)



## From Object to JSON
### Builtin Object
```python
from strong_json import strong_json
obj = {'a': [1,2,3], 'b':[2,3,4]}
s = strong_json.to_json(obj)

# if you want indentation you could do
s_indent = strong_json.to_json(obj, indent=2)
```
### Custom Class

#### SimpleClass
Custom class works out of the box 
```python
from strong_json import strong_json

class SimpleClass:
    def __init__(self, msg):
        self.msg = msg

obj = SimpleClass('hello')
s = strong_json.to_json(object)
```
which produce json of the form
```json
{
  "__type__": "SimpleClass",
  "msg": "hello"
}
```

#### Custom Encoder.
If you don't like the default class encoder you can create new one by implementing ```ToJsonable``` interface.
```python
from strong_json import strong_json, ToJsonable

class User(ToJsonable):
    def __init__(self, first, last):
        self.first = first
        self.last = last
        
    # this is where the magic happens.
    def to_json_dict(self, encoder: StrongJson) -> Dict[str, JSONPrimitive]:
        return {
            '__type__': 'User',
            'first': encoder.to_json_dict(self.first),
            'last': encoder.to_json_dict(self.last),
            'full_name': encoder.to_json_dict(f"{self.first} {self.last}")
        }

obj = User('hello', 'world')
s = strong_json.to_json(object)
```
which produces json of the form
```json
{
  "__type__": "User",
  "first": "hello",
  "last": "world",
  "full_name": "hello_world"
}
```

## From JSON to object

### Builtin Object
```python
from strong_json import strong_json
s = """{'a': 'b', 'c':'d'}"""
obj = strong_json.from_json(s)
````

### Custom Class
```python
from strong_json import StrongJson

class User: # it doesn't have to be ToJsonable
    def __init__(self, first, last):
        self.first = first
        self.last = last

s = """
{
    '__type__': 'User',
    'first': 'hello',
    'last': 'world'
}
"""
class_map = {'User': User}
custom_json = StrongJson(class_map=class_map)
obj = custom_json.to_json(s, class_map)
```
