import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import json
import os

import detail
import related_extra
import apps
import db 
import topic_functions
import ckan.logic
import ckan.model as model
from ckan.common import _, c
import logging

class Applications(plugins.SingletonPlugin):
    controller = 'ckanext.applications.related:RelatedController'
    '''An example theme plugin.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.interfaces.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    def before_map(self, map):
        map.connect('apps','/apps', action='dashboard', controller='ckanext.applications.apps:AppsController')
        map.connect('apps_search','/apps/search', action='search', controller='ckanext.applications.apps:AppsController')
        map.connect('app_page','/apps/detail', action='detail', controller='ckanext.applications.detail:DetailController')
        map.connect('new_app','/apps/new', action='new_app', controller='ckanext.applications.detail:DetailController')
        map.connect('new_app_in', '/apps/new/in', action='new_app_in', controller='ckanext.applications.detail:DetailController')
        map.connect('edit_app', '/apps/update', action='edit_app', controller='ckanext.applications.detail:DetailController')
        map.connect('edit_app', '/apps/update/in', action='edit_app_do', controller='ckanext.applications.detail:DetailController')
        map.connect('delete_app', '/apps/delete', action='delete_app', controller='ckanext.applications.detail:DetailController')
        map.connect('list_apps', '/dataset/{id}/related', action='list', controller='ckanext.applications.detail:DetailController')
        map.connect('dashboard', '/related', action='dashboard', controller='ckanext.applications.apps:AppsController')

        map.connect('apps_report', '/apps/report', action='report_app', controller='ckanext.applications.apps:AppsController')
        map.connect('delete_report', '/report/delete', action='delete_app_report', controller='ckanext.applications.apps:AppsController')
        map.connect('delete_reports', '/report/delete/all', action='delete_all_reports', controller='ckanext.applications.apps:AppsController')
        map.connect('report_admin', '/admin/reports', action='list_reports', controller='ckanext.applications.apps:AppsController')
        return map
    def get_actions(self):
    # Registers the custom API method defined above
        return {'delete_app':apps.delete_app,
                'list_apps': apps.list_apps,
                'mod_app': apps.mod_app_api,
                'new_app': apps.new_app_api,
                'statistics':apps.ckan_stats}
    def get_helpers(self):
        return {'own': apps.own,
                'is_priv': related_extra.is_private,
                'extra_v': detail.errors_and_other_stuff,
                'del_x':detail.del_xtra,
                'can_v': apps.can_view,
                'is_admin': apps.is_admin,
                'list_reports': related_extra.list_reports,
                'app_name': apps.app_name,
                'reports_num': related_extra.reports_num,
                'reported_by_user': related_extra.reported_by_user,
                'reported_by': related_extra.reported_by,
                'report_text': related_extra.report_text,
                'all_topics': topic_functions.all_topics}
