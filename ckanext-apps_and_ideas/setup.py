from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-apps_and_ideas',
    version=version,
    description="apps and ideas extension",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='JanosFarkas',
    author_email='farkas48@uniba.sk',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.apps_and_ideas'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        # Add plugins here, e.g.
        apps_and_ideas=ckanext.apps_and_ideas.plugin:AppsAndIdeasPlugin
	
    ''',
)
