import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit



class AppsAndIdeasPlugin(plugins.SingletonPlugin):
    controller = 'ckanext.apps_and_ideas.related:RelatedController'
    '''An example theme plugin.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
	toolkit.add_template_directory(config, 'templates')
	toolkit.add_public_directory(config, 'public')

    def before_map(self, map):
	map.connect('apps','/apps', action='dashboard', controller='ckanext.apps_and_ideas.apps:AppsController')
	map.connect('apps_search','/apps/search', action='search', controller='ckanext.apps_and_ideas.apps:AppsController')
	map.connect('app_page','/apps/detail', action='detail', controller='ckanext.apps_and_ideas.detail:DetailController')
	map.connect('new_app','/apps/new', action='new_app', controller='ckanext.apps_and_ideas.detail:DetailController')

	return map
	 
