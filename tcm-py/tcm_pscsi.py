#!/usr/bin/python

import os
import subprocess as sub
import string, re
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"

def print_lsscsi(option, opt_str, value, parser):
        command = "lsscsi"

	p = sub.Popen(command,shell=True, stdout=sub.PIPE).stdout
	while 1:
		line = p.readline()
		if not line: break
		print line,
	return

def pscsi_get_hba_prefix(arg):
	path = "/sys/kernel/config/target/core/pscsi_" + arg
	return path	

def pscsi_scan_lsscsi(option, opt_str, value, parser):
	command = "lsscsi -H"
	p = sub.Popen(command,shell=True, stdout=sub.PIPE).stdout
	while 1:
		line = p.readline()
		if not line: break
		line.split()
		host_id = line[1]
		print "SCSI Host ID: " + host_id
		
		cfs_path = pscsi_get_hba_prefix(host_id)
		if (os.path.isdir(cfs_path)):
			print "pSCSI HBA already registered, skipping"
			continue

		print cfs_path
		ret = os.mkdir(cfs_path)
		print "os.path.mkdir ret: " + str(ret)
		if not ret:
			print "Successfully added ConfigFS path " + cfs_path
	return

def pscsi_createvirtdev(path, params):
	
#	print "Calling pscsi_createvirtdev: path " + path
	cfs_path = tcm_root + "/" + path + "/"

#	print "Calling pscsi_createvirtdev: params " + str(params)
	pscsi_params = params[0]
#	print pscsi_params

	control_opt = "echo " + pscsi_params + " > " + cfs_path + "control"
#	print "Calling control_opt " + control_opt
	ret = os.system(control_opt)
	if ret:
		print "pSCSI: createvirtdev failed for control_opt with " + pscsi_params
		return -1

	enable_opt = "echo 1 > " +  cfs_path + "enable"	
#	print "Calling enable_opt " + enable_opt
	ret = os.system(enable_opt)
	if ret:
		print "pSCSI: createvirtdev failed for enable_opt with " + pscsi_params
		return -1

	return

def pscsi_freevirtdev():
	return

def pscsi_get_params(path):
	
	info_file = path + "/info"
	p = os.open(info_file, 0)
	value = os.read(p, 1024)
	off = value.index('Channel ID: ')
	off += 12	
	channel_id_tmp = value[off:]
	channel_id = channel_id_tmp.split(' ')
	off = value.index('Target ID: ')
	off += 11
	target_id_tmp = value[off:]
	target_id = target_id_tmp.split(' ')
	off = value.index('LUN: ')	
	off += 5
	lun_id_tmp = value[off:]
	lun_id = lun_id_tmp.split(' ')
	params = "scsi_channel_id=" + channel_id[0] + ",scsi_target_id=" + target_id[0] + ",scsi_lun_id=" + lun_id[0].rstrip()
	os.close(p)

	# Direct configfs reference usage
#	print "mkdir -p " + path
#	print "echo " + params + " > " + path + "/control"
#	print "echo 1 > " + path + "/enable"
#	return 0

	# scsi_channel_id=, scsi_target_id= and scsi_lun_id= reference for tcm_node --createdev
	return params
	
#parser = OptionParser()
#parser.add_option("-s", "--scan", action="callback", callback=pscsi_scan_lsscsi,
#		default=False, help="Scan and register pSCSI HBAs with TCM/ConfigFS")
#parser.parse_args()
#
