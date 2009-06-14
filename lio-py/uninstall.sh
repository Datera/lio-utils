#!/bin/sh

SITE_PACKAGES=`python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`

if [ -f /usr/sbin/lio_dump ]; then
	rm /usr/sbin/lio_dump
fi
if [ -f /usr/sbin/lio_node ]; then
	rm /usr/sbin/lio_node
fi

rm -rf $SITE_PACKAGES/lio_*
