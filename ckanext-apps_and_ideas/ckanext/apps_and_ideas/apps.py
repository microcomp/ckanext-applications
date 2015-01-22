import urllib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.plugins as p
from ckan.common import _, c
import ckan.plugins.toolkit as toolkit

import logging
import ckan.logic
import __builtin__
import db

abort = base.abort
_get_action = logic.get_action
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
    
    logging.warning(info[index].value)
    return info[index].value == 'public'
    
def check(id):
    context = context = {'model': model, 'session': model.Session,
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
        for i in new_list2:
            if i not in new_list:
                new_list.append(i)
        public_list = []      
        for i in new_list:
            data_dict = {'related_id':i['id'],'key':'privacy'}
            if check_priv_related_extra(context, data_dict):
                public_list.append(i)
            else:
                try:
                    logic.check_access('app_edit', context, data_dict)
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
                if c.privonly != True:
                    i['priv'] = 'public'
                    public_list.append(i)
                c.pr.append('')
            else:
                try:
                    logic.check_access('app_edit', context, {'owner_id' : i['owner_id']})
                    c.priv_private = True
                    i['priv'] = 'private'
                    public_list.append(i)
                except logic.NotAuthorized:
                    logging.warning("access denied")
                c.pr.append('private')
        
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