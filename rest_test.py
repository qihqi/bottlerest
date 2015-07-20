import unittest
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import sessionmaker
from rest import DBApi

Base = declarative_base()


class NTest(Base):
    __tablename__ = 'test'
    uid = Column(Integer, primary_key=True)
    value = Column(Integer)


class DBTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite://')
        cls.sessionmaker = sessionmaker(bind=engine)
        cls.dbapi = DBApi(NTest)
        Base.metadata.create_all(engine)


    def test_db(self):

        session = self.sessionmaker()
        key = self.dbapi.create(session, {'uid': 1, 'value': 2})
        session.commit()

        to_get = self.dbapi._get_dbobj(session, 1)
        self.assertEquals(2, to_get.value)

        assert self.dbapi.update(session, 1, {'value': 5})
        session.commit()

        to_get = self.dbapi._get_dbobj(session, 1)
        self.assertEquals(5, to_get.value)



if __name__ == '__main__':
    unittest.main()
