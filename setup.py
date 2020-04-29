import os
from setuptools import setup, find_packages

# Dynamically calculate the version based on django_url_framework.VERSION
version = __import__('django_url_framework').__version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='django-url-framework',
    version=version,
    license="MIT",
    description='Automagically discover urls in a django application, similar to the Ruby on Rails Controller/Action/View implementation.',
    long_description=long_description,    
    long_description_content_type="text/markdown",
    author='Dimo Fedortchenko',
    author_email='d@angelhill.net',
    url='https://github.com/zeraien/django-url-framework/',
    packages=[p for p in find_packages() if p!="tests"],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 3',
                   'Topic :: Utilities'],
)
