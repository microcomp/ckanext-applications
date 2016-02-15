import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.common import _, c
import logging
import __builtin__
import json
import os
import logging

import app_topics_db
import topic_rel_tables

import ckan.logic

import ckan.lib.jsonp as jsonp

def create_topic_rel_table(context):
    if topic_rel_tables.topic_rel_table is None:
        topic_rel_tables.init_db(context['model'])

@ckan.logic.side_effect_free
def add_new_topic_rel(context, data_dict):
    create_topic_rel_table(context)
    if topic_rel_exists(context, data_dict):
        return {"status":"fail"}
    info = topic_rel_tables.TopicRelTable()
    info.topic_id = data_dict.get('topic_id')
    logging.warning('topic_id')
    logging.warning(data_dict.get('topic_id'))
    info.app_id = data_dict.get('app_id')
    logging.warning(data_dict.get('app_id'))
    info.save()
    logging.warning("saved")
    session = context['session']
    session.add(info)
    logging.warning("added")
    session.commit()
    logging.warning("commit")
    return True

@ckan.logic.side_effect_free
def topic_rel_exists(context, data_dict):
    create_topic_rel_table(context)
    all_topics = topic_rel_tables.TopicRelTable.get(**{'app_id':data_dict['app_id'], 'topic_id':data_dict['topic_id']})
    return len(all_topics) != 0

@ckan.logic.side_effect_free
def del_topic_rel(context, data_dict):
    create_topic_rel_table(context)
    logging.warning("deleting...")
    session = context['session']
    to_remove = topic_rel_tables.TopicRelTable.delete(**{'app_id':data_dict['app_id']})
    logging.warning(to_remove)
    session.commit()
    return

@ckan.logic.side_effect_free
def get_apps_topics(context, data_dict):
    create_topic_rel_table(context)
    all_topics = topic_rel_tables.TopicRelTable.get(**{'app_id':data_dict['app_id']})
    buffer_ = [x.topic_id for x in all_topics ]
    result = [ get_topic_name(context, {'id':x}) for x in buffer_]
    return result

@ckan.logic.side_effect_free
def has_topic(context, data_dict):
    create_topic_rel_table(context)
    topic = topic_rel_tables.TopicRelTable.get(**{'app_id':data_dict['app_id'], 'topic_id':get_topic_id(context, {'display_name':data_dict['topic']})})

    return len(topic) > 0

def create_new_app_topic_db(context):

    if app_topics_db.AppTopicTable is None:
        app_topics_db.init_db(context['model'])

@ckan.logic.side_effect_free
def add_new_app_topic(context, data_dict):
    create_new_app_topic_db(context)
    topic = app_topics_db.AppTopicTable()
    topic.display_name = data_dict.get('display_name')
    topic.save()
    session = context['session']
    session.add(topic)
    session.commit()
    return True

@ckan.logic.side_effect_free
def topic_exists(context, data_dict):
    create_new_app_topic_db(context)
    topic = app_topics_db.AppTopicTable.get(**{'display_name':data_dict['display_name']})
    return topic != None

@ckan.logic.side_effect_free
def get_topic_id(context, data_dict):
    create_new_app_topic_db(context)
    topic = app_topics_db.AppTopicTable.get(**{'display_name':data_dict['display_name']})
    if (len(topic)) == 0:
        return ""
    return topic[0].id

@ckan.logic.side_effect_free
def get_topic_name(context, data_dict):
    create_new_app_topic_db(context)
    topic = app_topics_db.AppTopicTable.get(**{'id':data_dict['id']})
    return topic[0].display_name
@ckan.logic.side_effect_free
def get_all_topics(context, data_dict):
    create_new_app_topic_db(context)
    topic = app_topics_db.AppTopicTable.getALL(**data_dict)
    logging.warning(topic)
    topics = [{'id': x.id, 'display_name': x.display_name} for x in topic]
    return topics

@ckan.logic.side_effect_free
def get_all_topic_names(context, data_dict):
    create_new_app_topic_db(context)
    topic = app_topics_db.AppTopicTable.getALL(**data_dict)
    logging.warning(topic)
    topics = [x.display_name for x in topic]
    return topics

def all_topics():
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    result = get_all_topics(context, {})
    return result
