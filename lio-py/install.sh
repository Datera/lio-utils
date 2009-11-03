#!/bin/sh

SITE_PACKAGES=`python ../get-py-modules-path.py`

chmod a+x $SITE_PACKAGES/lio_dump.py
chmod a+x $SITE_PACKAGES/lio_node.py

if [ ! -f /usr/sbin/lio_dump ]; then
	ln -s $SITE_PACKAGES/lio_dump.py /usr/sbin/lio_dump
fi
if [ ! -f /usr/sbin/lio_node ]; then
	ln -s $SITE_PACKAGES/lio_node.py /usr/sbin/lio_node
fi
