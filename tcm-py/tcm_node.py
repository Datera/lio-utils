#!/usr/bin/python
import os
import subprocess as sub
import string
import re
from optparse import OptionParser

import tcm_pscsi
import tcm_iblock
import tcm_ramdisk
import tcm_fileio

tcm_root = "/sys/kernel/config/target/core"

def tcm_cat(fname):
    return file(fname).xreadlines()

def tcm_get_cfs_prefix(arg):
	path = "/sys/kernel/config/target/core/" + arg
	return path

def tcm_delhba(option, opt_str, value, parser):
	hba_name = str(value)

	hba_path = tcm_root + "/" + hba_name
	print "hba_path: " + hba_path

	dev_root = tcm_root + "/" + hba_name + "/"
	for g in os.listdir(dev_root):
		if g == "hba_info":
			continue;

		tmp_str = hba_name + "/"+ g
		tcm_freevirtdev(None, None, tmp_str, None)

	ret = os.rmdir(hba_path)
	if ret:
		print "Unable to delete TCM HBA: " + hba_path
		return -1
	else:
		print "Successfully released TCM HBA: " + hba_path

	return

def tcm_createvirtdev(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_path_tmp = cfs_unsplit.split('/')

	hba_cfs = cfs_path_tmp[0]
	print " ConfigFS HBA: " + hba_cfs
	cfs_hba_path = tcm_get_cfs_prefix(hba_cfs)
	if (os.path.isdir(cfs_hba_path) == False):
		ret = os.mkdir(cfs_hba_path)
		if not ret:
			print "Successfully added TCM/ConfigFS HBA: " + hba_cfs
		else:
			print "Unable to create TCM/ConfigFS HBA: " + cfs_hba_path
			return -1

	dev_vfs_alias = cfs_path_tmp[1]
	print " ConfigFS Device Alias: " + dev_vfs_alias
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path)):
		print "TCM/ConfigFS storage object already exists: " + cfs_dev_path
		return -1

	cfs_path = cfs_path_tmp[0] + "/" + cfs_path_tmp[1]

	tmp_params = str(value[1])
	dev_params = tmp_params.split(' ')
	plugin_params = dev_params
	print "Device Params " + str(plugin_params)
	
	ret = os.mkdir(cfs_dev_path)
	if ret:
		print "Failed to create ConfigFS Storage Object: " + cfs_dev_path + " ret: " + ret

#	Calls into submodules depending on target_core_mod subsystem plugin
	ret = 0
	result = re.search('pscsi_', hba_cfs)
	if result:
		ret = tcm_pscsi.pscsi_createvirtdev(cfs_path, plugin_params)
	result = re.search('stgt_', hba_cfs)
	if result:
		print "stgt"
	result = re.search('iblock_', hba_cfs)
	if result:
		ret = tcm_iblock.iblock_createvirtdev(cfs_path, plugin_params)
	result = re.search('rd_dr_', hba_cfs)
	if result:
		ret = tcm_ramdisk.rd_createvirtdev(cfs_path, plugin_params)
	result = re.search('rd_mcp_', hba_cfs)
	if result:
		ret = tcm_ramdisk.rd_createvirtdev(cfs_path, plugin_params)
	result = re.search('fileio_', hba_cfs)
	if result:
		ret = tcm_fileio.fd_createvirtdev(cfs_path, plugin_params)

	if not ret:
		info_op = "cat " + cfs_dev_path + "/info"
		ret = os.system(info_op)
		if ret:
			"Unable to access " + cfs_dev_path + "/info for TCM storage object"
			os.rmdir(cfs_dev_path);
			return -1

		print "Successfully created TCM/ConfigFS storage object: " + cfs_dev_path
	else:
		os.rmdir(cfs_dev_path);

	return ret

