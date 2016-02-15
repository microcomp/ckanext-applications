# coding=utf-8
import urllib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import datetime
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.plugins as p
from ckan.common import _, c
import ckan.plugins.toolkit as toolkit
import urllib2
import logging
import ckan.logic
import __builtin__
import db
from pylons import config, request, response

import topic_functions as tf
import related_extra
import json


import stats as stats_lib

abort = base.abort
_get_action = logic.get_action
_check_access = logic.check_access
_related_id_exists = logic.validators.related_id_exists

@toolkit.side_effect_free
def ckan_stats(context, data_dict):
    ''' Ckan stats API for mobile applications '''
    result = {}
    stats = stats_lib.Stats()
    rev_stats = stats_lib.RevisionStats()

    result['most_edited_packages'] = []
    users = stats.most_edited_packages()
    for i in users:
        result['most_edited_packages'].append({'title':i[0].title, 'edits' : i[1]})

    result['largest_groups'] = []
    groups = stats.largest_groups()

    for i in groups:
        name = model.Session.query(model.Group).filter(model.Group.id == i[0].id).first().title
        result['largest_groups'].append({'group_name':name, 'users_in_group':i[1]})

    result['top_package_owners'] = []
    owners = stats.top_package_owners()
    oo = {}
    for j in owners:
        result['top_package_owners'].append({'username': j[0].fullname, 'packages' : j[1]})

    result['new_packages_by_week'] = []
    bv = rev_stats.get_by_week('new_packages')
    for i in bv:
        result['new_packages_by_week'].append({'date':i[0], 'new_packages':i[2], 'all_packages':i[3]})

    #deleted packages
    result['deleted_packages_by_week'] = []
    dv = rev_stats.get_by_week('deleted_packages')

    for i in dv:
        result['deleted_packages_by_week'].append({'date':i[0], 'deleted_packages_this_week':i[2], 'all_deleted_packages':i[3]})

    datasets = model.Session.query(model.Package).filter(model.Package.id != "").all()
    result['dataset_num'] = len(datasets)
    users = model.Session.query(model.User).filter(model.User.id != "").all()
    result['user_count'] = len(users)
    resources = model.Session.query(model.Resource).filter(model.Resource.id != '').all()
    result['resources_count'] = len(resources)
    organizations = model.Session.query(model.Group).filter(model.Group.id != '').all()
    result['organizations_count'] = len(organizations)
    new_30d = 0
    new_7d = 0
    mod_30d = 0
    mod_7d = 0
    today = datetime.datetime.now()
    year = today.year
    month = today.month
    month2 = today.month

    if month != 1:
        month -= 1
    else:
        year-=1
        month = 12
    day = today.day
    if day > 7:
        day-= 7
    else:
        month2 -=1
        day-=7
        day = 30+day
    l7d = ""+str(today.year)+"-"+str(month2)+"-"+str(day)+" "+str(today.hour)+":"+str(today.minute)+":"+str(today.second)
    l30d = ""+str(year)+"-"+str(month)+"-"+str(today.day)+" "+str(today.hour)+":"+str(today.minute)+":"+str(today.second)
    l30d =  datetime.datetime.strptime(l30d, '%Y-%m-%d %H:%M:%S')
    l7d =  datetime.datetime.strptime(l7d, '%Y-%m-%d %H:%M:%S')

    new_users_30d = 0
    new_users_7d = 0
    for i in users:
        lm = datetime.datetime.strptime(str(i.created).split('.')[0],'%Y-%m-%d %H:%M:%S')
        if  lm > l30d:
            new_users_30d +=1
        if lm > l7d:
            new_users_7d += 1
    result['new_users_7d'] = new_users_7d
    result['new_users_30d'] = new_users_30d

    new_orgs_30d = 0
    new_orgs_7d = 0
    for i in organizations:
        lm = datetime.datetime.strptime(str(i.created).split('.')[0],'%Y-%m-%d %H:%M:%S')
        if  lm > l30d:
            new_orgs_30d +=1
        if lm > l7d:
            new_orgs_7d += 1
    result['new_orgs_7d'] = new_orgs_7d
    result['new_orgs_30d'] = new_orgs_30d

    new_resources_30d = 0
    new_resources_7d = 0
    for i in resources:
        lm = datetime.datetime.strptime(str(i.created).split('.')[0],'%Y-%m-%d %H:%M:%S')
        if  lm > l30d:
            new_resources_30d +=1
        if lm > l7d:
            new_resources_7d += 1
    result['new_resources_7d'] = new_resources_7d
    result['new_resources_30d'] = new_resources_30d
    

    for i in datasets:
        lm = datetime.datetime.strptime(str(i.metadata_modified).split('.')[0],'%Y-%m-%d %H:%M:%S')
        if  lm > l30d:
            mod_30d +=1
        if lm > l7d:
            mod_7d += 1

    result['modified_datasets_last_30d'] = mod_30d
    result['modified_datasets_last_7d'] = mod_7d
    return result


