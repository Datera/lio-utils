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

	# Exract HCTL from sysfs and set udev_path
	if re.search('/dev/', pscsi_params):
		udev_path = pscsi_params.rstrip()
		if re.search('/dev/disk/', udev_path):
			udev_op = "/bin/ls -l " + udev_path		
			p = sub.Popen(udev_op, shell=True, stdout=sub.PIPE).stdout
			if not p:
				print "pSCSI: Unable to locate scsi_device from udev_path: " + udev_path
				return -1

			line = p.readline()
			out = line.split(' ../../');
			p.close()
			if not out:
				print "pSCSI: Unable to locate scsi_device from udev_path: " + udev_path
				return -1
	
			scsi_dev = out[1].rstrip()
		elif re.search('/dev/s', udev_path):
			out = udev_path.split('/dev/')
			scsi_dev = out[1]
		else:
			print "pSCSI: Unable to locate scsi_device from udev_path: " + udev_path
			return -1

		# Convert scdX to sr0 for TYPE_ROM in /sys/block/
		if re.search('scd', scsi_dev):
			scsi_dev = scsi_dev.replace('scd', 'sr');

		if not os.path.isdir("/sys/block/" + scsi_dev + "/device/"):
			print "pSCSI: Unable to locate scsi_device from udev_path: " + udev_path
			return -1

		scsi_dev_sysfs = "/sys/block/" + scsi_dev + "/device"
		udev_op = "/bin/ls -l " + scsi_dev_sysfs 
		p = sub.Popen(udev_op, shell=True, stdout=sub.PIPE).stdout
		if not p:
			print "pSCSI: Unable to locate scsi_device from udev_path: " + udev_path
			return -1			

		line = p.readline()
		out = line.split('/')
		p.close()

		scsi_hctl_tmp = out[len(out)-1]	
		scsi_hctl = scsi_hctl_tmp.split(':')
		scsi_host_id = scsi_hctl[0]
		scsi_channel_id = scsi_hctl[1]
		scsi_target_id = scsi_hctl[2]
		scsi_lun_id = scsi_hctl[3]
		print "pSCSI: Referencing HCTL " + out[1].rstrip() + " for udev_path: " + udev_path

		set_udev_path_op = "echo -n " + udev_path + " > " + cfs_path + "udev_path"
		ret = os.system(set_udev_path_op)
		if ret:
			print "pSCSI: Unable to set udev_path in " + cfs_path + " for: " + udev_path
			return -1

		pscsi_params = "scsi_host_id=" + scsi_host_id + ",scsi_channel_id=" + scsi_channel_id + ",scsi_target_id=" + scsi_target_id + ",scsi_lun_id=" + scsi_lun_id.rstrip()

		
	control_opt = "echo -n " + pscsi_params + " > " + cfs_path + "control"
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
	params = ""
	
	try:
		off = value.index('Host ID: ')
	except ValueError:
		params = ""
	else:
		off += 9
		host_id_tmp = value[off:]
		host_id = host_id_tmp.split(' ')
		host_id = host_id[0].rstrip()
		if host_id != "PHBA":
			params += "scsi_host_id=" + host_id[0] + ","

	params += "scsi_channel_id=" + channel_id[0] + ",scsi_target_id=" + target_id[0] + ",scsi_lun_id=" + lun_id[0].rstrip()

	# scsi_channel_id=, scsi_target_id= and scsi_lun_id= reference for tcm_node --createdev
	return params
	
#parser = OptionParser()
#parser.add_option("-s", "--scan", action="callback", callback=pscsi_scan_lsscsi,
#		default=False, help="Scan and register pSCSI HBAs with TCM/ConfigFS")
#parser.parse_args()
#
