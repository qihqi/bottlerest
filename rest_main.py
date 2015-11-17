import bottle
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from bottlerest import RestApiApp

api = RestApiApp('sqlite://')
Base = declarative_base()


@api.rest('/api/test')
class NTest(Base):
    __tablename__ = 'test'
    key = Column(Integer, primary_key=True)
    value = Column(Integer)
    string_attr = Column(String(20))

@bottle.post('/api/helloworld')
def custom_api_that_uses_NTest_too():
    # some preprocessing
    x = NTest()
    x.key = 1 
    x.value = 2
    testapi = api.getapi(NTest)
    with api.sessionmanager as session:
        testapi.create(session, x)
        session.commit()
    # some post processing 
    # blah

    # return result
    import json
    return json.dumps(x.serialize())



if __name__ == '__main__':
    Base.metadata.create_all(api.connection)
    bottle.run(host='0.0.0.0', port=8080)