def valid_dataset(dataset_name):
        dataset =  model.Session.query(model.Package).filter(model.Package.name == dataset_name).first()
        if dataset != None:
            return True
        ds2 = model.Session.query(model.Package).filter(model.Package.title == dataset_name).first()
        if ds2 != None:
            return ds2.name
        return False

def add_datasets(datasets,  id):
    related_ids = []
    for i in datasets:
        id_query = model.Session.query(model.Package).filter(model.Package.name == i).first()
        if id_query == None:
            logging.warning('redirecting...')
            return
        related_ids.append(id_query.id)
    logging.warning('related id-s:')
    logging.warning(related_ids)
    related_datasets = []
    for i in range(len(related_ids)):
        buffer = model.related.RelatedDataset()
        related_datasets.append(buffer)
    for i in range(len(related_ids)):
        related_datasets[i].dataset_id = related_ids[i]
        related_datasets[i].id = unicode(uuid.uuid4())
        related_datasets[i].related_id = id
        related_datasets[i].status = 'active'
        model.Session.add(related_datasets[i])   
    model.Session.commit()
    return

@toolkit.side_effect_free
def mod_app_api(context, data_dict=None):
    ''' Mod_app_api- application modification '''
    
    old_data = model.Session.query(model.Related).filter(model.Related.id == data_dict['id']).first()
    logic.get_action('related_show')(context,data_dict)
    #all related items deleted...
    data = {}
    try:
        title = data_dict['title']
    except KeyError:
        title= ""
    try:
        description = data_dict['description']
    except KeyError:
        description = ""
    try:
        image_url =  data_dict['image_url']
    except KeyError:
        image_url = ""
    try:
        url = data_dict['url'] 
    except KeyError:
        url = ""
    try:
        private =  data_dict['private'] 
    except KeyError:
        private = ""
    try:
        datasets =  data_dict['datasets'] 
    except KeyError:
        datasets = ""
    try:
        owner = data_dict['owner'] 
    except KeyError:
        owner  = c.userobj.fullname
    try:
        tags = data_dict['tags'] 
    except KeyError:
        tags  = ""

    try:
        topics = data_dict['topics'] 
    except KeyError:
        topics  = ""
    old_data = model.Session.query(model.Related).filter(model.Related.id == data_dict['id']).first()
    logic.get_action('related_show')(context,data_dict)

    logging.warning(old_data)
    logging.warning(len(datasets))
    if len(title)== 0:
        title = old_data.title
    if len(description)== 0:
        description = old_data.description
    if len(image_url)== 0:
        image_url= old_data.image_url
    if len(url)== 0:
        url = old_data.url

    old_data.title = title
    old_data.description = description
    old_data.image_url = image_url
    old_data.url = url
    old_data.private = private
    data_dict["owner_id"] = old_data.owner_id
    _check_access('app_edit', context, data_dict)
    data_dict2 = {'related_id':data_dict['id'],'key':'privacy'}
    __builtin__.value = private

    #if private != None or private != '':
    #    related_extra.mod_related_extra(context, data_dict2)
    #    model.Session.commit()
    #logging.warning(related_datasets)
    if datasets != "":
        related_datasets = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == data_dict['id']).all()
        for i in related_datasets:
            model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.id == i.id).delete(synchronize_session=False)
        model.Session.commit()
        datasets2 = datasets.split(',')
        logging.warning(datasets2)
        add_datasets(datasets2, data_dict['id'])
    #else:
    #    add_datasets(related_datasets, id)
    related_extra.mod_app_owner(context, {'related_id':old_data.id,'key':'owner', 'value':owner})

    try:
        other_topics = data_dict['topics']
    except KeyError:
        other_topics = ""


    topics = tf.get_all_topic_names(context, {'app_id':data_dict['id']})
    if len(other_topics) > 3:
        tf.del_topic_rel(context, {'app_id':data_dict['id']})
        other_topics_arr = [x.strip() for x in other_topics.split(',')]
        for other_topic in other_topics_arr:
            if other_topic not in topics:
                tf.add_new_app_topic(context, {'display_name':other_topic})
            topics_data = tf.get_all_topics(context, {'app_id':data_dict['id']})    
            for i in topics_data:
                if i['display_name'] == other_topic:
                    tf.add_new_topic_rel(context, {'topic_id':i['id'], 'app_id':data_dict['id']})
    data = {}
    try:
        data_s = data_dict['tags']
    except KeyError:
        data_s = ""
    logging.warning(data_s)
    if len(data_s) > 2:
        logging.warning('len(data_s) > 2')
        helper = [x.strip() for x in data_s.split(',') if x.strip()!='']
        tgs = ""
        for i in helper:
            tgs+= i+', '
        data['tags'] = tgs[0:-2]
            
       
        try:
            data2 = {'id': 'app_tag'}
            toolkit.get_action('vocabulary_show')(context, data2)
            logging.info("Example genre vocabulary already exists, skipping.")
        except toolkit.ObjectNotFound:
            logging.info("Creating vocab 'app_tag'")
            data2 = {'name': 'app_tag'}
            vocab = toolkit.get_action('vocabulary_create')(context, data2)
            for tag in helper:
                logging.info(
                        "Adding tag {0} to vocab 'country_codes'".format(tag))
                data2 = {'name': tag, 'vocabulary_id': vocab['id']}
                toolkit.get_action('tag_create')(context, data2)
        except toolkit.ValidationError:
            logging.info("Creating vocab 'app_tag'")
            data2 = {'name': 'app_tag'}
            vocab = toolkit.get_action('vocabulary_create')(context, data2)
            for tag in helper:
                logging.info(
                        "Adding tag {0} to vocab 'country_codes'".format(tag))
                data2 = {'name': tag, 'vocabulary_id': vocab['id']}
                toolkit.get_action('tag_create')(context, data2)
        related_extra.mod_extra_data(context, {'related_id':data_dict['id'], 'key': "tags", 'value': data['tags']})
    return _('done')
    
