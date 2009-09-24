#!/usr/bin/python

from distutils.core import setup

long_desc="""Python CLI for controlling the LIO-Target/ConfigFS fabric module
"""

setup(name='lio',
      version='3.2',
      description='CLI for controlling LIO-Target/ConfigFS',
      long_description=long_desc,
      author='Nicholas A. Bellinger',
      author_email='nab@linux-iscsi.org',
      url='http://linux-iscsi.org',
      license='GPL',
      requires=['tcm'],
      py_modules=['lio_dump','lio_node']
)

