#!/bin/sh

SITE_PACKAGES=`python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`

rm /usr/sbin/lio_dump
rm /usr/sbin/lio_node
rm /usr/sbin/tcm_node
rm /usr/sbin/tcm_dump

rm -rf $SITE_PACKAGES/lio_*
rm -rf $SITE_PACKAGES/tcm_*
