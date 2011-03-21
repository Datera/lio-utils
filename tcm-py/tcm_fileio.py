#!/usr/bin/python

import os
import subprocess as sub
import string, re 
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"

def createvirtdev(path, params):
	
#	print "Calling fileio createvirtdev: path " + path
	cfs_path = tcm_root + "/" + path + "/"
#	print "Calling fileio createvirtdev: params " + str(params)
	fd_params = str(params)

        # Extract the udev_dev path from fd_dev_name=
	try:
		off = fd_params.index('fd_dev_name=')
		off += 12
		file_tmp = fd_params[off:]
		file = file_tmp.split(',')
	except IOError, msg:
		print "Unable to locate fd_dev_name= parameter key"
		return -1

	# Set UDEV path if struct file is pointing to an underlying struct block_device
        if re.search('/dev/', file[0]):
		udev_path = file[0]
		set_udev_path_op = "echo -n " + udev_path + " > " + cfs_path + "udev_path"
		ret = os.system(set_udev_path_op)
		if ret:
			print "pSCSI: Unable to set udev_path in " + cfs_path + " for: " + udev_path
			return -1

	control_opt = "echo -n " + params[0] + " > " + cfs_path + "control"
#	print "control_opt: " + control_opt
	ret = os.system(control_opt)
	if ret:
		print "FILEIO: createvirtdev failed for control_opt with " + params[0]
		return -1

	enable_opt = "echo 1 > " +  cfs_path + "enable"	
#	print "Calling enable_opt " + enable_opt
	ret = os.system(enable_opt)
	if ret:
		print "FILEIO: createvirtdev failed for enable_opt with " + params[0]
		return -1

def fd_freevirtdev():
	pass

def fd_get_params(path):
        # Reference by udev_path if available   
	udev_path_file = path + "/udev_path"
	p = os.open(udev_path_file, 0)
	value = os.read(p, 1024)
	if re.search('/dev/', value):
		os.close(p)
		# Append a FILEIO size of ' 0', as struct block_device sector count is autodetected by TCM
		return "fd_dev_name=" + value.rstrip() + ",fd_dev_size=0"

	os.close(p)

	info_file = path + "/info"
	p = open(info_file, 'rU')
	try:
		value = p.read(1024)
	except IOError, msg:
		p.close()
		return
	p.close()

	off = value.index('File: ')
	off += 6
	fd_dev_name_tmp = value[off:]
	fd_dev_name = fd_dev_name_tmp.split(' ')
	off = value.index(' Size: ')
	off += 7
	fd_dev_size_tmp = value[off:]
	fd_dev_size = fd_dev_size_tmp.split(' ')
	params = "fd_dev_name=" + fd_dev_name[0] + ",fd_dev_size=" + fd_dev_size[0]

	# fd_dev_name= and fd_dev_size= parameters for tcm_node --createdev
	return params
