#!/bin/sh

SITE_PACKAGES=`python ../get-py-modules-path.py`

if [ -f /usr/sbin/tcm_node ]; then
	rm /usr/sbin/tcm_node
fi
if [ -f /usr/sbin/tcm_dump ]; then
	rm /usr/sbin/tcm_dump
fi

if [ -f /usr/sbin/tcm_loop ]; then
        rm /usr/sbin/tcm_loop
fi

if [ -f /usr/sbin/tcm_snap ]; then
        rm /usr/sbin/tcm_snap
fi

if [ -f /usr/sbin/tcm_fabric ]; then
        rm /usr/sbin/tcm_fabric
fi

rm -rf $SITE_PACKAGES/tcm_*
