#!/usr/bin/env python
from os import path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

README = path.abspath(path.join(path.dirname(__file__), 'README.md'))
PIP_REQUIRED = path.abspath(path.join(path.dirname(__file__),
                            'pip-requires.txt'))

desc = 'A Python console to connect to my arduino alarm'

setup(
    name='alarm_console',
    version='0.0.1',
    author='Zaurky',
    author_email='zaurky@zeb.re',
    description=desc,
    long_description=open(README).read(),
    license='GPLV2',
    url='http://github.com/zaurky/alarm_console',
    packages=['alarm'],
    scripts=['bin/console.py'],
    install_requires=[line.strip() for line in open(PIP_REQUIRED).readlines()],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
