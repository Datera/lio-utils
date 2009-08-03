#!/bin/sh

SITE_PACKAGES=`python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`

chmod a+x $SITE_PACKAGES/tcm_node.py
chmod a+x $SITE_PACKAGES/tcm_dump.py
chmod a+x $SITE_PACKAGES/tcm_snap.py

if [ ! -f /usr/sbin/tcm_node ]; then
        ln -s $SITE_PACKAGES/tcm_node.py /usr/sbin/tcm_node 
fi
if [ ! -f /usr/sbin/tcm_dump ]; then
        ln -s $SITE_PACKAGES/tcm_dump.py /usr/sbin/tcm_dump
fi
if [ ! -f /usr/sbin/tcm_snap ]; then
	ln -s $SITE_PACKAGES/tcm_snap.py /usr/sbin/tcm_snap
fi