@toolkit.side_effect_free    
def new_app_api(context, data_dict=None):
    '''Create a new application.
        You must be authorized to create new application. '''
    _check_access('app_create', context)
    data_to_commit = model.related.Related()
    try:
        title = data_dict['title'] 
    except KeyError:
        title = ""
    try:
        description= data_dict['description']
    except KeyError:
        description  = ""
    try:
        url = data_dict['url']
    except KeyError:
        url = ""
    try:
        image_url = data_dict['image_url'] 
    except KeyError:
        image_url  = ""
    try:
        datasets = data_dict['datasets'] 
    except KeyError:
        datasets  = ""
    try:
        owner = data_dict['owner'] 
    except KeyError:
        owner  = c.userobj.fullname
    data_to_commit.id = unicode(uuid.uuid4())
    if len(title) == 0:
        ed = {'message': 'Application name too short'}
        raise logic.ValidationError(ed)
       
    datasets = datasets.split(',')
    ds = []
    for i in datasets:
        tester = valid_dataset(i)
        if tester == True:
            ds.append(i)
        elif type(tester) != bool:
            ds.append(i)
    if len(ds) == 0:
        
        ed = {'message': 'Failed to create application, at least 1 dataset is required'}
        raise logic.ValidationError(ed)
    #########################################################################################

    try:
        tags__ = data_dict['tags'] 
    except KeyError:
        ed = {'message': 'Failed to create application, at least 1 tag is required'}
        raise logic.ValidationError(ed)

    helper = [x.strip() for x in tags__.split(',') if x.strip()!='']
    tgs = ""
    for i in helper:
        tgs+= i+', '
    dat = {}
    dat['tags'] = tgs[0:-2]
    tags_array = dat['tags'].split(', ')

    try:
        data2 = {'id': 'app_tag'}
        toolkit.get_action('vocabulary_show')(context, data2)
        logging.info("Example genre vocabulary already exists, skipping.")
    except toolkit.ObjectNotFound:
        logging.info("Creating vocab 'app_tag'")
        data2 = {'name': 'app_tag'}
        vocab = toolkit.get_action('vocabulary_create')(context, data2)
        for tag in tags_array:
            logging.info(
                    "Adding tag {0} to vocab 'app_tag'".format(tag))
            data2 = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data2)
    except toolkit.ValidationError:
        logging.info("Creating vocab 'app_tag'")
        data2 = {'name': 'app_tag'}
        vocab = toolkit.get_action('vocabulary_create')(context, data2)
        for tag in tags_array:
            logging.info(
                    "Adding tag {0} to vocab 'app_tag'".format(tag))
            data2 = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data2)

    #########################################################################################
    try:
        other_topic = data_dict['topics']
    except KeyError:
        ed = {'message': 'Failed to create application, at least 1 tag is required'}
        raise logic.ValidationError(ed)

    topics = tf.get_all_topic_names(context, data_dict)
    if len(other_topic) > 4:
        if other_topic not in topics:
            tf.add_new_app_topic(context, {'display_name':other_topic})
        topics_data = tf.get_all_topics(context, data_dict)   
        logging.warning("topics_data")
        logging.warning(topics_data) 
        for i in topics_data:
            if i['display_name'] == other_topic:
                tf.add_new_topic_rel(context, {'topic_id':i['id'], 'app_id':data_to_commit.id})
    topics_to_add = []
    topics_data = tf.get_all_topics(context, data_dict)
    logging.warning("topics_data2")
    logging.warning(topics_data) 
    #for i in data.keys():
    #    for j in topics_data:
    #        if j['display_name'] == i:
    #            logging.warning("j['display_name'] == i"+i+"=="+j['display_name'])
    #            dat[i] = ''
    #            tf.add_new_topic_rel(context, {'topic_id':j['id'], 'app_id':data_to_commit.id})
    #########################################################################################
    
    owner_id = c.userobj.id
    data_to_commit.title = title
    data_to_commit.description = description
    data_to_commit.url = url
    data_to_commit.image_url = image_url
    data_to_commit.created = datetime.datetime.now()
    data_to_commit.owner_id = owner_id
    data_to_commit.type = 'application'
    data_dict2 = {'related_id':data_to_commit.id,'key':'privacy'}
    model.Session.add(data_to_commit)
    add_datasets(ds,  data_to_commit.id)
    __builtin__.value = 'private'
    related_extra.new_related_extra(context, data_dict2)
    related_extra.add_app_owner(context, {'related_id':data_to_commit.id,'key':'owner', 'value':owner})
    related_extra.add_extra_data(context, {'related_id': data_to_commit.id,'value': dat['tags'], 'key':'tags'})
    
    model.Session.commit()
    c.result =_('done')
    return c.result

