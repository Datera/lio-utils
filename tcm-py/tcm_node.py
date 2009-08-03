#!/usr/bin/python
import os, sys, signal
import subprocess as sub
import string
import re
import errno
from optparse import OptionParser

import tcm_pscsi
import tcm_iblock
import tcm_ramdisk
import tcm_fileio

import tcm_snap

tcm_root = "/sys/kernel/config/target/core"

def tcm_cat(fname):
    return file(fname).xreadlines()

def tcm_err(msg):
	print msg
	sys.exit(1)

def tcm_get_cfs_prefix(arg):
	path = "/sys/kernel/config/target/core/" + arg
	return path

def tcm_add_alua_lugp(option, opt_str, value, parser):
	lu_gp_name = str(value)

	if os.path.isdir(tcm_root + "/alua/lu_gps/" + lu_gp_name):
		tcm_err("ALUA Logical Unit Group: " + lu_gp_name + " already exists!")
	
	mkdir_op = "mkdir -p " + tcm_root + "/alua/lu_gps/" + lu_gp_name
	ret = os.system(mkdir_op)
	if ret:
		tcm_err("Unable to create ALUA Logical Unit Group: " + lu_gp_name)

	set_lu_gp_op = "echo 0 > " + tcm_root + "/alua/lu_gps/" + lu_gp_name + "/lu_gp_id"
	ret = os.system(set_lu_gp_op)
	if ret:
		rmdir_op = "rmdir " + tcm_root + "/alua/lu_gps/" + lu_gp_name
		test = os.system(rmdir_op)
		tcm_err("Unable to set ID for ALUA Logical Unit Group: " + lu_gp_name)
	else:
		print "Successfully created ALUA Logical Unit Group: " + lu_gp_name

	return

def tcm_add_alua_tgptgp(option, opt_str, value, parser):
	tg_pt_gp_name = str(value)

	if os.path.isdir(tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp_name):
		tcm_err("ALUA Target Port Group: " + tg_pt_gp_name + " already exists!")

	mkdir_op = "mkdir -p " + tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp_name
	ret = os.system(mkdir_op)
	if ret:
		tcm_err("Unable to create ALUA Target Port Group: " + tg_pt_gp_name)

	set_tg_pt_gp_op = "echo 0 > " + tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp_name + "/tg_pt_gp_id"
	ret = os.system(set_tg_pt_gp_op)
	if ret:
		rmdir_op = "rmdir " + tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp_name
		os.system(rmdir_op)
		tcm_err("Unable to set ID for ALUA Target Port Group: " + tg_pt_gp_name)
	else:
		print "Successfully created ALUA Target Port Group: " + tg_pt_gp_name

	return

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
		tcm_err("Unable to delete TCM HBA: " + hba_path)
	else:
		print "Successfully released TCM HBA: " + hba_path

	return

def tcm_del_alua_lugp(option, opt_str, value, parser):
	lu_gp_name = str(value)

	if not os.path.isdir(tcm_root + "/alua/lu_gps/" + lu_gp_name):
		tcm_err("ALUA Logical Unit Group: " + lu_gp_name + " does not exist!")

	rmdir_op = "rmdir "  + tcm_root + "/alua/lu_gps/" + lu_gp_name
	ret = os.system(rmdir_op)
	if ret:
		tcm_err("Unable to delete ALUA Logical Unit Group: " + lu_gp_name)
	else:
		print "Successfully deleted ALUA Logical Unit Group: " + lu_gp_name

	return

def tcm_del_alua_tgptgp(option, opt_str, value, parser):
	tg_pt_gp_name = str(value)

	if not os.path.isdir(tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp_name):
		tcm_err("ALUA Target Port Group: " + tg_pt_gp_name + " does not exist!")

	rmdir_op = "rmdir " + tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp_name
	ret = os.system(rmdir_op)
	if ret:
		tcm_err("Unable to delete ALUA Target Port Group: " + tg_pt_gp_name)
	else:
		print "Successfully deleted ALUA Target Port Group: " + tg_pt_gp_name

	return

