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

import json

abort = base.abort
_get_action = logic.get_action
_check_access = logic.check_access
#log = logging.getLogger('ckanext_apps_and_ideas')
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
def check_priv_related_extra(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra.get(**data_dict)
    index = 0
    for i in range(len(info)):
        if info[i].key == 'privacy':
            index == i
    info[index].related_id = data_dict.get('related_id')
    if own(data_dict['related_id']):
        return True
    logging.warning(info[index].value)
    return info[index].value == 'public'
 
def own(id):
    owner_id = model.Session.query(model.Related) \
                .filter(model.Related.id == id).first()
    owner_id = owner_id.owner_id
    if c.userobj != None and owner_id == c.userobj.id:
        return True 
    return False


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


def check(id):
    API_KEY = base.request.params.get('apikey', '')
    if len(c.user) == 0 and len(API_KEY) != 0:
        c.user = model.Session.query(model.User).filter(model.User.apikey == API_KEY).first().name

    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id':id,'key':'privacy'}
    return check_priv_related_extra(context, data_dict)

@ckan.logic.side_effect_free
def mod_related_extra(context, data_dict):
    create_related_extra_table(context)
    info = db.RelatedExtra.get(**data_dict)
    index = 0
    for i in range(len(info)):
        if info[i].key == 'privacy':
            index == i
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

class AppsController(base.BaseController):
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
            if check_priv_related_extra(context, data_dict):
                public_list.append(i)
            else:
                try:
                    logic.check_access('app_edit', context, {'owner_id': i['owner_id']})
                    c.priv_private = True
                    public_list.append(i)
                except logic.NotAuthorized:
                    logging.warning("access denied")
        

        
        def search_url(params):
            url = h.url_for(controller='ckanext.apps_and_ideas.apps:AppsController', action='search')
            params = [(k, v.encode('utf-8')
                      if isinstance(v, basestring) else str(v))
                      for k, v in params]
            return url + u'?' + urllib.urlencode(params)

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

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
            url = h.url_for(controller='ckanext.apps_and_ideas.apps:AppsController', action='dashboard')
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
            if check_priv_related_extra(context, data_dict):
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
                    controller='ckanext.apps_and_ideas.apps:AppsController', action='list', id=c.pkg_dict['name'])
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
            h.redirect_to(controller='ckanext.apps_and_ideas.apps:AppsController', action='edit',
                          id=id, related_id=related_id)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            if base.request.method == 'POST':
                logic.get_action('related_delete')(context, {'id': related_id})
                h.flash_notice(_('Related item has been deleted.'))
                h.redirect_to(controller='ckanext.apps_and_ideas.apps:AppsController', action='read', id=id)
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
            url = h.url_for(controller='ckanext.apps_and_ideas.apps:AppsController', action='search')
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
    def list_apps_json(self):
        """ List all related items regardless of dataset """
        API_KEY = base.request.params.get('apikey', '')
        if len(c.user) == 0 and len(API_KEY) != 0:
            c.user = model.Session.query(model.User).filter(model.User.apikey == API_KEY).first().name

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
            url = h.url_for(controller='ckanext.apps_and_ideas.apps:AppsController', action='dashboard')
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
            if check_priv_related_extra(context, data_dict):
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

        c.type_options = self._type_options()
        c.sort_options = (
            {'value': 'view_count_desc', 'text': _('Most Viewed')},
            {'value': 'view_count_asc', 'text': _('Least Viewed')},
            {'value': 'created_desc', 'text': _('Newest')},
            {'value': 'created_asc', 'text': _('Oldest')}
        )
        g = []
        app_id = base.request.params.get('id', '')
        search_keyword = base.request.params.get('search', '')
        for i in range(len(public_list)):
            public_list[i]['datasets'] = self.datasets(public_list[i]['id'])
        for i in range(len(public_list)):
            user_id = public_list[i]['owner_id']
            public_list[i].pop('owner_id')
            full_name = model.Session.query(model.User).filter(model.User.id == user_id).first().fullname
            public_list[i]['full_name'] = full_name

        if (app_id == '' or app_id == None) and (search_keyword =='' or search_keyword == None):
            data = {}
            data['help'] = 'all apps'
            data['sucess'] =True
            data['result'] = public_list
            
            c.list = json.dumps(data, encoding='utf8')
            return c.list
        elif (app_id != '' or app_id != None) and (search_keyword =='' or search_keyword == None):
            for i in public_list:
                if app_id == i['id']:
                   g.append(i) 
                   c.list = json.dumps({"help": "1 app","sucess":True, "result": i}, encoding='utf8')
        elif (app_id == '' or app_id == None) and (search_keyword !='' or search_keyword != None):
            for i in public_list:
                if (search_keyword.lower() in i['title'].lower()) or (search_keyword.lower() in i['description'].lower()):
                    g.append(i)
            helper = []
            #for i in range(len(g)):
                #g[i]['datasets'] = self.datasets(g[i]['id'])

            c.list = json.dumps({"help": "search results","sucess":True, "result": g}, encoding='utf8')
        else:
            for i in public_list:
                if app_id == i['id']:
                   g.append(i) 
            result = [] 
            for j in g:
                if (search_keyword.lower() in j['title'].lower()) or (search_keyword.lower() in j['description'].lower()):
                    #j['datasets'] = self.datasets(j['id'])
                    result.append(j)
            c.list = json.dumps({"help": "search results","sucess":True, "result": result}, encoding='utf8')
        if len(g) == 0:
            c.list = json.dumps({"help": "1 app","sucess":False, "result": _("no results found")}, encoding='utf8') 

        return c.list

    def datasets(self, id):
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


    def delete_app(self):
        id = base.request.params.get('id','')
        logging.warning('deleting...')
        logging.warning(id)

        valid = model.Session.query(model.Related).filter(model.Related.id == id).first()
        if valid == None:
            logging.warning('application not found')
            #base.abort(404, _('Application not found'))
            c.result = json.dumps({'help': 'delete app', 'success':False, 'result': _('app not found')})
            return c.result
        API_KEY = base.request.params.get('apikey','')
        logging.warning('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        logging.warning(API_KEY)
        if len(c.user) == 0 and len(API_KEY) != 0:
            c.user = model.Session.query(model.User).filter(model.User.apikey == API_KEY).first().name
            logging.warning(c.user)
        context = {'user' : c.user} 
        data_dict = {'owner_id' : valid.owner_id}
        try:
            _check_access('app_edit', context, data_dict)
        except toolkit.NotAuthorized, e:
            c.result = json.dumps({'help': 'delete app', 'success':False, 'result': _('not authorized')})
            return c.result
            #toolkit.abort(401, e.extra_msg)
            
        rel = model.Session.query(model.Related).filter(model.Related.id == id).first()
        rel_datasets = model.Session.query(model.RelatedDataset).filter(model.Related.id == id).all()
        logging.warning(rel_datasets)
        model.Session.delete(rel)
        model.Session.commit()
        #for i in rel_datasets:
        #    model.Session.delete(i)
        #model.Session.commit()

        data_dict = {'related_id':id}
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        del_related_extra(context, data_dict)
        model.Session.commit()
        c.result = json.dumps({'help': 'delete app', 'success':True, 'result': _('done')})
        return c.result
    def add_datasets(self, datasets,  id):
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
    def mod_app_api(self):
        API_KEY = base.request.params.get('apikey', '')
        if len(c.user) == 0 and len(API_KEY) != 0:
            c.user = model.Session.query(model.User).filter(model.User.apikey == API_KEY).first().name

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'auth_user_obj': c.userobj,
                   'for_view': True}
        id = base.request.params.get('id','')
        data_dict = {'id': id}
        c.result = None

        #id = base.request.params.get('id','')
        valid = model.Session.query(model.Related).filter(model.Related.id == id).first()

        if valid == None:
            c.result = json.dumps({'help': 'mod app', 'success':False, 'result': _('dataset not found')})
            return c.result

        related_datasets = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == id).all()
        logging.warning('rows to delete...\n'+str(related_datasets))

        for i in related_datasets:
            model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.id == i.id).delete(synchronize_session=False)
        model.Session.commit()
        #all related items deleted...
        data = {}

        #related = logic.clean_dict(df.unflatten(logic.tuplize_dict(logic.parse_params(base.request.params))))
        #data = {}
        title = base.request.params.get('title','')
        description = base.request.params.get('description','') 
        image_url = base.request.params.get('image_url','')
        url = base.request.params.get('url','')
        private = base.request.params.get('private','')
        datasets = base.request.params.get('datasets','')



        #logging.warning('post data values:')
        #logging.warning(data)
        #select the old value:
        old_data = model.Session.query(model.Related).filter(model.Related.id == id).first()
        logging.warning("old_data>>>>>>>>>>>>>>>>>>>>>>>")
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
        
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}

        data_dict = {'related_id':id,'key':'privacy'}

        try:
            _check_access('app_editall', context, data_dict)
            __builtin__.value = private
        except toolkit.NotAuthorized, e:
            __builtin__.value = 'private'
            c.result = json.dumps({'help': 'mod app', 'success':False, 'result': _('not authorized')})
            return c.result
        if datasets != None or datasets != '':
            mod_related_extra(context, data_dict)

        model.Session.commit()
        if datasets != "" or datasets != None:
            datasets = datasets.split(',')
            self.add_datasets(datasets, id)
        c.result = json.dumps({'help': 'mod app', 'success':True, 'result': _('done')})
        return c.result
    def valid_dataset(self, dataset_name):
        dataset =  model.Session.query(model.Package).filter(model.Package.name == dataset_name).first()
        return dataset != None

    def new_app_api(self):
        API_KEY = base.request.params.get('apikey', '')
        if len(c.user) == 0 and len(API_KEY) != 0:
            c.user = model.Session.query(model.User).filter(model.User.apikey == API_KEY).first().name
        context = {'user': c.user}
        
        request = urllib2.Request('http://192.168.21.27:5000/')
        request.add_header('Authorization', 'e8491611-60f7-46a1-8c2a-94d0cc294d6b')
        response_dict = json.loads(urllib2.urlopen(request, '{}').read())
        
        logging.warning(response_dict)

        try:
            _check_access('app_create', context)
        except toolkit.NotAuthorized, e:
            c.result = json.dumps({'help': 'mod app', 'success':False, 'result': _('not authorized')}, encoding='utf8')
            return c.result


        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}

        data_to_commit = model.related.Related()

        title = base.request.params.get('title','')
        description= base.request.params.get('description','')
        url = base.request.params.get('url','')
        image_url = base.request.params.get('image_url','')
        datasets = base.request.params.get('datasets','')

        data_to_commit.id = unicode(uuid.uuid4())
        if len(title) == 0:
            c.result = json.dumps({'help': 'new app', 'success':False, 'result': _('title is required')})
            return c.result
        datasets = datasets.split(',')
        ds = []
        for i in datasets:
            if self.valid_dataset(i):
                ds.append(i)
        if len(ds) == 0:
            c.result = json.dumps({'help': 'new app', 'success':False, 'result': _('add some datasets')})
            return c.result
        owner_id = c.userobj.id

        data_to_commit.title = title
        data_to_commit.description = description
        data_to_commit.url = url
        data_to_commit.image_url = image_url
        data_to_commit.created = datetime.datetime.now()
        data_to_commit.owner_id = owner_id
        data_to_commit.type = 'application'

        data_dict = {'related_id':data_to_commit.id,'key':'privacy'}
        model.Session.add(data_to_commit)
        self.add_datasets(ds,  data_to_commit.id)

        __builtin__.value = 'private'
        new_related_extra(context, data_dict)
        
        model.Session.commit()
        c.result = json.dumps({'help': 'new app', 'success':True, 'result': _('done')})
        return c.result
def can_view(id):
    if own(id) or check(id):
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


