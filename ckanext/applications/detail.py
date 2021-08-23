# coding=utf-8
import urllib

import datetime
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.common import _, c
import logging
import topic_functions as tf
import json
import os
from pylons import config

import related_extra

import ckan.logic
import __builtin__

data_path = "/data/"

abort = base.abort
_get_action = logic.get_action
_check_access = logic.check_access
log = logging.getLogger('ckanext_applications')

class DetailController(base.BaseController):  
    def list(self, id):
        """ List all related items for a specific dataset """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id}

        try:
            logic.check_access('package_show', context, data_dict)
        except logic.NotFound:
            base.abort(404, base._('Dataset not found'))
        except logic.NotAuthorized:
            base.abort(401, base._('Not authorized to see this page'))

        try:
            c.pkg_dict = logic.get_action('package_show')(context, data_dict)

            c.pkg = context['package']
            logging.warning(c.pkg)
            c.resources_json = h.json.dumps(c.pkg_dict.get('resources', []))
         
        
        except logic.NotFound:
            base.abort(404, base._('Dataset not found'))
        except logic.NotAuthorized:
            base.abort(401, base._('Unauthorized to read package %s') % id)
        logging.warning(c.pkg.related)

        related_list = []

        for i in c.pkg.related:
            data_dict = {'related_id':i.id,'key':'privacy'}
            if related_extra.check_priv_related_extra(context, data_dict):
                related_list.append(i)
            else:
                
                try:
                    logic.check_access('app_edit', context, data_dict)
                    related_list.append(i)
                except logic.NotAuthorized:
                    logging.warning("access denied")
                    
        c.pkg.related = related_list
        return base.render("package/related_list.html")

    def _type_options(self):
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
            'sort': base.request.params.get('sort', '')
        }
        
        id = base.request.params.get('id','')
        c.id = id
        extra = related_extra.get_extra_data(context, {"related_id":id})
        for i in extra:
            if i.key == 'tags':
                c.tags = i.value.split(',')
        params_nopage = [(k, v) for k, v in base.request.params.items()
                         if k != 'page']
        try:
            page = int(base.request.params.get('page', 1))
        except ValueError:
            base.abort(400, ('"page" parameter must be an integer'))
    
        related_list = logic.get_action('related_list')(context, data_dict)
        
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
        if len(new_list) == 0:
            base.abort(404, _('Application not found'))
        c.title = new_list[0]['title']
        c.description = new_list[0]['description']
        c.url = new_list[0]['url']
        c.created = ('.').join(new_list[0]['created'].split('T')[0].split('-'))
        self.owner_id = new_list[0]['owner_id']
        owner_id = self.owner_id
        c.img = new_list[0]['image_url']

        c.creator = new_list[0]['owner_id'] 
        c.owner = related_extra.get_app_owner(context, {"related_id":c.id})

        ds_ids = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == c.id).all()
        ds_id = []
        for i in ds_ids:
            ds_id.append(i.dataset_id)
        logging.warning(ds_id)
        c.datasets = []

        ###############################################
        c.topics = tf.get_apps_topics(context, {'app_id':id})
        ###############################################
        for i in ds_id:
            pack = model.Session.query(model.Package).filter(model.Package.id == i).first()
            c.datasets.append(pack.name)
        data_dict2 = {'related_id':c.id,'key':'privacy'}
        privacy_list = related_extra.get_related_extra(context, data_dict2)
        if len(privacy_list) == 0:
            c.private = "no information"
        else:
            c.private = privacy_list[0].value
        
        data_dict = {'related_id':c.id,'key':'privacy'}

        if related_extra.check_priv_related_extra(context, data_dict) == False:
            try:
                logic.check_access('app_edit', context, {'owner_id': owner_id})
            except logic.NotAuthorized:
                logging.warning("access denied")
                base.abort(404, ('Application not found'))

        logging.warning(c.datasets)
        logging.warning(c.private)
        logging.warning(c.owner)
        return base.render("related/dashboard.html")
        
    def new_app(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        try:
            _check_access('app_create', context)
        except toolkit.NotAuthorized, e:
            toolkit.abort(401, e.extra_msg)
        all_apps = model.Session.query(model.Package).filter(model.Package.name != "").all()
        c.app_names = []
        for i in all_apps:
            c.app_names.append(i.name)
        logging.warning(c.app_names)
        logging.warning("before topics init...")
        data_dict = {}
        #tf.create_topic_rel_table(context)
        #tf.create_new_app_topic_db(context)
        logging.warning("after topics init...")
        c.dataset = base.request.params.get('dataset','')        
        if base.request.cookies.has_key("edemo_vars"):
            __builtin__.vars = json.loads(base.request.cookies.pop("edemo_vars"))
            base.response.delete_cookie("edemo_vars")
        return base.render("related/dashboard.html")


    def new_app_in(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        context_ignore_auth = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True, 'ignore_auth': True}
        data_dict = {}
        data = {}

        related = logic.clean_dict(df.unflatten(logic.tuplize_dict(logic.parse_params(base.request.params))))
        data = related
        logging.warning('post data values:')
        logging.warning(data)
        owner_id = c.userobj.id
        
        data_to_commit = model.related.Related()

        logging.warning(data_to_commit)   

        data_to_commit.id = unicode(uuid.uuid4())
        data_to_commit.title = data['title']
        data_to_commit.description = data['description']
        data_to_commit.url = data['url']
        data_to_commit.image_url = data['image_url']
        data_to_commit.created = datetime.datetime.now()
        data_to_commit.owner_id = owner_id
        data_to_commit.type = 'application'
        errors, error_summary, dat = {}, {}, {}
        dat["title"] = data_to_commit.title
        dat["owner"] = data["owner"]
        dat["description"] = data_to_commit.description
        dat["url"] = data_to_commit.url
        dat["image_url"] = data_to_commit.image_url
        dat["datasets"] = data['datasets']
        logging.warning(data)
        ###############################
        other_topic = data['other']
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
        for i in data.keys():
            for j in topics_data:
                if j['display_name'] == i:
                    logging.warning("j['display_name'] == i"+i+"=="+j['display_name'])
                    dat[i] = ''
                    tf.add_new_topic_rel(context, {'topic_id':j['id'], 'app_id':data_to_commit.id})

        ###############################
        helper = [x.strip() for x in data['tags'].split(',') if x.strip()!='']
        tgs = ""
        for i in helper:
            tgs+= i+', '
        dat['tags'] = tgs[0:-2]
        tags_array = dat['tags'].split(', ')

        try:
            data2 = {'id': 'app_tag'}
            toolkit.get_action('vocabulary_show')(context, data2)
            logging.info("Example genre vocabulary already exists, skipping.")
        except toolkit.ObjectNotFound:
            logging.info("Creating vocab 'app_tag'")
            data2 = {'name': 'app_tag'}
            vocab = toolkit.get_action('vocabulary_create')(context_ignore_auth, data2)
            for tag in tags_array:
                logging.info(
                        "Adding tag to vocab 'app_tag'")
                data2 = {'name': tag, 'vocabulary_id': vocab['id']}
                toolkit.get_action('tag_create')(context, data2)
        except toolkit.ValidationError:
            logging.info("Creating vocab 'app_tag'")
            data2 = {'name': 'app_tag'}
            vocab = toolkit.get_action('vocabulary_create')(context_ignore_auth, data2)
            for tag in tags_array:
                logging.info(
                        "Adding tag to vocab 'app_tag'")
                data2 = {'name': tag, 'vocabulary_id': vocab['id']}
                toolkit.get_action('tag_create')(context, data2)


        __builtin__.vars = {}
        c.errorrs = {}
        datasets = data['datasets'].split(',')
        if len(data_to_commit.title) > 3 and len(data_to_commit.url) > 3 and len(dat['tags']) >= 3 : #and topic_:
            model.Session.add(data_to_commit)
            
            datasets_bool  = self.add_datasets(datasets,  data_to_commit.id)
            data_dict = {'related_id':data_to_commit.id,'key':'privacy'}
            __builtin__.value = 'private'
            related_extra.new_related_extra(context, data_dict)
            related_extra.add_app_owner(context, {'related_id': data_to_commit.id,'key':'owner', 'value': dat["owner"] })

            related_extra.add_extra_data(context, {'related_id': data_to_commit.id,'value': dat['tags'], 'key':'tags'})

            if datasets_bool:
                model.Session.commit()
                
                __builtin__.vars = {}
                recipients_string = config.get('ckanext.edem.apps.notification_recipients')
                if recipients_string:
                    recipients = [(x,'') for x in recipients_string.split(',')]
                    subject = 'EDEMO: Registrácia novej aplikácie'
                    message=u'''Nová aplikácia bola zaregistrovaná.
                    
Názov: {title}
Popis: {description}
Vlastník: {owner}
Adresa: {url}
                    '''
                    message = message.format(title=data_to_commit.title,description=data_to_commit.description,owner=data["owner"],url=data_to_commit.url)
                    data_notification = {'entity_id' : c.userobj.id,
                    'entity_type' : 'user',
                    'subject' : subject,
                    'message' : message,
                    'recipients' : recipients}
                    toolkit.get_action('send_general_notification')(context, data_notification)
                return toolkit.redirect_to(controller='ckanext.applications.apps:AppsController', action='dashboard')
            else:
                errors['datasets'] = _("Invalid dataset(s)")
                vars = {'errors': errors, 'data':dat}    
                __builtin__.vars = vars
                base.response.set_cookie("edemo_vars",json.dumps(vars))                
                return toolkit.redirect_to(controller='ckanext.applications.detail:DetailController', action='new_app')
        else:
            if len(data_to_commit.title) < 3:
                errors['title'] = _("Title too short")
            if len(data_to_commit.url) < 3:
                errors['url'] = _("URL incorrect")
            
            if len(dat['tags']) < 3:
                errors['tags'] = _("At least 1 tag required. (min. lenght 3 chars.)")  
            for i in datasets:
                id_query = model.Session.query(model.Package).filter(model.Package.name == i).first()
                if id_query == None:
                    logging.warning('redirecting...')
                    errors['datasets'] = _("Invalid dataset(s)")
            vars = {'errors': errors, 'data':dat}    
            __builtin__.vars = vars           
            base.response.set_cookie("edemo_vars",json.dumps(vars))            

            return toolkit.redirect_to(controller='ckanext.applications.detail:DetailController', action='new_app')



    def add_datasets(self, datasets,  id):
        related_ids = []
        for i in datasets:
            id_query = model.Session.query(model.Package).filter(model.Package.name == i).first()
            if id_query == None:
                logging.warning('redirecting...')
                return False
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
        return True
        
    def edit_app(self):
        
        id = base.request.params.get('id','')
        data_from_db = model.Session.query(model.Related).filter(model.Related.id == id).first()
        if data_from_db == None:
            base.abort(404, _('Application not found'))
        
        context = {'user' : c.user} 
        data_dict = {'owner_id' : data_from_db.owner_id}
        try:
            _check_access('app_edit', context, data_dict)
        except toolkit.NotAuthorized, e:
            toolkit.abort(401, e.extra_msg)
        
        
        logging.warning(data_from_db)
        data, errors, error_summary = {}, {}, {}
        data["id"] = data_from_db.id
        data["type"] = data_from_db.type
        data["title"] = data_from_db.title
        data["description"] = data_from_db.description
        data["image_url"] = data_from_db.image_url
        data["url"] = data_from_db.url
        data["created"] = data_from_db.created
        data["owner_id"] = data_from_db.owner_id
        data["view_count"] = data_from_db.view_count
        data["featured"] = data_from_db.featured
        data["owner"] = related_extra.get_app_owner(context, {"related_id":id})
        bf = related_extra.get_data(context, {"related_id":id})
        logging.warning(data)
        data['tags'] = "" 
        for tag in bf["tags"]:
            data["tags"] += tag

        c.id = data["id"]
        c.data = data
        c.tags = data['tags']
        c.errors  = errors
        c.error_summary = error_summary
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        c.topics = tf.get_apps_topics(context, {'app_id':data['id']})

        name_query = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == data["id"] ).all()
        names = []
        for i in name_query:
            names.append(i.dataset_id)
            
        dataset_names = []
        for i in names:
            query_data = model.Session.query(model.Package).filter(model.Package.id == i).first()
            dataset_names.append(query_data.name)
        logging.warning(dataset_names)
        data['datasets'] = ",".join(dataset_names)
        c.datasets = data['datasets']
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        return base.render("related/update.html", extra_vars = vars)

    def edit_app_do(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data, errors, error_summary = {}, {}, {}
        id = base.request.params.get('id','')
        valid = model.Session.query(model.Related).filter(model.Related.id == id).first()
        if valid == None:
            base.abort(404, _('Application not found'))

        data = {}

        related = logic.clean_dict(df.unflatten(logic.tuplize_dict(logic.parse_params(base.request.params))))
        data = related
        logging.warning('post data values:')
        logging.warning(data)
        old_data = model.Session.query(model.Related).filter(model.Related.id == id).first()

        logging.warning(type(old_data))

        old_data.title = data["title"] 
        old_data.description =data["description"]
        old_data.image_url =data["image_url"] 
        old_data.url =data["url"] 

        c.data = old_data
        c.errors  = errors
        c.error_summary = {}
        ########################################
        error_summary = {}
        other_topic = data['other']
        topics = tf.get_all_topic_names(context, {'app_id':data['id']})
        if len(other_topic) > 4:
            if other_topic not in topics:
                tf.add_new_app_topic(context, {'display_name':other_topic})
            topics_data = tf.get_all_topics(context, {'app_id':data['id']})    
            for i in topics_data:
                if i['display_name'] == other_topic:
                    tf.add_new_topic_rel(context, {'topic_id':i['id'], 'app_id':data['id']})
        topics_to_add = []
        topics_data = tf.get_all_topics(context, {'app_id':data['id']})
        for i in data.keys():
            for j in topics_data:
                if j['display_name'] == i:
                    tf.add_new_topic_rel(context, {'topic_id':j['id'], 'app_id':data['id']})
        ########################################
        helper = [x.strip() for x in data['tags'].split(',') if x.strip()!='']
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
            for tag in tags_array:
                logging.info(
                        "Adding tag {0} to vocab 'country_codes'".format(tag))
                data2 = {'name': tag, 'vocabulary_id': vocab['id']}
                toolkit.get_action('tag_create')(context, data2)
        except toolkit.ValidationError:
            logging.info("Creating vocab 'app_tag'")
            data2 = {'name': 'app_tag'}
            vocab = toolkit.get_action('vocabulary_create')(context, data2)
            for tag in tags_array:
                logging.info(
                        "Adding tag {0} to vocab 'country_codes'".format(tag))
                data2 = {'name': tag, 'vocabulary_id': vocab['id']}
                toolkit.get_action('tag_create')(context, data2)
        ds = []

        if len(data['title']) < 3:
            errors['title'] = [_('Title too short')]
        if len(data['owner']) < 3:
            errors['owner'] = [_('Invalid owner')]
        if len(data['url']) < 3:
            errors['url'] = [_("URL incorrect")]
        if len(data['tags']) < 3:
            errors['tags'] = [_("At least 1 tag required. (min. lenght 3 chars.)")]
        for i in data['datasets'].split(','):
                id_query = model.Session.query(model.Package).filter(model.Package.name == i).first()
                if id_query == None:
                    errors['datasets'] = [_("Invalid dataset(s)")]
                else:
                    ds.append(i)
        c.datasets = ",".join(ds)
        if len(errors) > 0:
            return base.render("related/update.html")

        related_datasets = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == id).all()
        logging.warning('rows to delete...\n'+str(related_datasets))
        for i in related_datasets:
            model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.id == i.id).delete(synchronize_session=False)
        model.Session.commit()
        #model.Session.add(old_data)
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}

        data_dict = {'related_id':id,'key':'privacy'}

        related_extra.mod_extra_data(context, {'related_id':id, 'key': "tags", 'value': data['tags']})
        try:
            _check_access('app_editall', context, data_dict)
            __builtin__.value = data['private']
        except toolkit.NotAuthorized, e:
            __builtin__.value = 'private'
        
        related_extra.mod_related_extra(context, data_dict)

        model.Session.commit()

        datasets = data['datasets'].split(',')
        self.add_datasets(datasets, id)
        related_extra.mod_app_owner(context, {'related_id':id, 'key':'owner', 'value':data['owner']})
        return toolkit.redirect_to(controller='ckanext.applications.apps:AppsController', action='dashboard')
        
    def delete_app(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        
        id = base.request.params.get('id','')

        logging.warning('deleting...')
        logging.warning(id)

        valid = model.Session.query(model.Related).filter(model.Related.id == id).first()
        if valid == None:
            logging.warning('application not found')
            base.abort(404, _('Application not found'))

        data_dict = {'owner_id' : valid.owner_id}
        try:
            _check_access('app_edit', context, data_dict)
        except toolkit.NotAuthorized, e:
            toolkit.abort(401, e.extra_msg)
            
        rel = model.Session.query(model.Related).filter(model.Related.id == id).first()
        rel_datasets = model.Session.query(model.RelatedDataset).filter(model.Related.id == id).all()
        
        model.Session.delete(rel)
        model.Session.commit()
        logging.warning(' related datasets >>>>')
        logging.warning(rel_datasets)
        data_dict = {'related_id':id}

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        related_extra.del_related_extra(context, data_dict)
        d_dtopic = {'app_id':id}
        tf.del_topic_rel(context, d_dtopic)
        model.Session.commit()
        return toolkit.redirect_to(controller='ckanext.applications.apps:AppsController', action='dashboard')

def errors_and_other_stuff():
    return __builtin__.vars
def del_xtra():
    __builtin__.vars = None
    __builtin__.vars = {}
    return __builtin__.vars