def tcm_generate_uuid_for_unit_serial(cfs_dev_path):
	uuidgen_op = 'uuidgen'
	p = sub.Popen(uuidgen_op, shell=True, stdout=sub.PIPE).stdout
	uuid = p.readline()
	p.close()

	if not uuid:
		print "Unable to generate UUID using uuidgen, continuing anyway"
		return

	swus_val = [cfs_dev_path,uuid.rstrip()]
	tcm_set_wwn_unit_serial(None, None, swus_val, None)

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
			tcm_err("Unable to create TCM/ConfigFS HBA: " + cfs_hba_path)

	dev_vfs_alias = cfs_path_tmp[1]
	print " ConfigFS Device Alias: " + dev_vfs_alias
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path)):
		tcm_err("TCM/ConfigFS storage object already exists: " + cfs_dev_path)

	cfs_path = cfs_path_tmp[0] + "/" + cfs_path_tmp[1]

	tmp_params = str(value[1])
	dev_params = tmp_params.split(' ')
	plugin_params = dev_params
	print "Device Params " + str(plugin_params)
	
	ret = os.mkdir(cfs_dev_path)
	if ret:
		tcm_err("Failed to create ConfigFS Storage Object: " + cfs_dev_path + " ret: " + ret)

	# Calls into submodules depending on target_core_mod subsystem plugin
	ret = 0
	gen_uuid = 1
	# Determine if --establishdev is being called and we want to skip
	# the T10 Unit Serial Number generation
	if len(value) > 2:
		if str(value[2]) == "1":
			gen_uuid = 0

	result = re.search('pscsi_', hba_cfs)
	if result:
		gen_uuid = 0
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
			os.rmdir(cfs_dev_path)
			tcm_err("Unable to access " + cfs_dev_path + "/info for TCM storage object")

		if gen_uuid:
                        tcm_generate_uuid_for_unit_serial(cfs_path)

		print "Successfully created TCM/ConfigFS storage object: " + cfs_dev_path
	else:
		os.rmdir(cfs_dev_path);
		tcm_err("Unable to register TCM/ConfigFS storage object: " + cfs_dev_path)

	return

