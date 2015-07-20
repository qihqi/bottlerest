# bottlerest
Build Simple REST API on Bottle and SqlAlchemy!

## Dependency:

* Bottle
```
pip install bottle
```

* SqlAlchemy
```
pip install sqlalchemy
```


## Example: Basic Rest API



```python
import bottle
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, create_engine
from bottlerest import RestApiApp

app = bottle.Bottle()
engine = create_engine('sqlite://')
restapi = RestApiApp(app, engine)
Base = declarative_base()

@restapi('/api/test')
class NTest(Base):
    __tablename__ = 'test'
    key = Column(Integer, primary_key=True)
    value = Column(Integer)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    bottle.run(app, host='0.0.0.0', port=8080)
```

The restapi decorator shown in the above example will add 5 routes to the 
bottle app:

1. *GET '/api/test/<pkey>'* Get element by primary key.

2. *POST '/api/test'* Create an element, will return the primary key of
   the created element.

3. *PUT'/api/test/<pkey>'* Modify element by primary key

4. *DELETE'/api/test/<pkey>'* Delete element by primary key

5. *GET '/api/test?attr=value1&..'* search by specific attribute.

## Demo
1. Run above file:

``` 
python rest_main.py 
```

2. Create a a Test object:

```
$ curl localhost:8080/api/test --data '{"key": 1, "value":2 }'
{"key": 1}
```

3. Get that Test object using primary key.

```
$ curl localhost:8080/api/test/1
{"uid": 1, "value": 2}
```

4. Modify test object.

```
 curl localhost:8080/api/test/1 --data '{"value":3 }' -X PUT
{"modified": 1}
```
The api returns the number of object modified.

5. Searching:

```
$ curl localhost:8080/api/test?value=3
{"uid": 1, "value": 3}
```
5. Deleting: Api returns number of items deleted.

```
$ curl localhost:8080/api/test/1 -X DELETE
{"deleted": 1}
```