def datasets(id):
        ds_ids = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == id).all()
        ds_id = []
        result= []
        for i in ds_ids:
            ds_id.append(i.dataset_id)
        for i in ds_id:
            pack = model.Session.query(model.Package).filter(model.Package.id == i).first()
            if pack != None:
                result.append(pack.name)
        return result
import sys

@toolkit.side_effect_free
def delete_app(context, data_dict=None):
    '''
        Mod_app_api - delete app
        params:
        -id: dataset id -required
        -id: String
        -header: Authorization
    '''
    logic.get_action('related_show')(context,data_dict)

    rel = model.Session.query(model.Related).filter(model.Related.id == data_dict['id']).first()
    rel_datasets = model.Session.query(model.RelatedDataset).filter(model.Related.id == data_dict['id']).all()
    data_dict['owner_id'] = rel.owner_id
    _check_access('app_edit', context, data_dict)

    d_dtopic = {'app_id':data_dict['id']}
    tf.del_topic_rel(context, d_dtopic)

    logging.warning(rel_datasets)
    model.Session.delete(rel)
    model.Session.commit()
    related_extra.del_related_extra(context, {'related_id':data_dict['id']})
    model.Session.commit()
    c.result = _('done')
    return c.result

@toolkit.side_effect_free
def list_apps(context, data_dict=None):
    """ List all related items regardless of dataset """
    
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj,
               'for_view': True}
    params_nopage = [(k, v) for k, v in base.request.params.items()
                     if k != 'page']
    try:
        page = int(base.request.params.get('page', 1))
    except ValueError:
        base.abort(400, ('"page" parameter must be an integer'))

    # Update ordering in the context
    related_list = logic.get_action('related_list')(context, data_dict)

    def search_url(params):
        url = h.url_for(controller='ckanext.applications.apps:AppsController', action='dashboard')
        params = [(k, v.encode('utf-8')
                  if isinstance(v, basestring) else str(v))
                  for k, v in params]
        return url + u'?' + urllib.urlencode(params)

    def pager_url(q=None, page=None):
        params = list(params_nopage)
        params.append(('page', page))
        return search_url(params)

    public_list = []
    c.pr = []
    c.priv_private = False
    c.privonly = base.request.params.get('private', '') == 'on'


    for i in related_list:
        data_dict = {'related_id':i['id'],'key':'privacy'}
        if related_extra.check_priv_related_extra(context, data_dict):
            public_list.append(i)
        else:
            data_dict = {'owner_id': i['owner_id']}
            try:
                logic.check_access('app_edit', context, data_dict)
                c.priv_private = True
                public_list.append(i)
            except logic.NotAuthorized:
                logging.warning("access denied")
        
        
    c.page = h.Page(
        collection=public_list,
        page=page,
        url=pager_url,
        item_count=len(public_list),
        items_per_page=9
    )

    c.filters = dict(params_nopage)

    c.type_options =({"text": _("API"), "value": "api"},
            {"text": _("Application"), "value": "application"},
            {"text": _("Idea"), "value": "idea"},
            {"text": _("News Article"), "value": "news_article"},
            {"text": _("Paper"), "value": "paper"},
            {"text": _("Post"), "value": "post"},
            {"text": _("Visualization"), "value": "visualization"})
    c.sort_options = (
        {'value': 'view_count_desc', 'text': _('Most Viewed')},
        {'value': 'view_count_asc', 'text': _('Least Viewed')},
        {'value': 'created_desc', 'text': _('Newest')},
        {'value': 'created_asc', 'text': _('Oldest')}
    )
    g = []
    app_id = base.request.params.get('id', '')
    search_keyword = base.request.params.get('search', '')
    tag = base.request.params.get('tag', '')
    topic = base.request.params.get('topic', '')
    tr=[]
    for i in range(len(public_list)):
        public_list[i]['datasets'] = datasets(public_list[i]['id'])
    for i in range(len(public_list)):
        user_id = public_list[i]['owner_id']
        public_list[i].pop('owner_id')
        public_list[i].pop('view_count')
        public_list[i].pop('featured')
        public_list[i]['tags'] = related_extra.apps_tags(context, {'related_id':public_list[i]['id']})
        public_list[i]['topics'] = tf.get_apps_topics(context, {'app_id':public_list[i]['id']})
        if tag != '':
            if tag not in public_list[i]['tags']:
                tr.append(i.strip())
        if topic != '':
            if topic not in public_list[i]['topics']:
                tr.append(i)
        full_name = model.Session.query(model.User).filter(model.User.id == user_id).first().fullname
        public_list[i]['full_name'] = related_extra.get_app_owner(context, {'related_id':public_list[i].get('id')})
    pl_buffer = []
    for i in range(len(public_list)):
        if i not in tr:
            pl_buffer.append(public_list[i])

    public_list = pl_buffer[:]
    if (app_id == '' or app_id == None) and (search_keyword =='' or search_keyword == None):
        data = {}

        data['result'] = public_list[:]
        
        c.list = data
        return c.list
    elif (app_id != '' or app_id != None) and (search_keyword =='' or search_keyword == None):
        for i in public_list:
            if app_id == i['id']:
               g.append(i) 
               c.list = g[:]
    elif (app_id == '' or app_id == None) and (search_keyword !='' or search_keyword != None):
        for i in public_list:
            if (search_keyword.lower() in i['title'].lower()) or (search_keyword.lower() in i['description'].lower()):
                g.append(i)
        helper = []
        c.list =  g[:]
    else:
        for i in public_list:
            if app_id == i['id']:
               g.append(i) 
        result = [] 
        for j in g:
            if (search_keyword.lower() in j['title'].lower()) or (search_keyword.lower() in j['description'].lower()):
                result.append(j)
        c.list = result[:]
    if len(g) == 0:
        c.list =  [_("no results found")]
    return c.list

