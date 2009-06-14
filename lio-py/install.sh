#!/bin/sh

SITE_PACKAGES=`python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`

chmod a+x $SITE_PACKAGES/lio_dump.py
chmod a+x $SITE_PACKAGES/lio_node.py

if [ ! -f /usr/sbin/lio_dump ]; then
	ln -s $SITE_PACKAGES/lio_dump.py /usr/sbin/lio_dump
fi
if [ ! -f /usr/sbin/lio_node ]; then
	ln -s $SITE_PACKAGES/lio_node.py /usr/sbin/lio_node
fi
