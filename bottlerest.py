from sqlalchemy.inspection import inspect
from sqlalchemy.orm import sessionmaker

import bottle
import json
import traceback


class SessionManager(object):
    def __init__(self, session_factory):
        self._session = None
        self._factory = session_factory

    def __enter__(self):
        self._session = self._factory()
        return self._session

    def __exit__(self, type_, value, stacktrace):
        if type_ is None:
            self._session.commit()
            self._session.close()
            return True
        else:
            if type_ is not bottle.HTTPResponse:
                self._session.rollback()
                raise type_, value, stacktrace
            else:
                self._session.commit()
            self._session.close()
            return False

    @property
    def session(self):
        return self._session


# Copies src to dest.
# src and dest can be both dict or object
def fieldcopy(src, dest, fields):
    srcgetter = src.get if hasattr(src, 'get') else src.__getattribute__
    destsetter = dest.__setitem__ if hasattr(dest, 'get') else dest.__setattr__
    for f in fields:
        try:
            value = srcgetter(f)
        except KeyError:
            pass
        else:
            destsetter(f, value)


def dbmix(database_class, override_name=()):
    class DataObjectMixin(object):
        db_class = database_class
        _columns = inspect(database_class).columns
        pkey = inspect(database_class).primary_key[0]

        def __init__(self, **kwargs):
            self.merge_from(kwargs)

        def db_instance(self):
            result = self.db_class()
            fieldcopy(self, result, self._columns.keys())
            return result

        @classmethod
        def from_db_instance(cls, db_instance):
            y = cls()
            fieldcopy(db_instance, y, cls._columns.keys())
            return y

        def merge_from(self, obj):
            fieldcopy(obj, self, self._columns.keys())
            return self

        def serialize(self):
            return self._serialize_helper(self, self._columns.keys())

        @classmethod
        def deserialize(cls, dict_input):
            result = cls().merge_from(dict_input)
            for x, y in override_name:
                original = dict_input.get(y, None)
                setattr(result, x, original)
            return result

        @classmethod
        def _serialize_helper(cls, obj, names):
            result = {}
            fieldcopy(obj, result, names)
            for x, y in override_name:
                original = result[x]
                result[y] = original
                del result[x]
            return result
    return DataObjectMixin


class DBApi(object):

    def __init__(self, objclass):
        self.objclass = objclass

    def create(self, session, obj):
        dbobj = obj.db_instance()
        session.add(dbobj)

    def get(self, session, pkey):
        db_instance = session.query(self.objclass.db_class).filter(
            self.objclass.pkey == pkey).first()
        if db_instance is None:
            return None
        return self.objclass.from_db_instance(db_instance)

    def update(self, session, pkey, content_dict):
        count = session.query(self.objclass.db_class).filter(
            self.objclass.pkey == pkey).update(
            content_dict)
        return count

    def delete(self, session, pkey):
        count = session.query(self.objclass.db_class).filter(
            self.objclass.primary_key == pkey).delete()
        return count

    def getone(self, session, **kwargs):
        result = self.search(session, **kwargs)
        if not result:
            return None
        return result[0]

    def search(self, session, **kwargs):
        query = session.query(self.objclass.db_class)
        for key, value in kwargs.items():
            mode = None
            if '-' in key:
                key, mode = key.split('-')
            f = self.objclass._columns[key] == value
            if mode == 'prefix':
                f = self.objclass._columns[key].startswith(value)
            query = query.filter(f)
        return map(self.objclass.from_db_instance, iter(query))


class RestApi(object):

    def __init__(self, dbapi, sessionmanager):
        self.dbapi = dbapi
        self.sm = sessionmanager 

    def get(self, pkey):
        with self.sm as session:
            return self.dbapi.get(session, pkey=pkey).serialize()

    def put(self, pkey):
        content_dict = json.loads(bottle.request.body.read())
        with self.sm as session:
            count = self.dbapi.update(session,
                pkey=pkey, content_dict=content_dict)
            return {'modified': count}

    def post(self):
        content_dict = json.loads(bottle.request.body.read())
        with self.sm as session:
            pkey = self.dbapi.create(session, content_dict=content_dict)
            return {'key': pkey}

    def delete(self, pkey):
        with self.sm as session:
            count = self.dbapi.delete(session, pkey)
            return {'deleted': count}

    def search(self):
        with self.sm as session:
            args = bottle.request.query
            content = self.dbapi.search(session, **args)
            return {'result': [c.serialize() for c in content]}


class RestApiApp(object):

    def __init__(self, connection, bottle_app=None):
        if bottle_app is None:
            bottle_app = bottle.default_app()
        self.app = bottle_app
        if isinstance(connection, str):
            from sqlalchemy import create_engine
            connection = create_engine(connection)
        self.connection = connection
        self.sessionmanager = SessionManager(sessionmaker(bind=connection)) 
        self.apis = {}

    def bind_api(self, url, clazz):
        dbclass = dbmix(clazz)
        dbapi = DBApi(dbclass)
        self.restapi = RestApi(dbapi, self.sessionmanager)
        self.apis[clazz] = dbapi
        self.apis[dbclass] = dbapi
        url_with_id = url +'/<pkey>'
        self.app.get(url_with_id)(self.restapi.get)
        self.app.put(url_with_id)(self.restapi.put)
        self.app.delete(url_with_id)(self.restapi.delete)
        self.app.post(url)(self.restapi.post)
        self.app.get(url)(self.restapi.search)
        return dbclass

    def rest(self, url):
        def decorator(clazz):
            return self.bind_api(url, clazz)
        return decorator

    def getapi(self, clazz):
        return self.apis.get(clazz)