log = logging.getLogger('ckanext_applications')

def own(id):
    owner_id = model.Session.query(model.Related) \
                .filter(model.Related.id == id).first()
    owner_id = owner_id.owner_id
    if c.userobj != None and owner_id == c.userobj.id:
        return True 
    return False
def app_name(id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}

    app_name = model.Session.query(model.Related).filter(model.Related.id == id).first().title
    return app_name



class AppsController(base.BaseController):
    

    def delete_all_reports(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        try:
            logic.check_access('app_editall', context)
        except logic.NotAuthorized:
            base.abort(401, base._('Not authorized to see this page'))

        related_id = str(base.request.params.get('related_id',''))

        data_dict = {'related_id': related_id, 'key': 'report'}
        if db.related_extra_table is None:
            db.init_db(context['model'])
        data_dict = {'related_id': related_id, 'key': 'report'}
        data_dict2 = {'related_id': related_id, 'key': 'reported_by'}
        res = db.RelatedExtra.delete(**data_dict)  
        res = db.RelatedExtra.delete(**data_dict2) 
        session = context['session']
        session.commit()
        return base.render('reports/admin.html')
    def list_reports(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        try:
            logic.check_access('app_editall', context)
        except logic.NotAuthorized:
            base.abort(401, base._('Not authorized to see this page'))
        try:
            c.page = int(base.request.params.get('page', 1))
        except ValueError:
            base.abort(400, ('"page" parameter must be an integer'))

        c.filter = base.request.params.get('id','')
        
        
        return base.render('reports/admin.html')


    def report_app(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        if context['auth_user_obj']: 
            user_id = context['auth_user_obj'].id
        else:
            base.abort(401, base._('Not authorized to see this page'))
        report = logic.clean_dict(df.unflatten(logic.tuplize_dict(logic.parse_params(base.request.params))))
        app_id = report['app_id']
        key= 'report'
        value = report['report_text']
        #logging.warning('///////////////value /////////////////////')
        #logging.warning(value)
        value = value.replace('\r\n', '\n')
        if len(value) > 500:
            value = value[:500]
        logging.warning(value)
        id_ = unicode(uuid.uuid4())
        if related_extra.reported_by_user(c.userobj.id, app_id) == False:
            rep_id = related_extra.reported_id(app_id, c.userobj.id)
            related_extra.update_report(context, {'id':rep_id, 'related_id': app_id,'key': key, 'value':value})
            return h.redirect_to(controller='ckanext.applications.detail:DetailController', action='detail', id=app_id)
        data_dict = {
            'id': id_,
            'related_id': app_id,
            'key': key,
            'value': value
        }
        related_extra.new_report(context, data_dict)
        id2 = unicode(uuid.uuid4())
        data = {'related_id': app_id,
            'key': key,
            'value': value}
        report_id = db.RelatedExtra.get(**data)
        data_dict2 = {
            'id': id2,
            'related_id': app_id,
            'key': 'reported_by',
            'value': c.userobj.id+"*"+report_id[0].id
        }
        related_extra.new_report(context, data_dict2)
        return h.redirect_to(controller='ckanext.applications.detail:DetailController', action='detail', id=app_id)

    def delete_app_report(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        report = base.request.params.get('report_id','')
        

        data_dict = {'id': report}
        info = db.RelatedExtra.get(**data_dict)
        data_dict2 = {'related_id': info[0].related_id, 'key':'reported_by'}
        report_user = db.RelatedExtra.get(**data_dict2)
        
        report_user = [x for x in report_user if x.value.split('*')[1] == report ]
        data_dict3 = {'id': report_user[0].id}
        try:
            logic.check_access('app_editall', context)
            related_extra.del_related_extra(context, data_dict)
            related_extra.del_related_extra(context, data_dict3)
        except logic.NotAuthorized:
            base.abort(401, base._('Not authorized to see this page'))

        return h.redirect_to(controller='ckanext.applications.apps:AppsController', action='list_reports')
        
    def new(self, id):
        return self._edit_or_new(id, None, False)

    def edit(self, id, related_id):
        return self._edit_or_new(id, related_id, True)
            
    def search(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {
            'type_filter': 'application',
            'sort': base.request.params.get('sort', ''),
            #'featured': base.request.params.get('featured', '')
        }
        
        name = base.request.params.get('app_name','')
        
        private_only = base.request.params.get('private','')
        if private_only == 'on':
            private_only = True
        else:
            private_only = False

        params_nopage = [(k, v) for k, v in base.request.params.items()
                         if k != 'page']
        try:
            page = int(base.request.params.get('page', 1))
        except ValueError:
            base.abort(400, ('"page" parameter must be an integer'))
    
        related_list = logic.get_action('related_list')(context, data_dict)
        # Update ordering in the context
        logging.warn('---search debug---')

        new_list2 = [x for x in related_list if name.lower() in x['description'].lower()]

        new_list = [x for x in related_list if name.lower() in x['title'].lower()]
        logging.warning("private test")
        c.priv_private = False
        public_list = []      
        for i in new_list:
            data_dict = {'related_id':i['id'],'key':'privacy'}
            if related_extra.check_priv_related_extra(context, data_dict):
                public_list.append(i)
            else:
                try:
                    logic.check_access('app_edit', context, {'owner_id': i['owner_id']})
                    c.priv_private = True
                    public_list.append(i)
                except logic.NotAuthorized:
                    logging.warning("access denied")
        pl = []
        if private_only:
            for i in public_list:
                data_dict = {'related_id':i['id'],'key':'privacy'}
                if related_extra.check_priv_related_extra(context, data_dict) == False:
                    pl.append(i)

        
        def search_url(params):
            url = h.url_for(controller='ckanext.applications.apps:AppsController', action='search')
            params = [(k, v.encode('utf-8')
                      if isinstance(v, basestring) else str(v))
                      for k, v in params]
            return url + u'?' + urllib.urlencode(params)

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)
        if private_only:
            c.page = h.Page(
                collection=pl,
                page=page,
                url=pager_url,
                item_count=len(pl),
                items_per_page=9
            )
        else:
            c.page = h.Page(
                collection=public_list,
                page=page,
                url=pager_url,
                item_count=len(public_list),
                items_per_page=9
            )

        c.filters = dict(params_nopage)
        c.name = name
        c.type_options = self._type_options()
        c.sort_options = (
            {'value': '', 'text': _('Most viewed')},
            {'value': 'view_count_desc', 'text': _('Most Viewed')},
            {'value': 'view_count_asc', 'text': _('Least Viewed')},
            {'value': 'created_desc', 'text': _('Newest')},
            {'value': 'created_asc', 'text': _('Oldest')}
        )
    

        return base.render("related/dashboard.html")

    def dashboard(self):
        """ List all related items regardless of dataset """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {
            'type_filter': 'application',
            'sort': base.request.params.get('sort', ''),
            'featured': base.request.params.get('featured', '')
        }

        params_nopage = [(k, v) for k, v in base.request.params.items()
                         if k != 'page']
        

        try:
            page = int(base.request.params.get('page', 1))
        except ValueError:
            base.abort(400, ('"page" parameter must be an integer'))

        # Update ordering in the context
        related_list = logic.get_action('related_list')(context, data_dict)

        def search_url(params):
            url = h.url_for(controller='ckanext.applications.apps:AppsController', action='dashboard')
            params = [(k, v.encode('utf-8')
                      if isinstance(v, basestring) else str(v))
                      for k, v in params]
            return url + u'?' + urllib.urlencode(params)

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        public_list = []
        c.pr = []
        c.priv_private = False
        c.privonly = base.request.params.get('private', '') == 'on'


        for i in related_list:
            data_dict = {'related_id':i['id'],'key':'privacy'}
            if related_extra.check_priv_related_extra(context, data_dict):
                public_list.append(i)
            else:
                data_dict = {'owner_id': i['owner_id']}
                try:
                    logic.check_access('app_edit', context, data_dict)
                    c.priv_private = True
                    public_list.append(i)
                except logic.NotAuthorized:
                    logging.warning("access denied")
            
        tag = base.request.params.get('tag', '')
        if tag != '':
            public_list2 = []
            for i in public_list:
                if related_extra.has_tag(context, {'related_id': i['id'], 'tag':tag}):
                    public_list2.append(i)  
        else:
            public_list2 = public_list

        topic = base.request.params.get('topic', '')
        public_list = []
        
        if topic != '':
            public_list = []
            for i in public_list2:
                if tf.has_topic(context, {'app_id': i['id'], 'topic':topic}):
                    public_list.append(i)  
        else:
            public_list = public_list2

        c.page = h.Page(
            collection=public_list,
            page=page,
            url=pager_url,
            item_count=len(public_list),
            items_per_page=9
        )

        c.filters = dict(params_nopage)

        c.type_options = self._type_options()
        c.sort_options = (
            {'value': 'view_count_desc', 'text': _('Most Viewed')},
            {'value': 'view_count_asc', 'text': _('Least Viewed')},
            {'value': 'created_desc', 'text': _('Newest')},
            {'value': 'created_asc', 'text': _('Oldest')}
        )

        return base.render("related/dashboard.html")
    
    def read(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id}

        try:
            logic.check_access('related_show', context, data_dict)
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))
        related = model.Session.query(model.Related) \
                .filter(model.Related.id == id).first()

        if not related:
            base.abort(404, _('The requested related item was not found'))

        related.view_count = model.Related.view_count + 1

        model.Session.add(related)
        model.Session.commit()

        base.redirect(related.url)

    def list(self, id):
        """ List all related items for a specific dataset """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id}
        response.headers['Content-Type'] = 'json'
        try:
            logic.check_access('package_show', context, data_dict)
        except logic.NotFound:
            base.abort(404, base._('Dataset not found'))
        except logic.NotAuthorized:
            base.abort(401, base._('Not authorized to see this page'))

        try:
            c.pkg_dict = logic.get_action('package_show')(context, data_dict)
            c.pkg = context['package']
            c.resources_json = h.json.dumps(c.pkg_dict.get('resources', []))
        except logic.NotFound:
            base.abort(404, base._('Dataset not found'))
        except logic.NotAuthorized:
            base.abort(401, base._('Unauthorized to read package %s') % id)

        return base.render("package/related_list.html")

    def _edit_or_new(self, id, related_id, is_edit):
        """
        Edit and New were too similar and so I've put the code together
        and try and do as much up front as possible.
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {}

        if is_edit:
            tpl = 'related/edit.html'
            auth_name = 'related_update'
            auth_dict = {'id': related_id}
            action_name = 'related_update'

            try:
                related = logic.get_action('related_show')(
                    context, {'id': related_id})
            except logic.NotFound:
                base.abort(404, _('Related item not found'))
        else:
            tpl = 'related/new.html'
            auth_name = 'related_create'
            auth_dict = {}
            action_name = 'related_create'

        try:
            logic.check_access(auth_name, context, auth_dict)
        except logic.NotAuthorized:
            base.abort(401, base._('Not authorized'))

        try:
            c.pkg_dict = logic.get_action('package_show')(context, {'id': id})
        except logic.NotFound:
            base.abort(404, _('Package not found'))

        data, errors, error_summary = {}, {}, {}

        if base.request.method == "POST":
            try:
                data = logic.clean_dict(
                    df.unflatten(
                        logic.tuplize_dict(
                            logic.parse_params(base.request.params))))

                if is_edit:
                    data['id'] = related_id
                else:
                    data['dataset_id'] = id
                data['owner_id'] = c.userobj.id

                related = logic.get_action(action_name)(context, data)

                if not is_edit:
                    h.flash_success(_("Related item was successfully created"))
                else:
                    h.flash_success(_("Related item was successfully updated"))

                h.redirect_to(
                    controller='ckanext.applications.apps:AppsController', action='list', id=c.pkg_dict['name'])
            except df.DataError:
                base.abort(400, _(u'Integrity Error'))
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
        else:
            if is_edit:
                data = related

        c.types = self._type_options()

        c.pkg_id = id
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        c.form = base.render("related/edit_form.html", extra_vars=vars)
        return base.render(tpl)

    def delete(self, id, related_id):
        if 'cancel' in base.request.params:
            h.redirect_to(controller='ckanext.applications.apps:AppsController', action='edit',
                          id=id, related_id=related_id)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            if base.request.method == 'POST':
                logic.get_action('related_delete')(context, {'id': related_id})
                h.flash_notice(_('Related item has been deleted.'))
                h.redirect_to(controller='ckanext.applications.apps:AppsController', action='read', id=id)
            c.related_dict = logic.get_action('related_show')(
                context, {'id': related_id})
            c.pkg_id = id
        except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to delete related item %s') % '')
        except logic.NotFound:
            base.abort(404, _('Related item not found'))
        return base.render('related/confirm_delete.html')

    def _type_options(self):
        '''
        A tuple of options for the different related types for use in
        the form.select() template macro.
        '''
        return ({"text": _("API"), "value": "api"},
                {"text": _("Application"), "value": "application"},
                {"text": _("Idea"), "value": "idea"},
                {"text": _("News Article"), "value": "news_article"},
                {"text": _("Paper"), "value": "paper"},
                {"text": _("Post"), "value": "post"},
                {"text": _("Visualization"), "value": "visualization"})

    def detail(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {
            'type_filter': 'application',
            'sort': base.request.params.get('sort', ''),
            #'featured': base.request.params.get('featured', '')
        }
        
        id = base.request.params.get('id','')
        c.id = id

        params_nopage = [(k, v) for k, v in base.request.params.items()
                         if k != 'page']
        try:
            page = int(base.request.params.get('page', 1))
        except ValueError:
            base.abort(400, ('"page" parameter must be an integer'))
    
        related_list = logic.get_action('related_list')(context, data_dict)
        # Update ordering in the context
        logging.warn('---search debug---')

        

        new_list = [x for x in related_list if id == x['id']]
        
        def search_url(params):
            url = h.url_for(controller='ckanext.applications.apps:AppsController', action='search')
            params = [(k, v.encode('utf-8')
                      if isinstance(v, basestring) else str(v))
                      for k, v in params]
            return url + u'?' + urllib.urlencode(params)

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)



        c.page = h.Page(
            collection=new_list,
            page=page,
            url=pager_url,
            item_count=len(new_list),
            items_per_page=9
        )

        c.filters = dict(params_nopage)
        
        c.type_options = self._type_options()
        c.sort_options = (
            {'value': '', 'text': _('Most viewed')},
            {'value': 'view_count_desc', 'text': _('Most Viewed')},
            {'value': 'view_count_asc', 'text': _('Least Viewed')},
            {'value': 'created_desc', 'text': _('Newest')},
            {'value': 'created_asc', 'text': _('Oldest')}
        )
    

        return base.render("related/dashboard.html")
    
def can_view(id):
    if own(id):
        return True
    context = {'model': model, 'session': model.Session,
                'user': c.user or c.author, 'auth_user_obj': c.userobj,
                'for_view': True}

    data_dict = {'related_id':id}
    try:
        _check_access('app_editall', context, data_dict)
        return True
    except toolkit.NotAuthorized, e:
        return False
    return False
def is_admin():
    context = {'model': model, 'session': model.Session,
                'user': c.user or c.author, 'auth_user_obj': c.userobj,
                'for_view': True}
    try:
        _check_access('app_editall', context)
        return True
    except toolkit.NotAuthorized, e:
         return False         
    return False

