#!/usr/bin/python

from distutils.sysconfig import get_python_lib,re;

str = get_python_lib()

# Fix up get_python_lib() path for Python v2.6 on Ubuntu 9.10 and SLES 11
if re.search('python2.6', str):
	print str.replace('/usr','/usr/local')
else:
	print str;
