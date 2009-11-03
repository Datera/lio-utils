#!/bin/sh

SITE_PACKAGES=`python ../get-py-modules-path.py`

if [ -f /usr/sbin/tcm_node ]; then
	rm /usr/sbin/tcm_node
fi
if [ -f /usr/sbin/tcm_dump ]; then
	rm /usr/sbin/tcm_dump
fi

rm -rf $SITE_PACKAGES/tcm_*
