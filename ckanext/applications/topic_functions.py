import topic_rel_table as trb
import app_topics_db as at
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

import ckan.logic

def create_topic_rel_table_table(context):
    if trb.topic_rel_table_table is None:
        trb.init_db(context['model'])

@ckan.logic.side_effect_free
def add_new_topic_rel(context, data_dict):
    create_topic_rel_table_table(context)
    if topic_rel_exists(context, data_dict):
        return {"status":"fail"}
    info = trb.TopicRelTable()
    info.topic_id = data_dict.get('topic_id')
    info.app_id = data_dict.get('app_id')
    info.save()
    session = context['session']
    session.add(info)
    session.commit()
    return {"status":"success"}

@ckan.logic.side_effect_free
def topic_rel_exists(context, data_dict):
    create_topic_rel_table_table(context)
    all_topics = trb.get(**{'app_id':data_dict['app_id'], 'topic_id':data_dict['topic_id']})
    return all_topics != None

@ckan.logic.side_effect_free
def del_topic_rel(context, data_dict):
    create_topic_rel_table_table(context)
    to_remove = trb.get(**{'app_id':data_dict['app_id'], 'topic_id':data_dict['topic_id']})
    session = context['session']
    session.remove(to_remove)
    session.commit()
    return

def create_new_app_topic_db(context):
    if at.app_topic_db is None:
        at.init_db(context['model'])

@ckan.logic.side_effect_free
def add_new_app_topic(context, data_dict):
    create_new_app_topic_db(context)
    topic = at.AppTopicTable()
    topic.display_name = data_dict.get('display_name')
    topic.save()
    sesssion = context['session']
    session.add(topic)
    session.commit()
    return True

@ckan.logic.side_effect_free
def topic_exists(context, data_dict):
    create_new_app_topic_db(context)
    topic = at.get(**{'display_name':data_dict['display_name']})
    return topic != None

@ckan.logic.side_effect_free
def get_topic_id(context, data_dict):
    create_new_app_topic_db(context)
    topic = at.get(**{'display_name':data_dict['display_name']})
    return topic.id

@ckan.logic.side_effect_free
def all_topics(context):
	create_new_app_topic_db(context)
    topic = at.getALL(**{})
    topics = [{'id': x.id, 'display_name': x.display_name} for x in topic]
    return topics