import unittest
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, create_engine
from rest import DBApi, RestApiApp
import bottle
app = bottle.Bottle()
engine = create_engine('sqlite://')
decor = RestApiApp(app, engine)


Base = declarative_base()

@decor('/api/test')
class NTest(Base):
    __tablename__ = 'test'
    uid = Column(Integer, primary_key=True)
    value = Column(Integer)

Base.metadata.create_all(engine)
bottle.run(app, host='0.0.0.0', port=8080)
