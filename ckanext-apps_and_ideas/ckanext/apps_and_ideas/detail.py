import urllib

import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.common import _, c
import logging

abort = base.abort
_get_action = logic.get_action
#log = logging.getLogger('ckanext_apps_and_ideas')

class DetailController(base.BaseController):  

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
        c.title = new_list[0]['title']
        c.description = new_list[0]['description']
        c.url = new_list[0]['url']
        c.created = ('.').join(new_list[0]['created'].split('T')[0].split('-'))
        owner_id = new_list[0]['owner_id']
        c.img = new_list[0]['image_url']

        c.owner = model.Session.query(model.User).filter(model.User.id == owner_id).first().name
        ds_id = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == c.id).first().dataset_id
        logging.warning(ds_id)
        pack = model.Session.query(model.Package).filter(model.Package.id == ds_id).first()
        c.datasets = pack.name
        c.data = [c.datasets]
        c.datasets = c.data
        private =  pack.private
        if private == 'f':
            c.private = 'Private'
        else:
            c.private = 'Public'

        logging.warning(c.datasets)
        logging.warning(c.private)
        return base.render("related/dashboard.html")
        
    def new_app(self):
        return base.render("related/dashboard.html")

    def  new_app_in(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {}
        data = logic.clean_dict(df.unflatten(logic.tuplize_dict(logic.parse_params(base.request.params))))
        logging.warning('post data values:')
        logging.warning(data)
        '''
        insert into related... dataset
        
        app_id select from related

        for bla bla 
            array.append ... select from package ID (name == name)

        for bla bla array
            insert related dataset app_id array id
        '''
        return toolkit.redirect_to(controller='ckanext.apps_and_ideas.apps:AppsController', action='dashboard')

    
 