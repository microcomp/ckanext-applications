import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import json
import os

import apps
import db 
import ckan.logic
import ckan.model as model
from ckan.common import _, c
import logging



class AppsAndIdeasPlugin(plugins.SingletonPlugin):
    controller = 'ckanext.apps_and_ideas.related:RelatedController'
    '''An example theme plugin.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    def before_map(self, map):
        map.connect('apps','/apps', action='dashboard', controller='ckanext.apps_and_ideas.apps:AppsController')
        map.connect('apps_search','/apps/search', action='search', controller='ckanext.apps_and_ideas.apps:AppsController')
        map.connect('app_page','/apps/detail', action='detail', controller='ckanext.apps_and_ideas.detail:DetailController')
        map.connect('new_app','/apps/new', action='new_app', controller='ckanext.apps_and_ideas.detail:DetailController')
        map.connect('new_app_in', '/apps/new/in', action='new_app_in', controller='ckanext.apps_and_ideas.detail:DetailController')
        map.connect('edit_app', '/apps/update', action='edit_app', controller='ckanext.apps_and_ideas.detail:DetailController')
        map.connect('edit_app', '/apps/update/in', action='edit_app_do', controller='ckanext.apps_and_ideas.detail:DetailController')
        map.connect('delete_app', '/apps/delete', action='delete_app', controller='ckanext.apps_and_ideas.detail:DetailController')
        map.connect('list_apps', '/dataset/{id}/related', action='list', controller='ckanext.apps_and_ideas.detail:DetailController')
        map.connect('dashboard', '/related', action='dashboard', controller='ckanext.apps_and_ideas.apps:AppsController')
        return map

    def get_helpers(self):
        return {'check_2': apps.check, 
                'own': apps.own}

