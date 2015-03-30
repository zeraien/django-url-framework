"""
Based entirely on Django's own ``setup.py``.
"""
import os
from setuptools import setup

# Dynamically calculate the version based on django_url_framework.VERSION
version = __import__('django_url_framework').__version__

setup(
    name='django-url-framework',
    version=version,
    license="MIT",
    description='Automagically discover urls in a django application, similar to the Ruby on Rails Controller/Action/View implementation.',
    author='Dmitri Fedortchenko',
    author_email='d@angelhill.net',
    url='https://github.com/zeraien/django-url-framework/',
    packages=['django_url_framework'],
    install_requires=['django'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
)
