#!/usr/bin/python
from distutils.core import setup

long_desc="""Python CLI for controlling the generic target_core_mod/ConfigFS engine
"""

setup (name='tcm',
      version='3.2',
      description='CLI for controlling target_core_mod/ConfigFS',
      long_description=long_desc,
      author='Nicholas A. Bellinger',
      author_email='nab@linux-iscsi.org',
      url='http://linux-iscsi.org',
      license='GPL',
      py_modules=['tcm_dump', 'tcm_fileio','tcm_iblock','tcm_node','tcm_pscsi','tcm_ramdisk','tcm_snap']
)

