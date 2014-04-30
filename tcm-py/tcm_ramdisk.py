#!/usr/bin/python

import os
import subprocess as sub
import string, re
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"

def createvirtdev(path, params):
	
#	print "Calling ramdisk createvirtdev: path " + path
	cfs_path = tcm_root + "/" + path + "/"
#	print "Calling ramdisk createvirtdev: params " + str(params)
	rd_pages = params[0]

	rd_params = "rd_pages=" + rd_pages
#	print "rd_params: " + rd_params

	control_opt = "echo -n " + rd_params.rstrip() + " > " + cfs_path + "/control"
#	print "control_opt: " + control_opt
	ret = os.system(control_opt)
	if ret:
		print "RAMDISK: createvirtdev failed for control_opt with " + rd_params
		return -1

	enable_opt = "echo 1 > " +  cfs_path + "enable"	
#	print "Calling enable_opt " + enable_opt
	ret = os.system(enable_opt)
	if ret:
		print "RAMDISK: createvirtdev failed for enable_opt with " + rd_params
		return -1

def rd_freevirtdev():
	pass

def rd_get_params(path):

	info_file = path + "/info"
	p = open(info_file, 'rU')
	try:
		value = p.read(1024)
	except IOError, msg:
		p.close()
		return
	p.close()

	off = value.index('PAGE_SIZE: ')
	off += 11 # Skip over "PAGE_SIZE: "
	rd_pages_tmp = value[off:]
	rd_pages = rd_pages_tmp.split('*')
	params = rd_pages[0]

	try:
		off = value.index('nullio: ')
		off += 8 # Skip over "nullio: "
		rd_nullio = value[off]
		params += ",rd_nullio=" + rd_nullio
	except ValueError:
		pass

	return params
