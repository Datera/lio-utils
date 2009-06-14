#!/usr/bin/python

import os
import subprocess as sub
import string
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"

def iblock_createvirtdev(path, params):
	
#	print "Calling iblock_createvirtdev: path " + path
	cfs_path = tcm_root + "/" + path + "/"
#	print "Calling iblock_createvirtdev: params " + str(params)
	sysfs_dev = params[0]
	open_op = "cat " + sysfs_dev
	block_dev = sub.Popen(open_op, shell=True, stdout=sub.PIPE).stdout
	line = block_dev.readline()
	if not line:
		print "Unable to open SysFS device information"		
		return -1

	new_line = line.split(':')
	major = new_line[0]
	minor = new_line[1]

	iblock_params = "major=" + major + ",minor=" + minor
#	print "iblock_params: " + iblock_params

	control_opt = "echo " + iblock_params.rstrip() + " > " + cfs_path + "/control"
#	print "control_opt: " + control_opt
	ret = os.system(control_opt)
	if ret:
		print "IBLOCK: createvirtdev failed for control_opt with " + iblock_params
		return -1

	enable_opt = "echo 1 > " +  cfs_path + "enable"	
#	print "Calling enable_opt " + enable_opt
	ret = os.system(enable_opt)
	if ret:
		print "IBLOCK: createvirtdev failed for enable_opt with " + iblock_params
		return -1

	return

def iblock_freevirtdev():
	return

def iblock_get_params(path):

	info_file = path + "/info"
	p = os.open(info_file, 0)
	value = os.read(p, 1024)
	off = value.index('Major: ')
	off += 7
	major_tmp = value[off:]
	major = major_tmp.split(' ')
	off = value.index('Minor: ')
	off += 7
	minor_tmp = value[off:]
	minor = minor_tmp.split(' ')
	params = "major=" + major[0] + ",minor=" + minor[0]
	os.close(p)

	return params

