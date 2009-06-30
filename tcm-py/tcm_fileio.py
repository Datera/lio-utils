#!/usr/bin/python

import os
import subprocess as sub
import string, re 
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"

def fd_createvirtdev(path, params):
	
#	print "Calling fd_createvirtdev: path " + path
	cfs_path = tcm_root + "/" + path + "/"
#	print "Calling fd_createvirtdev: params " + str(params)
	fd_params = params[0]

	control_opt = "echo " + fd_params + " > " + cfs_path + "control"
	print "control_opt: " + control_opt
	ret = os.system(control_opt)
	if ret:
		print "FILEIO: createvirtdev failed for control_opt with " + fd_params
		return -1

	enable_opt = "echo 1 > " +  cfs_path + "enable"	
	print "Calling enable_opt " + enable_opt
	ret = os.system(enable_opt)
	if ret:
		print "FILEIO: createvirtdev failed for enable_opt with " + fd_params
		return -1

	return

def fd_freevirtdev():
	return

def fd_get_params(path):

	info_file = path + "/info"
	p = os.open(info_file, 0)
	value = os.read(p, 1024)
	off = value.index('File: ')
	off += 6
	fd_dev_name_tmp = value[off:]
	fd_dev_name = fd_dev_name_tmp.split(' ')
	off = value.index(' Size: ')
	off += 7
	fd_dev_size_tmp = value[off:]
	fd_dev_size = fd_dev_size_tmp.split(' ')
	params = "fd_dev_name=" + fd_dev_name[0] + ",fd_dev_size=" + fd_dev_size[0]
	os.close(p)

	# Direct configfs reference usage
#	print "mkdir -p " + path
#	print "echo " + params + " > " + path + "/control"
#	print "echo 1 > " + path + "/enable"
#	return 0

	# fd_dev_name= and fd_dev_size= parameters for tcm_node --createdev
	return params
