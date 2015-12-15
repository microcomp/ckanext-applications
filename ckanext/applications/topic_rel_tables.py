import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import class_mapper


topic_rel_table = None
TopicRelTable = None


def make_uuid():
    return unicode(uuid.uuid4())


def init_db(model):
    class _TopicRelTable(model.DomainObject):
        __table_args__ = {'extend_existing': True}
        @classmethod
        def get(cls, **kw):
            '''Finds a single entity in the register.'''
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kw).all()
        @classmethod
        def getALL(cls, **kw):
            '''Finds a single entity in the register.'''
            query = model.Session.query(cls).autoflush(False)
            return query.all()
        @classmethod
        def delete(cls, **kw):
            query = model.Session.query(cls).autoflush(False).filter_by(**kw).all()
            for i in query:
                model.Session.delete(i)
            return


        @classmethod
        def topic_rel_table(cls, **kw):
            '''Finds a single entity in the register.'''
            order = kw.pop('order', False)

            query = model.Session.query(cls).autoflush(False)
            query = query.filter_by(**kw)
            if order:
                query = query.order_by(cls.order).filter(cls.order != '')
            return query.all()

    global TopicRelTable
    TopicRelTable = _TopicRelTable
    sql = '''
                CREATE TABLE topic_rel_table (
                    id text NOT NULL,
                    topic_id text NOT NULL,
                    app_id text NOT NULL
                );
    '''
    conn = model.Session.connection()
    try:
        conn.execute(sql)
    except sa.exc.ProgrammingError:
        model.Session.rollback()
    model.Session.commit()

    types = sa.types
    global topic_rel_table
    topic_rel_table = sa.Table('topic_rel_table', model.meta.metadata,
        sa.Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        sa.Column('topic_id', types.UnicodeText, default=u''),
        sa.Column('app_id', types.UnicodeText, default=u'')
    )

    model.meta.mapper(
        TopicRelTable,
        topic_rel_table,
    )


def table_dictize(obj, context, **kw):
    '''Get any model object and represent it as a dict'''
    result_dict = {}

    if isinstance(obj, sa.engine.base.RowProxy):
        fields = obj.keys()
    else:
        ModelClass = obj.__class__
        table = class_mapper(ModelClass).mapped_table
        fields = [field.name for field in table.c]

    for field in fields:
        name = field
        if name in ('current', 'expired_timestamp', 'expired_id'):
            continue
        if name == 'continuity_id':
            continue
        value = getattr(obj, name)
        if value is None:
            result_dict[name] = value
        elif isinstance(value, dict):
            result_dict[name] = value
        elif isinstance(value, int):
            result_dict[name] = value
        elif isinstance(value, datetime.datetime):
            result_dict[name] = value.isoformat()
        elif isinstance(value, list):
            result_dict[name] = value
        else:
            result_dict[name] = unicode(value)

    result_dict.update(kw)

    ##HACK For optimisation to get metadata_modified created faster.

    context['metadata_modified'] = max(result_dict.get('revision_timestamp', ''),
                                       context.get('metadata_modified', ''))

    return result_dict

