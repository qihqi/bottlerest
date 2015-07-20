from sqlalchemy.inspection import inspect
from sqlalchemy.orm import sessionmaker
from bottle import request
import json


class DBApi(object):

    def __init__(self, db_class):
        self.db_class = db_class
        self.primary_key = inspect(db_class).primary_key[0]
        self.columns = inspect(db_class).columns

    def create(self, session, content_dict):
        dbobj = self.db_class()
        for key, value in content_dict.items():
            setattr(dbobj, key, value)
        session.add(dbobj)
        session.flush()
        return getattr(dbobj, self.primary_key.name)

    def _get_dbobj(self, session, pkey):
        dbobj = session.query(self.db_class).filter(
            self.primary_key == pkey).first()
        return dbobj

    def obj_to_dict(self, obj):
        result = {}
        for col_name in self.columns.keys():
            attr = getattr(obj, col_name)
            if attr is not None:
                result[col_name] = attr
        return result

    def get(self, session, pkey):
        return self.obj_to_dict(self._get_dbobj(session, pkey))

    def update(self, session, pkey, content_dict):
        count = session.query(self.db_class).filter(
            self.primary_key == pkey).update(
            content_dict)
        return count

    def delete(self, session, pkey):
        count = session.query(self.db_class).filter(
            self.primary_key == pkey).delete()
        return count

    def search(self, session, **kwargs):
        query = session.query(self.db_class)
        for key, value in kwargs.items():
            mode = None
            if '$' in key:
                key, mode = key.split('$')
            f = self.columns[key] == value
            if mode == 'prefix':
                f = self.columns[key].startwith(value)
            query = query.filter(f)
        return map(self.obj_to_dict, query)


class RestApi(object):

    def __init__(self, dbapi, sessionmaker):
        self.dbapi = dbapi
        self.sessionmaker = sessionmaker

    def wrapped_call(self, func, *args, **kwargs):
        try:
            session = self.sessionmaker()
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            session.rollback()
            raise e

    def get(self, pkey):
        return self.wrapped_call(self.dbapi.get, pkey=pkey)

    def put(self, pkey):
        content_dict = json.loads(request.body.read())
        count = self.wrapped_call(
            self.dbapi.update,
            pkey=pkey, content_dict=content_dict)
        return {'modified': count}

    def post(self):
        content_dict = json.loads(request.body.read())
        pkey = self.wrapped_call(
            self.dbapi.create,
            content_dict=content_dict)
        return {'key': pkey}

    def delete(self, pkey):
        count = self.wrapped_call(self.dbapi.delete, pkey)
        return {'deleted': count}

    def search(self):
        args = request.query
        content = self.wrapped_call(self.dbapi.search, **args)
        return {'result': list(content)}


class RestDecorator(object):

    def __init__(self, bottle_app, connection):
        self.app = bottle_app
        self.connection = connection
        self.sessionmaker = sessionmaker(bind=connection)
        self.apis = {}


    def __call__(self, url):
        def decorator(clazz):
            dbapi = DBApi(clazz)
            self.apis[clazz] = dbapi
            restapi = RestApi(dbapi, self.sessionmaker)
            url_with_id = url +'/<pkey>'
            self.app.get(url_with_id)(restapi.get)
            self.app.put(url_with_id)(restapi.put)
            self.app.post(url)(restapi.post)
            self.app.delete(url)(restapi.delete)
            self.app.get(url)(restapi.search)
            return clazz
        return decorator

    def getapi(self, clazz):
        return self.apis.get(clazz)
