### setup.py ###
from distutils.core import setup

setup (name='Target_Core_Mod/ConfigFS v3.0 CLI',
      version='1.0',
      description='CLI for controlling target_core_mod/ConfigFS',
      author='Nicholas A. Bellinger',
      author_email='nab@linux-iscsi.org',
      url='http://linux-iscsi.org',
      license='GPL',
      py_modules=['tcm_dump', 'tcm_fileio','tcm_iblock','tcm_node','tcm_pscsi','tcm_ramdisk','tcm_snap']
)

