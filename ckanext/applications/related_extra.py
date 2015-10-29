import db
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

import related_extra

import ckan.logic

def create_related_extra_table(context):
    if db.related_extra_table is None:
        db.init_db(context['model'])
@ckan.logic.side_effect_free
def new_related_extra(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra()
    info.related_id = data_dict.get('related_id')
    info.key = data_dict.get('key')
    info.value = __builtin__.value
    info.save()
    session = context['session']
    session.add(info)
    session.commit()
    return {"status":"success"}

@ckan.logic.side_effect_free
def add_app_owner(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra()
    info.related_id = data_dict.get('related_id')
    info.key = data_dict.get('key')
    info.value = data_dict.get('value')
    info.save()
    session = context['session']
    session.add(info)
    session.commit()
    return {"status":"success"}

@ckan.logic.side_effect_free
def mod_app_owner(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra.get(**{'related_id':data_dict['related_id']})
    index = 0
    for i in range(len(info)):
        if info[i].key == 'owner':
            index = i
    info[index].related_id = data_dict.get('related_id')
    
    info[index].key = data_dict.get('key')
    info[index].value = data_dict.get('value')
    info[index].save()
    session = context['session']
    session.commit()
    return {"status":"success"}

@ckan.logic.side_effect_free
def get_app_owner(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra.get(**data_dict)
    index = 0
    for i in range(len(info)):
        if info[i].key == 'owner':
            index = i
    info[index].related_id = data_dict.get('related_id')
    
    logging.warning(info[index])
    logging.warning(info)
    return info[index].value

@ckan.logic.side_effect_free
def check_priv_related_extra(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra.get(**data_dict)
    index = 0
    for i in range(len(info)):
        if info[i].key == 'privacy':
            index = i
    info[index].related_id = data_dict.get('related_id')
    
    logging.warning(info[index].value)
    return info[index].value == 'public'

@ckan.logic.side_effect_free
def mod_related_extra(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra.get(**data_dict)
    index = 0
    for i in range(len(info)):
        if info[i].key == 'privacy':
            index = i
    info[index].related_id = data_dict.get('related_id')
    
    info[index].key = data_dict.get('key')
    info[index].value = __builtin__.value
    info[index].save()
    session = context['session']

    #session.add(info)
    session.commit()
    return {"status":"success"}

@ckan.logic.side_effect_free
def del_related_extra(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra.delete(**data_dict)
    session = context['session']
    session.commit()
    return {"status":"success"}



@ckan.logic.side_effect_free
def get_related_extra(context, data_dict):
    '''
    This function retrieves extra information about given tag_id and
    possibly more filtering criterias. 
    '''
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.get(**data_dict)
    return res

def list_reports(page, filter_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {}
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.getALL(**data_dict)

    res = [x for x in res if x.key == 'report']

    if filter_id != '':
        res = [x for x in res if x.related_id == filter_id]
    length = len(res)
    result = []
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    for i in range(page*10-10,page*10):
        try:
            result.append(res[i])
        except IndexError:
            pass
    if page > length//10+1:   
        base.abort(400, ('"page" parameter out of range')) 
    
    #res = res[page-1*10:page*10+4]

    return {'reports': result, 'count': length, 'delall': (length > 0) and (filter_id != ''), 'related_id':filter_id}
def reports_num(related_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id': related_id, 'key':'report'}
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.get(**data_dict)
    return len(res)

def reported_by_user(user_id, related_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id': related_id, 'key':'reported_by'}
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.get(**data_dict)
    res = [x for x in res if x.value.split('*')[0] == c.userobj.id]

    return len(res) == 0
def report_text(user_id, related_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id': related_id, 'key':'reported_by'}
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.get(**data_dict)
    res = [x for x in res if x.value.split('*')[0] == c.userobj.id]
    data_dict2 = {'related_id': related_id, 'key':'report', 'id': res[0].value.split('*')[1]}
    res = db.RelatedExtra.get(**data_dict2)
    return res[0].value

def reported_by(related_id, report_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id': related_id, 'key':'reported_by'}
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.get(**data_dict)
    res = [x for x in res if x.value.split('*')[1] == report_id]
    return res[0].value.split('*')[0]
def reported_id(related_id, user_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id': related_id, 'key':'reported_by'}
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.get(**data_dict)
    res = [x for x in res if x.value.split('*')[0] == user_id]
    return res[0].value.split('*')[1]

def is_private(id):

    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id':id,'key':'privacy'}
    create_related_extra_table(context)
    info = db.RelatedExtra.get(**data_dict)
    index = 0
    for i in range(len(info)):
        if info[i].key == 'privacy':
            index == i
    logging.warning(info[index].value)
    return info[index].value