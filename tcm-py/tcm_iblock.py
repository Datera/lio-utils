#!/usr/bin/python

import os, tempfile
import subprocess as sub
import string, re
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"

def iblock_createvirtdev(path, params):
#	print "Calling iblock_createvirtdev: path " + path
	cfs_path = tcm_root + "/" + path + "/"
#	print "Calling iblock_createvirtdev: params " + str(params)
	path = params[0]
	if not re.search('/dev/', path):
		print "IBLOCK: Please reference a valid /dev/ block_device"
		return -1

	udev_path = path.rstrip()
	# Resolve symbolic links to get major/minor
	udev_op = "/bin/ls -laL " + udev_path
	p = sub.Popen(udev_op, shell=True, stdout=sub.PIPE).stdout
	line = p.readline() 
	out = line.split(' ');
	major = out[4]
	minor = out[5]
	p.close()

	if major == "11,":
		print "Unable to export Linux/SCSI TYPE_CDROM from IBLOCK, please use pSCSI export"
		return -1
	if major == "22,":
		print "Unable to export IDE CDROM from IBLOCK"
		return -1

	set_udev_path_op = "echo -n " + udev_path + " > " + cfs_path + "udev_path"
	ret = os.system(set_udev_path_op)
	if ret:
		print "IBLOCK: Unable to set udev_path in " + cfs_path + " for: " + udev_path
		return -1

	# Failure here will be handled in tcm_createvirtdev() by checking
	# /sys/kernel/config/target/core/$HBA/$DEV/info.  A failure case here will return
	# -ENODEV
	exec_op = "exec 3<>" + udev_path + "; echo 3 > " + cfs_path + "fd" + "; exec 3>&-"
	ret = os.system(exec_op)
	if ret:
		print "IBLOCK: Unable to access file descriptor for udev_path access: " + udev_path
		return -1

	return

def iblock_freevirtdev():
	return

def iblock_get_params(path):
	# Reference by udev_path if available	
	udev_path_file = path + "/udev_path"
	p = os.open(udev_path_file, 0)
	value = os.read(p, 1024)
	if re.search('/dev/', value):
		os.close(p)
		return value.rstrip()

	os.close(p)

	info_file = path + "/info"
	p = open(info_file, 'rU')
	try:
		value = p.read(1024)
	except IOError, msg:	
		p.close()
		return
	p.close()

	of = value.index('Major: ')
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
