import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import json
import os

import db 
import ckan.logic
import ckan.model as model
from ckan.common import _, c


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

	return info[index].value == 'public'
    
def check(id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
    data_dict = {'related_id':id,'key':'privacy'}
    check = check_priv_related_extra(context, data_dict)
    if check == False:
    	try:
            logic.check_access('app_edit', context, data_dict)
            return True
        except logic.NotAuthorized:
            logging.warning("access denied")
    return check

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
    
    if db.related_extra_table is None:
        db.init_db(context['model'])
    res = db.RelatedExtra.get(**data_dict)
    return res


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
        return {'check_2': check}

