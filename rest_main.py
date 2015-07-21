import bottle
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from bottlerest import RestApiApp

# Can also be constucted as api = RestApiApp(connection, app)
# where connection can be either a connection string or a sqlalchemy engine
# object; app is a bottle app (bottle.Bottle instance)
# Without passing app parameter it will use the default app in bottle
api = RestApiApp('sqlite://')
Base = declarative_base()


@api.rest('/api/test')
class NTest(Base):
    __tablename__ = 'test'
    key = Column(Integer, primary_key=True)
    value = Column(Integer)
    string_attr = Column(String(20))


if __name__ == '__main__':
    Base.metadata.create_all(api.connection)
    # or bottle.run(app, ...) if app is passed to construct RestApiApp
    bottle.run(host='0.0.0.0', port=8080)