def tcm_freevirtdev(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_path = cfs_unsplit.split('/')
	hba_cfs = cfs_path[0]
	dev_vfs_alias = cfs_path[1]
	print " ConfigFS HBA: " + hba_cfs
	print " ConfigFS Device Alias: " + dev_vfs_alias

	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		print "TCM/ConfigFS storage object does not exist: " + cfs_dev_path
		return -1

	ret = os.rmdir(cfs_dev_path)
	if not ret:
		print "Successfully released TCM/ConfigFS storage object: " + cfs_dev_path
	else:
		print "Failed to release ConfigFS Storage Object: " + cfs_dev_path + " ret: " + ret

	return

def tcm_list_hbas(option, opt_str, value, parser):

	for hba in os.listdir(tcm_root):
		if hba == "alua":
			continue

		print "\------> " + hba
		dev_root = tcm_root + "/" + hba
		p = os.open(dev_root + "/hba_info", 0)
		value = os.read(p, 128)
		print "        " + value.rstrip()
		os.close(p)

		for dev in os.listdir(dev_root):
			if dev == "hba_info":
				continue
			p = os.open(dev_root + "/" + dev + "/info", 0)
			value = os.read(p, 256)
			print "        \-------> " + dev
			print "        " + value.rstrip()
			os.close(p)

	return

def tcm_show_persistent_reserve_info(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		print "TCM/ConfigFS storage object does not exist: " + cfs_dev_path
		return -1

	pr_show_op = "cat " + cfs_dev_path + "/pr/*"
	ret = os.system(pr_show_op)
	if ret:
		print "Unable to disable storage object persistent reservation info"
		return -1

	return

def tcm_set_udev_path(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		print "TCM/ConfigFS storage object does not exist: " + cfs_dev_path
		return -1

	udev_path_set_op = "echo -n " + value[1] + " > " + cfs_dev_path + "/udev_path"
	ret = os.system(udev_path_set_op)
	if ret:
		print "Unable to set UDEV path for " + cfs_dev_path
		return -1

	print "Set UDEV Path: " + value[1] + " for " + cfs_dev_path
	return

def tcm_set_wwn_unit_serial(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		print "TCM/ConfigFS storage object does not exist: " + cfs_dev_path
		return -1

	wwn_show_op = "echo " + value[1] + " > " + cfs_dev_path + "/wwn/vpd_unit_serial"
	ret = os.system(wwn_show_op)
	if ret:
		print "Unable to set T10 WWN Unit Serial for " + cfs_dev_path
		return -1

	print "Set T10 WWN Unit Serial for " + cfs_unsplit + " to: " + value[1]
	return

def tcm_show_wwn_info(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		print "TCM/ConfigFS storage object does not exist: " + cfs_dev_path
		return -1

	wwn_show_op = "cat " + cfs_dev_path + "/wwn/*"
	ret = os.system(wwn_show_op)
	if ret:
		print "Unable to disable storage object WWN info"
		return -1

	return

def tcm_unload(option, opt_str, value, parser):

	hba_root = os.listdir(tcm_root)

	for f in hba_root:
		if f == "alua":
			continue;

		tcm_delhba(None, None, f, None)

	rmmod_op = "rmmod target_core_mod"
	ret = os.system(rmmod_op)
	if ret:
		print "Unable to rmmod target_core_mod"
		return -1

	return

def tcm_version(option, opt_str, value, parser):

	os.system("cat /sys/kernel/config/target/version")
	return

parser = OptionParser()
parser.add_option("--delhba", action="callback", callback=tcm_delhba, nargs=1,
		type="string", dest="HBA", help="Delete TCM Host Bus Adapter (HBA)")
parser.add_option("--createdev", action="callback", callback=tcm_createvirtdev, nargs=2,
		type="string", dest="HBA/DEV <params>", help="Create TCM Storage Object")
parser.add_option("--freedev", action="callback", callback=tcm_freevirtdev, nargs=1,
                type="string", dest="HBA/DEV", help="Free TCM Storage Object")
parser.add_option("--listhbas", action="callback", callback=tcm_list_hbas, nargs=0,
		help="List TCM Host Bus Adapters (HBAs)")
parser.add_option("--pr", action="callback", callback=tcm_show_persistent_reserve_info, nargs=1,
		type="string", dest="HBA/DEV", help="Show Persistent Reservation info")
parser.add_option("--setudevpath", action="callback", callback=tcm_set_udev_path, nargs=2,
		type="string", dest="HBA/DEV <udev_path>", help="Set UDEV Path Information, only used when --createdev did not contain <udev_path> as parameter")
parser.add_option("--setunitserial", action="callback", callback=tcm_set_wwn_unit_serial, nargs=2,
		type="string", dest="HBA/DEV <unit_serial>", help="Set T10 EVPD Unit Serial Information")
parser.add_option("--unload", action="callback", callback=tcm_unload, nargs=0,
		help="Unload target_core_mod")
parser.add_option("--version", action="callback", callback=tcm_version, nargs=0,
		help="Display target_core_mod version information")
parser.add_option("--wwn", action="callback", callback=tcm_show_wwn_info, nargs=1,
		type="string", dest="HBA/DEV", help="Show WWN info")

parser.parse_args()

