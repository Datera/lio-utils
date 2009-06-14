### setup.py ###
from distutils.core import setup

setup (name='LIO-Target/ConfigFS v3.0 CLI',
      version='1.0',
      description='CLI for controlling LIO-Target/ConfigFS',
      author='Nicholas A. Bellinger',
      author_email='nab@linux-iscsi.org',
      url='http://linux-iscsi.org',
      license='GPL',
      py_modules=['lio_dump','lio_node']
)

