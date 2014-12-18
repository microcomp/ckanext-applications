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

import json
import os

import ckan.logic

data_path = "/data/"

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
        self.owner_id = new_list[0]['owner_id']
        owner_id = self.owner_id
        c.img = new_list[0]['image_url']

        c.owner = model.Session.query(model.User).filter(model.User.id == owner_id).first().name
        ds_ids = model.Session.query(model.RelatedDataset).filter(model.RelatedDataset.related_id == c.id).all()
        ds_id = []
        for i in ds_ids:
            ds_id.append(i.dataset_id)
        logging.warning(ds_id)
        c.datasets = []

        for i in ds_id:
            pack = model.Session.query(model.Package).filter(model.Package.id == i).first()
            c.datasets.append(pack.name)
        #c.datasets = c.data
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
        data = {}

        related = logic.clean_dict(df.unflatten(logic.tuplize_dict(logic.parse_params(base.request.params))))
        data = related
        logging.warning('post data values:')
        logging.warning(data)
        owner_id = c.userobj.id

        '''
            {'datasets': u'aaaasdasd', 'description': u'', 'title': u'', 'url': u'', 'image_url': u'', 'save': u''}
        '''
        
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
        
        #related = logic.get_action(action_name)(context, data)
        
        model.Session.add(data_to_commit)
            
        related_ids = []
        datasets = data['datasets'].split(',')
        for i in datasets:
            related_ids.append(model.Session.query(model.Package).filter(model.Package.name == i).first().id)
        logging.warning(related_ids)
        related_datasets = []
        for i in range(len(related_ids)):
            buffer = model.related.RelatedDataset()
            related_datasets.append(buffer)
        for i in range(len(related_ids)):
            related_datasets[i].dataset_id = related_ids[i]
            related_datasets[i].id = unicode(uuid.uuid4())
            related_datasets[i].related_id = data_to_commit.id
            related_datasets[i].status = 'active'
            model.Session.add(related_datasets[i])
        model.Session.commit()
        return toolkit.redirect_to(controller='ckanext.apps_and_ideas.apps:AppsController', action='dashboard')



