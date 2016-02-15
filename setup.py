from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-applications',
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
    namespace_packages=['ckanext', 'ckanext.applications'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points={
        'babel.extractors': [
                    'ckan = ckan.lib.extract:extract_ckan',
                    ],
        'ckan.plugins' : [
                    'applications=ckanext.applications.plugin:Applications',
                    ]
        }
)