def tcm_establishvirtdev(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	plugin_params = str(value[1])

	vals = [cfs_dev, plugin_params, 1]
	tcm_createvirtdev(None, None, vals, None)
	return

def tcm_create_pscsi(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	ctl = str(value[1])

	ctl_params = ctl.split(':')

	pscsi_params = "scsi_channel_id=" + ctl_params[0] + ",scsi_target_id=" + ctl_params[1] + ",scsi_lun_id=" + ctl_params[2]
	vals = [cfs_dev, pscsi_params]
	tcm_createvirtdev(None, None, vals, None)
	return

def tcm_create_pscsibyudev(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	tmp_params = str(value[1])
	plugin_params = tmp_params.split(' ')

	print " ConfigFS Device Alias: " + cfs_dev
	ret = tcm_pscsi.pscsi_createvirtdev(cfs_dev, plugin_params)
	if not ret:
		print "Successfully created TCM/ConfigFS storage object: " + plugin_params[0]
	else:
		tcm_err("Unable to register TCM/ConfigFS storage object: " + plugin_params[0])

	return

def tcm_create_iblock(option, opt_str, value, parser):

	tcm_createvirtdev(option, opt_str, value, parser)
	return

def tcm_create_fileio(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	file = str(value[1])
	size_in_bytes = str(value[2])

	fileio_params = "fd_dev_name=" + file + ",fd_dev_size=" + size_in_bytes
	vals = [cfs_dev, fileio_params]	
	tcm_createvirtdev(None, None, vals, None)
	return

def tcm_create_ramdisk(option, opt_str, value, parser):

	tcm_createvirtdev(option, opt_str, value, parser)
	return

def tcm_freevirtdev(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_path = cfs_unsplit.split('/')
	hba_cfs = cfs_path[0]
	dev_vfs_alias = cfs_path[1]
	print " ConfigFS HBA: " + hba_cfs
	print " ConfigFS Device Alias: " + dev_vfs_alias

	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	snap_attr_path = cfs_dev_path + "/snap"
	if os.path.isdir(snap_attr_path) == True:
		tcm_snapshot_stop(None, None, value, None)

	ret = os.rmdir(cfs_dev_path)
	if not ret:
		print "Successfully released TCM/ConfigFS storage object: " + cfs_dev_path
	else:
		tcm_err("Failed to release ConfigFS Storage Object: " + cfs_dev_path + " ret: " + ret)

	return

def tcm_list_dev_attribs(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	print "TCM Storage Object Attributes for " + cfs_dev_path
	for attrib in os.listdir(cfs_dev_path + "/attrib/"):
		p = open(cfs_dev_path + "/attrib/" + attrib, 'rU')
		value = p.read(16)
		p.close()
		print "       " + attrib + ": " + value.rstrip()

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
			p = open(dev_root + "/" + dev + "/info", 'rU')
			try:
				value = p.read(256)
			except IOError, msg:
				print "        \-------> " + dev
				print "        No TCM object association active, skipping"
				p.close()
				continue
			
			p.close()
			u = os.open(dev_root + "/" + dev + "/udev_path", 0)
			udev_path = os.read(u, 256)
			if udev_path:
				udev_str = "udev_path: " + udev_path.rstrip()
			else:
				udev_str = "udev_path: N/A"

			print "        \-------> " + dev
			print "        " + value.rstrip()
			print "        " + udev_str
			os.close(u)

	return

def tcm_list_alua_lugps(option, opt_str, value, parser):

	for lu_gp in os.listdir(tcm_root + "/alua/lu_gps"):
		p = os.open(tcm_root + "/alua/lu_gps/" + lu_gp + "/lu_gp_id", 0)
		value = os.read(p, 8)
		lu_gp_id = value.rstrip();
		os.close(p)
		print "\------> " + lu_gp + "  LUN Group ID: " + lu_gp_id

		p = os.open(tcm_root + "/alua/lu_gps/" + lu_gp + "/members", 0)
		value = os.read(p, 4096)
		lu_gp_members = value.split('\n');
		os.close(p)

		if len(lu_gp_members) == 1:
			print "         No Logical Unit Group Members"
			continue

		i = 0
		while i < len(lu_gp_members) - 1:
			print "         " + lu_gp_members[i]
			i += 1

	return

def tcm_list_alua_tgptgps(option, opt_str, value, parser):

	for tg_pt_gp in os.listdir(tcm_root + "/alua/tg_pt_gps"):
		p = os.open(tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp + "/tg_pt_gp_id", 0)
		value = os.read(p, 8)
		tg_pt_gp_id = value.rstrip()
		os.close(p)
		print "\------> " + tg_pt_gp + "  Target Port Group ID: " + tg_pt_gp_id

		p = os.open(tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp + "/members", 0)
		value = os.read(p, 4096)
		tg_pt_gp_members = value.split('\n');
		os.close(p)

		if len(tg_pt_gp_members) == 1:
			print "         No Target Port Group Members"
			continue

		i = 0
		while i < len(tg_pt_gp_members) - 1:
			print "         " + tg_pt_gp_members[i]
			i += 1

        return

def tcm_snapshot_attr_set(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	tmp = str(value[1])
	
	out = tmp.split('=')
	if not out:
		tcm_err("Unable to locate snapshot attr=value")

	attr = out[0]
	value = out[1]

	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)
	
	p = open(cfs_dev_path + "/snap/" + attr, 'wU')
	val = p.write(value)
	if val:
		p.close()
		tcm_err("Unable to write to snap_attr: " + cfs_dev_path + "/snap/" + attr)

	p.close()
	print "Successfully updated snapshot attribute: " + attr + "=" + value + " for " + cfs_dev_path
	return

def tcm_snapshot_attr_show(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	snap_attr_path = cfs_dev_path + "/snap"
	for snap_attr in os.listdir(snap_attr_path):
		p = open(snap_attr_path + "/" + snap_attr, 'rU')
		val = p.read()
		p.close()
		print snap_attr +"=" + val.rstrip()	

	return

def tcm_snapshot_init(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	max_snapshots = int(value[1])
	lv_size = str(value[2])
	snap_interval = str(value[3])

	ret = tcm_snap.snap_set_cfs_defaults(cfs_dev_path, max_snapshots, lv_size, snap_interval)
	if ret:
		tcm_err("Unable to initialize snapshot attributes for " + cfs_dev_path)
	
	return

def tcm_snapshot_start(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	ret = tcm_snap.get_cfs_snap_enabled(cfs_dev_path)
	if ret:
		tcm_err("Not starting snapshot daemon because it is already enabled")

	lv_group = tcm_snap.get_cfs_snap_lvgroup(cfs_dev_path)
	if not lv_group:
		tcm_err("lv_group for snapshot not set, please initialize configfs snapshot attrs with --lvsnapinit");

	snap_size = tcm_snap.get_cfs_snap_size(cfs_dev_path)
	if not snap_size:
		tcm_err("size for snapshot not set, please initialize configfs snapshot attrs with --lvsnapinit");

	max_snapshots = tcm_snap.get_cfs_max_snapshots(cfs_dev_path)
	if not max_snapshots:
		tcm_err("max rotating snapshots value not set, please initialize configfs snapshot attrs with --lvsnapinit");

	ret = os.spawnlp(os.P_NOWAIT,"/usr/sbin/tcm_snap","tcm_snap","--p",cfs_dev_path)
	if not ret:
		tcm_err("Unable to start tcm_snap for: " + cfs_dev_path)

	print "Started tcm_snap daemon at pid: " + str(ret) + " for " + cfs_dev_path
	
	enabled_attr = cfs_dev_path + "/snap/enabled"
	p = open(enabled_attr, 'wU')
	if not p:
		tcm_err("Unable to open enabled_attr: " + enabled_attr)

	val = p.write("1")
	if val:
		p.close()
		tcm_err("Unable to set snap/enabled for " + cfs_dev_path)

	p.close()
	return

def tcm_snapshot_status(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	udev_path = tcm_snap.get_cfs_udev_path(cfs_dev_path)
	if not udev_path:
		tcm_err("Unable to locate udev path for LV snapshot")

	val = udev_path.split('/')
	if not val:
		tcm_err("Unable to split udev_path")

	# Assume that udev_path is in '/dev/$VG_GROUP/$LV_NAME' format
	vg_group = val[2]
#	print "vg_group: " + vg_group
	lv_name = val[3]
#	print "lv_name: " + lv_name
	
	tcm_snap.snap_dump_lvs_info(vg_group, lv_name)
	return

def tcm_snapshot_stop(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	enabled_attr = cfs_dev_path + "/snap/enabled"
	p = open(enabled_attr, 'rU')
	if not p:
		tcm_err("Unable to open enabled_attr: " + enabled_attr)

        val = p.read()
        p.close()
	if val.rstrip() == "0":
		return

	pid_attr = cfs_dev_path + "/snap/pid"
	p = open(pid_attr, 'rU')
	if not p:
		tcm_err("Unable to open pid_attr: " + pid_attr)

	val = p.read()
	pid = int(val.rstrip())
	p.close()
#	print "Located tcm_snap pid: " + str(pid) + " for " + cfs_dev_path
	try:
		os.kill(pid, signal.SIGKILL)
	except OSError, err:
		return err.errno == errno.EPERM

	print "Successfully stopped tcm_snap daemon for " + cfs_dev_path
	p = open(pid_attr, 'wU')
	if not p:
		tcm_err("Unable to open pid_attr: " + pid_attr)

	val = p.write("0")
	if val:
		print "Unable to clear snap pid"
	p.close()

	enabled_attr = cfs_dev_path + "/snap/enabled"
	p = open(enabled_attr, 'wU')
	if not p:
		tcm_err("Unable to open enabled_attr: " + enabled_attr)
		
	val = p.write("0")
	if val:
		p.close()
		tcm_err("Unable to set snap/enabled for " + cfs_dev_path)
	p.close()
	return

def tcm_show_persistent_reserve_info(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	pr_show_op = "cat " + cfs_dev_path + "/pr/*"
	ret = os.system(pr_show_op)
	if ret:
		tcm_err("Unable to disable storage object persistent reservation info")

	return

def tcm_set_alua_lugp(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	lu_gp_name = str(value[1])
	if not os.path.isdir(tcm_root + "/alua/lu_gps/" + lu_gp_name):
		tcm_err("ALUA Logical Unit Group: " + lu_gp_name + " does not exist!")

	lu_gp_set_op = "echo " + lu_gp_name + " > " + cfs_dev_path + "/alua_lu_gp"
	ret = os.system(lu_gp_set_op)
	if ret:
		tcm_err("Unable to set ALUA Logical Unit Group: " + lu_gp_name + " for TCM storage object: " + cfs_dev_path)
	else:
		print "Successfully set ALUA Logical Unit Group: " + lu_gp_name + " for TCM storage object: " + cfs_dev_path

	return

def tcm_set_dev_attrib(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	attrib = str(value[1])
	value = str(value[2])
	
	attrib_path_set_op = "echo " + value + " > " + cfs_dev_path + "/attrib/" + attrib
	ret = os.system(attrib_path_set_op)
	if ret:
		tcm_err("Unable to set TCM storage object attribute for:" + cfs_dev_path + "/attrib/" + attrib)
	else:
		print "Successfully set TCM storage object attribute: " + attrib + "=" + value + " for " + cfs_dev_path + "/attrib/" + attrib

	return

def tcm_set_udev_path(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	udev_path_set_op = "echo -n " + value[1] + " > " + cfs_dev_path + "/udev_path"
	ret = os.system(udev_path_set_op)
	if ret:
		tcm_err("Unable to set UDEV path for " + cfs_dev_path)

	print "Set UDEV Path: " + value[1] + " for " + cfs_dev_path
	return

def tcm_set_wwn_unit_serial(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	wwn_show_op = "echo " + value[1] + " > " + cfs_dev_path + "/wwn/vpd_unit_serial"
	ret = os.system(wwn_show_op)
	if ret:
		tcm_err("Unable to set T10 WWN Unit Serial for " + cfs_dev_path)

	print "Set T10 WWN Unit Serial for " + cfs_unsplit + " to: " + value[1]
	return

def tcm_show_udev_path(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	udev_path_show_op = "cat " + cfs_dev_path + "/udev_path"
	ret = os.system(udev_path_show_op)
	if ret:
		tcm_err("Unable to show UDEV path for " + cfs_dev_path)

	return

def tcm_show_wwn_info(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	wwn_show_op = "cat " + cfs_dev_path + "/wwn/*"
	ret = os.system(wwn_show_op)
	if ret:
		tcm_err("Unable to disable storage object WWN info")

	return

def tcm_unload(option, opt_str, value, parser):

	if not os.path.isdir(tcm_root):
		tcm_err("Unable to access tcm_root: " + tcm_root)

	hba_root = os.listdir(tcm_root)

	for f in hba_root:
		if f == "alua":
			continue;

		tcm_delhba(None, None, f, None)

	for tg_pt_gp in os.listdir(tcm_root + "/alua/tg_pt_gps"):
		if tg_pt_gp == "default_tg_pt_gp":
			continue

		tcm_del_alua_tgptgp(None, None, tg_pt_gp, None)		

	for lu_gp in os.listdir(tcm_root + "/alua/lu_gps"):
		if lu_gp == "default_lu_gp":
			continue

		tcm_del_alua_lugp(None, None, lu_gp, None)

	rmmod_op = "rmmod target_core_mod"
	ret = os.system(rmmod_op)
	if ret:
		tcm_err("Unable to rmmod target_core_mod")

	return

def tcm_version(option, opt_str, value, parser):

	os.system("cat /sys/kernel/config/target/version")
	return

def main():

	parser = OptionParser()
	parser.add_option("--addlungp", action="callback", callback=tcm_add_alua_lugp, nargs=1,
			type="string", dest="lu_gp_name", help="Add ALUA Logical Unit Group")
	parser.add_option("--addtgptgp", action="callback", callback=tcm_add_alua_tgptgp, nargs=1,
			type="string", dest="tg_pt_gp_name", help="Add ALUA Target Port Group")
	parser.add_option("--block","--iblock", action="callback", callback=tcm_create_iblock, nargs=2,
			type="string", dest="HBA/DEV <UDEV_PATH>", help="Associate TCM/IBLOCK object with Linux/BLOCK device")
	parser.add_option("--delhba", action="callback", callback=tcm_delhba, nargs=1,
			type="string", dest="HBA", help="Delete TCM Host Bus Adapter (HBA)")
	parser.add_option("--dellungp", action="callback", callback=tcm_del_alua_lugp, nargs=1,
			type="string", dest="lu_gp_name", help="Delete ALUA Logical Unit Group")
	parser.add_option("--deltgptgp", action="callback", callback=tcm_del_alua_tgptgp, nargs=1,
			type="string", dest="tg_pt_gp_name", help="Delete ALUA Target Port Group")
	parser.add_option("--createdev", action="callback", callback=tcm_createvirtdev, nargs=2,
			type="string", dest="HBA/DEV <SUBSYSTEM_PARAMS>", help="Create TCM Storage Object using subsystem dependent parameters, and generate new T10 Unit Serial for IBLOCK,FILEIO,RAMDISK")
	parser.add_option("--establishdev", action="callback", callback=tcm_establishvirtdev, nargs=2,
			type="string", dest="HBA/DEV <SUBSYSTEM_PARAMS>", help="Create TCM Storage Object using subsystem dependent parameters, do not generate new T10 Unit Serial")
	parser.add_option("--fileio", action="callback", callback=tcm_create_fileio, nargs=3,
			type="string", dest="HBA/DEV <FILE> <SIZE_IN_BYTES>", help="Associate TCM/FILEIO object with Linux/VFS file or underlying device for buffered FILEIO")
	parser.add_option("--freedev", action="callback", callback=tcm_freevirtdev, nargs=1,
			type="string", dest="HBA/DEV", help="Free TCM Storage Object")
	parser.add_option("--listdevattr", action="callback", callback=tcm_list_dev_attribs, nargs=1,
			type="string", dest="HBA/DEV", help="List TCM storage object device attributes")
	parser.add_option("--listhbas", action="callback", callback=tcm_list_hbas, nargs=0,
			help="List TCM Host Bus Adapters (HBAs)")
        parser.add_option("--listlugps", action="callback", callback=tcm_list_alua_lugps, nargs=0,
                        help="List ALUA Logical Unit Groups")
        parser.add_option("--listtgptgps", action="callback", callback=tcm_list_alua_tgptgps, nargs=0,
                        help="List ALUA Target Port Groups");
	parser.add_option("--lvsnapattrset", action="callback", callback=tcm_snapshot_attr_set, nargs=2,
			type="string", dest="HBA/DEV ATTR=VALUE", help="Set LV snapshot configfs attributes for TCM/IBLOCK storage object");
	parser.add_option("--lvsnapattrshow", action="callback", callback=tcm_snapshot_attr_show, nargs=1,
			type="string", dest="HBA/DEV", help="Show LV snapshot configfs attributes for TCM/IBLOCK storage object");
	parser.add_option("--lvsnapinit", action="callback", callback=tcm_snapshot_init, nargs=4,
			type="string", dest="HBA/DEV MAX_SNAPSHOTS SNAP_SIZE_STR SNAP_INTERVAL_STR", help="Initialize snapshot with default attributes");
	parser.add_option("--lvsnapstart", action="callback", callback=tcm_snapshot_start, nargs=1,
			type="string", dest="HBA/DEV", help="Enable snapshot daemon for TCM/IBLOCK LVM storage object");
	parser.add_option("--lvsnapstat", action="callback", callback=tcm_snapshot_status, nargs=1,
			type="string", dest="HBA/DEV", help="Display LV snapshot status for TCM/IBLOCK LVM storage object");
	parser.add_option("--lvsnapstop", action="callback", callback=tcm_snapshot_stop, nargs=1,
			type="string", dest="HBA/DEV", help="Disable snapshot daemon for TCM/IBLOCK LVM storage object");
	parser.add_option("--pr", action="callback", callback=tcm_show_persistent_reserve_info, nargs=1,
			type="string", dest="HBA/DEV", help="Show Persistent Reservation info")
	parser.add_option("--ramdisk", action="callback", callback=tcm_create_ramdisk, nargs=2,
			type="string", dest="HBA/DEV <PAGES>", help="Create and associate TCM/RAMDISK object")
	parser.add_option("--scsi","--pscsi", action="callback", callback=tcm_create_pscsi, nargs=2,
			type="string", dest="HBA/DEV <C:T:L>", help="Associate TCM/pSCSI object with Linux/SCSI device by bus location")
	parser.add_option("--scsibyudev", "--pscsibyudev", action="callback", callback=tcm_create_pscsibyudev, nargs=2,
			type="string", dest="DEV <UDEV_PATH>", help="Associate TCM/pSCSI object with Linux/SCSI device by UDEV Path")
	parser.add_option("--setdevattr", action="callback", callback=tcm_set_dev_attrib, nargs=3,
			type="string", dest="HBA/DEV <ATTRIB> <VALUE>", help="Set new value for TCM storage object device attribute")
	parser.add_option("--setlugp", action="callback", callback=tcm_set_alua_lugp, nargs=2,
			type="string", dest="HBA/DEV LU_GP_NAME", help="Set ALUA Logical Unit Group")
	parser.add_option("--setudevpath", action="callback", callback=tcm_set_udev_path, nargs=2,
			type="string", dest="HBA/DEV <udev_path>", help="Set UDEV Path Information, only used when --createdev did not contain <udev_path> as parameter")
	parser.add_option("--setunitserial", action="callback", callback=tcm_set_wwn_unit_serial, nargs=2,
			type="string", dest="HBA/DEV <unit_serial>", help="Set T10 EVPD Unit Serial Information")
	parser.add_option("--udevpath", action="callback", callback=tcm_show_udev_path, nargs=1,
	
			type="string", dest="HBA/DEV", help="Show UDEV Path Information for TCM storage object")
	parser.add_option("--unload", action="callback", callback=tcm_unload, nargs=0,
			help="Unload target_core_mod")
	parser.add_option("--version", action="callback", callback=tcm_version, nargs=0,
			help="Display target_core_mod version information")
	parser.add_option("--wwn", action="callback", callback=tcm_show_wwn_info, nargs=1,
			type="string", dest="HBA/DEV", help="Show WWN info")

	(options, args) = parser.parse_args()
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)
	elif not re.search('--', sys.argv[1]):
		tcm_err("Unknown CLI option: " + sys.argv[1])

if __name__ == "__main__":
	main()
