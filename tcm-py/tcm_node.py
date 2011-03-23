#!/usr/bin/python
import os, sys, signal
import subprocess as sub
import string
import re
import errno
import uuid
import shutil
from optparse import OptionParser

import tcm_pscsi
import tcm_iblock
import tcm_ramdisk
import tcm_fileio

import tcm_snap

tcm_root = "/sys/kernel/config/target/core"

def tcm_err(msg):
	print msg
	sys.exit(1)

def tcm_read(filename):
	with open(filename) as f:
		return f.read()

def tcm_write(filename, value, newline=True):
	with open(filename, "w") as f:
		f.write(value)
		if newline:
			f.write("\n")

def tcm_get_cfs_prefix(arg):
	return tcm_root + "/" + arg

def tcm_check_dev_exists(cfs_dev_path):
	if not os.path.isdir(cfs_dev_path):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

def tcm_add_alua_lugp(option, opt_str, value, parser):
	lu_gp_name = str(value)

	os.makedirs(tcm_root + "/alua/lu_gps/" + lu_gp_name)

	try:
		tcm_write(tcm_root + "/alua/lu_gps/%s/lu_gp_id" % lu_gp_name, lu_gp_name)
	except:
		os.rmdir(tcm_root + "/alua/lu_gps/" + lu_gp_name)
		raise

def tcm_add_alua_tgptgp(option, opt_str, value, parser):
	cfs_dev_path = tcm_get_cfs_prefix(str(value[0]))
	tg_pt_gp_name = str(value[1]) + "/"
	alua_cfs_path = cfs_dev_path + "alua/" + tg_pt_gp_name

	tcm_check_dev_exists(cfs_dev_path)

	os.makedirs(alua_cfs_path)

	try:
		tcm_write(alua_cfs_path + "tg_pt_gp_id", "0")
	except:
		os.rmdir(alua_cfs_path)
		raise

def tcm_alua_check_metadata_dir(cfs_dev_path):

	alua_path = "/var/target/alua/tpgs_" + tcm_get_unit_serial(cfs_dev_path) + "/"
	if os.path.isdir(alua_path):
		return

	# Create the ALUA metadata directory for the passed storage object
	# if it does not already exist.
        os.makedirs(alua_path)

def tcm_alua_delete_metadata_dir(unit_serial):

	alua_path = "/var/target/alua/tpgs_" + unit_serial + "/"
	if os.path.isdir(alua_path) == False:
		return

	os.rmdir(alua_path)

def tcm_alua_process_metadata(cfs_dev_path, tg_pt_gp_name, tg_pt_gp_id):
	alua_cfs_path = cfs_dev_path + "/alua/" + tg_pt_gp_name
	unit_serial = tcm_get_unit_serial(cfs_dev_path)
	alua_path = "/var/target/alua/tpgs_" + unit_serial + "/" + tg_pt_gp_name

	if not os.path.isfile(alua_path):
		# If not pre-existing ALUA metadata exists, go ahead and
		# allow new ALUA state changes to create and update the
		# struct file metadata
		tcm_write(alua_cfs_path + "/alua_write_metadata", "1")
		return

	with open(alua_path, 'rU') as p:
		d = dict()
		for line in p.readlines():
			name, value = line.split("=")
			d[name.strip()] = value.strip()

	if "tg_pt_gp_id" in d and int(d["tg_pt_gp_id"]) != int(tg_pt_gp_id):
		raise IOError("Passed tg_pt_gp_id: %s does not match extracted: %s" % \
			(tg_pt_gp_id, d["tg_pt_gp_id"]))

	if "alua_access_state" in d:
		tcm_write(alua_cfs_path + "/alua_access_state", d["alua_access_state"])

	if "alua_access_status" in d:
		tcm_write(alua_cfs_path + "/alua_access_status", d["alua_access_status"])

	# Now allow changes to ALUA target port group update the struct file metadata
	# in /var/target/alua/tpgs_$T10_UNIT_SERIAL/$TG_PT_GP_NAME
	tcm_write(alua_cfs_path + "/alua_write_metadata", "1")

def tcm_add_alua_tgptgp_with_md(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	tg_pt_gp_name = str(value[1])
	tg_pt_gp_id = str(value[2])

	# If the default_tg_pt_gp is passed, we skip the creation (as it already exists)
	# and just process ALUA metadata
	if tg_pt_gp_name == 'default_tg_pt_gp' and tg_pt_gp_id == '0':
		tcm_alua_process_metadata(cfs_dev_path, tg_pt_gp_name, tg_pt_gp_id)
		return

	os.makedirs(cfs_dev_path + "/alua/" + tg_pt_gp_name)

	try:
		tcm_write(cfs_dev_path + "/alua/" + tg_pt_gp_name + "/tg_pt_gp_id",  tg_pt_gp_id)
	except:
		os.rmdir(cfs_dev_path + "/alua/" + tg_pt_gp_name)
		raise

	# Now process the ALUA metadata for this group
	tcm_alua_process_metadata(cfs_dev_path, tg_pt_gp_name, tg_pt_gp_id)

def tcm_delhba(option, opt_str, value, parser):
	hba_name = str(value)

	hba_path = tcm_root + "/" + hba_name

	for g in os.listdir(hba_path + "/"):
		if g == "hba_info" or g == "hba_mode":
			continue

		__tcm_freevirtdev(hba_name + "/" + g)

	os.rmdir(hba_path)

def tcm_del_alua_lugp(option, opt_str, value, parser):
	lu_gp_name = str(value)

	if not os.path.isdir(tcm_root + "/alua/lu_gps/" + lu_gp_name):
		tcm_err("ALUA Logical Unit Group: " + lu_gp_name + " does not exist!")

	os.rmdir(tcm_root + "/alua/lu_gps/" + lu_gp_name)

def __tcm_del_alua_tgptgp(values):
	cfs_unsplit = str(values[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	tg_pt_gp_name = str(values[1])
	if not os.path.isdir(cfs_dev_path + "/alua/" + tg_pt_gp_name):
		tcm_err("ALUA Target Port Group: " + tg_pt_gp_name + " does not exist!")

	os.rmdir(cfs_dev_path + "/alua/" + tg_pt_gp_name)

def tcm_del_alua_tgptgp(option, opt_str, values, parser):
	cfs_unsplit = str(values[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	unit_serial = tcm_get_unit_serial(cfs_dev_path)
	tg_pt_gp_name = str(values[1])
	alua_md_path = "/var/target/alua/tpgs_" + unit_serial + "/" + tg_pt_gp_name

	__tcm_del_alua_tgptgp(values)

	if os.path.isfile(alua_md_path) == False:
		return

	shutil.rmtree(alua_md_path)

def tcm_generate_uuid_for_unit_serial(cfs_dev_path):
	# Generate random uuid
	uuid = str(uuid.uuid4())
	tcm_set_wwn_unit_serial(None, None, (cfs_dev_path, uuid), None)

tcm_types = ( \
    dict(name="pscsi", module=tcm_pscsi, gen_uuid=False),
    dict(name="stgt", module=None, gen_uuid=True),
    dict(name="iblock", module=tcm_iblock, gen_uuid=True),
    dict(name="rd_dr", module=tcm_ramdisk, gen_uuid=True),
    dict(name="rd_mcp", module=tcm_ramdisk, gen_uuid=True),
    dict(name="fileio", module=tcm_fileio, gen_uuid=True),
)

def tcm_createvirtdev(option, opt_str, value, parser):
	hba_cfs, dev_vfs_alias = value[0].split('/')
	plugin_params = value[1].split(' ')
	print "Device Params " + str(plugin_params)

	# create hba if it doesn't exist
	cfs_hba_path = tcm_get_cfs_prefix(hba_cfs)
	if not os.path.isdir(cfs_hba_path):
		os.mkdir(cfs_hba_path)

	# create dev if it doesn't exist
	cfs_dev_path = cfs_hba_path + "/" + dev_vfs_alias
	if os.path.isdir(cfs_dev_path):
		tcm_err("TCM/ConfigFS storage object already exists: " + cfs_dev_path)
	else:
		os.mkdir(cfs_dev_path)

	# Determine if --establishdev is being called and we want to skip
	# the T10 Unit Serial Number generation
	gen_uuid = True
	if len(value) > 2 and str(value[2]) == "1":
		gen_uuid = False

	# Calls into submodules depending on target_core_mod subsystem plugin
	for tcm in tcm_types:
		if hba_cfs.startswith(tcm["name" + "_"]):
			try:
				if tcm["module"]:
					tcm["module"].createvirtdev(cfs_path, plugin_params)
				else:
					print "no module for %s" % tcm["name"]
			except:
				os.rmdir(cfs_dev_path);
				print "Unable to register TCM/ConfigFS storage object: " \
					+ cfs_dev_path
				raise

			print tcm_read(cfs_dev_path + "/info")

			if tcm["gen_uuid"] and gen_uuid:
        	                tcm_generate_uuid_for_unit_serial(cfs_dev_path)
				tcm_alua_check_metadata_dir(cfs_dev_path)
			break

def tcm_get_unit_serial(cfs_dev_path):
	string = tcm_read(cfs_dev_path + "/wwn/vpd_unit_serial")
	return string.split(":")[1].strip()

def tcm_show_aptpl_metadata(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	hba_cfs, dev_vfs_alias = cfs_unsplit.split('/')
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	aptpl_file = "/var/target/pr/aptpl_" + tcm_get_unit_serial(cfs_dev_path)
	if not os.path.isfile(aptpl_file):
		tcm_err("Unable to dump PR APTPL metadata file: " + aptpl_file)

	print tcm_read(aptpl_file)

def tcm_delete_aptpl_metadata(unit_serial):
	aptpl_file = "/var/target/pr/aptpl_" + unit_serial
	if not os.path.isfile(aptpl_file):
		return

	shutil.rmtree(aptpl_file)

def tcm_process_aptpl_metadata(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	hba_cfs, dev_vfs_alias = cfs_unsplit.split('/')
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	aptpl_file = "/var/target/pr/aptpl_" + tcm_get_unit_serial(cfs_dev_path)
	if not os.path.isfile(aptpl_file):
		return

	# read PR info from file
	lines = tcm_read(aptpl_file).split()

	if not lines[0].startswith("PR_REG_START:"):
		return

	reservations = []
	for line in lines:
		if line.startswith("PR_REG_START:"):
			res_list = []
		elif line.startswith("PR_REG_END:"):
			reservations.append(res_list)
		else:
			res_list.append(line.strip())

	# write info into configfs
	for res in reservations:
		tcm_write(cfs_dev_path + "/pr/res_aptpl_metadata", ",".join(res))
	
def tcm_establishvirtdev(option, opt_str, value, parser):
	tcm_createvirtdev(None, None, (str(value[0]), str(value[1]), 1), None)

def tcm_create_pscsi(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	ctl = str(value[1])

	ctl_params = ctl.split(':')

	pscsi_params = "scsi_channel_id=" + ctl_params[0] + ",scsi_target_id=" + ctl_params[1] + ",scsi_lun_id=" + ctl_params[2]
	vals = [cfs_dev, pscsi_params]
	tcm_createvirtdev(None, None, vals, None)

def tcm_create_pscsibyudev(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	tmp_params = str(value[1])
	plugin_params = tmp_params.split(' ')

	print " ConfigFS Device Alias: " + cfs_dev
	tcm_createvirtdev(option, opt_str, value, parser)

def tcm_create_iblock(option, opt_str, value, parser):

	tcm_createvirtdev(option, opt_str, value, parser)

def tcm_create_fileio(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	file = str(value[1])
	size_in_bytes = str(value[2])

	fileio_params = "fd_dev_name=" + file + ",fd_dev_size=" + size_in_bytes
	vals = [cfs_dev, fileio_params]	
	tcm_createvirtdev(None, None, vals, None)

def tcm_create_ramdisk(option, opt_str, value, parser):

	tcm_createvirtdev(option, opt_str, value, parser)

def __tcm_freevirtdev(value):
	cfs_unsplit = str(value)
	cfs_path = cfs_unsplit.split('/')
	hba_cfs = cfs_path[0]
	dev_vfs_alias = cfs_path[1]
	print " ConfigFS HBA: " + hba_cfs
	print " ConfigFS Device Alias: " + dev_vfs_alias

	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	if os.path.isdir(cfs_dev_path + "/snap"):
		tcm_snapshot_stop(None, None, value, None)

	if os.path.isdir(cfs_dev_path + "/alua/"):
		for tg_pt_gp in os.listdir(cfs_dev_path + "/alua/"):
			if tg_pt_gp == "default_tg_pt_gp":
				continue
			vals = (value, tg_pt_gp)
			__tcm_del_alua_tgptgp(vals)

	os.rmdir(cfs_dev_path)

def tcm_freevirtdev(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	unit_serial = tcm_get_unit_serial(cfs_dev_path)

	__tcm_freevirtdev(value)
	# For explict tcm_node --freedev, delete any remaining
	# PR APTPL and ALUA metadata
	tcm_delete_aptpl_metadata(unit_serial)
	tcm_alua_delete_metadata_dir(unit_serial)

def tcm_list_dev_attribs(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	print "TCM Storage Object Attributes for " + cfs_dev_path
	for attrib in os.listdir(cfs_dev_path + "/attrib/"):
		with open(cfs_dev_path + "/attrib/" + attrib) as p:
			print "       %s: %s" % (attrib, p.read(16).strip())

def tcm_list_hbas(option, opt_str, value, parser):

	for hba in os.listdir(tcm_root):
		if hba == "alua":
			continue

		print "\------> " + hba
		dev_root = tcm_root + "/" + hba
		print "\t" + tcm_read(dev_root+"/hba_info").strip()

		for dev in os.listdir(dev_root):
			if dev in ("hba_info", "hba_mode"):
				continue

			try:
				value = tcm_read(dev_root + "/" + dev + "/info")
			except IOError, msg:
				print "        \-------> " + dev
				print "        No TCM object association active, skipping"
				continue

			udev_path = tcm_read(dev_root + "/" + dev + "/udev_path")
			if udev_path:
				udev_str = "udev_path: " + udev_path.rstrip()
			else:
				udev_str = "udev_path: N/A"

			print "        \-------> " + dev
			print "        " + value.rstrip()
			print "        " + udev_str

def tcm_list_alua_lugps(option, opt_str, value, parser):

	for lu_gp in os.listdir(tcm_root + "/alua/lu_gps"):
		group_path = tcm_root + "/alua/lu_gps/" + lu_gp
		lu_gp_id = tcm_read(group_path + "/lu_gp_id").strip()
		print "\------> " + lu_gp + "  LUN Group ID: " + lu_gp_id

		lu_gp_members = tcm_read(group_path + "/members").strip().split()

		if not lu_gp_members:
			print "         No Logical Unit Group Members"
			continue

		for member in lu_gp_members:
			print "         " + member

def tcm_dump_alua_state(alua_state_no):
	
	if alua_state_no == "0":
		return "Active/Optimized"
	elif alua_state_no == "1":
		return "Active/NonOptimized"
	elif alua_state_no == "2":
		return "Standby"
	elif alua_state_no == "3":
		return "Unavailable"
	elif alua_state_no == "15":
		return "Transition"
	else:
		return "Unknown"

def tcm_list_alua_tgptgp(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	tg_pt_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + tg_pt_gp
	
	if not os.path.isdir(tg_pt_gp_base):
		tcm_err("Unable to access tg_pt_gp_base: " + tg_pt_gp_base)

	tg_pt_gp_id = tcm_read(tg_pt_gp_base + "/tg_pt_gp_id").strip()
	print "\------> " + tg_pt_gp + "  Target Port Group ID: " + tg_pt_gp_id

	alua_type = tcm_read(tg_pt_gp_base + "/alua_access_type").strip()
	print "         Active ALUA Access Type(s): " + alua_type

	alua_state = tcm_read(tg_pt_gp_base + "/alua_access_state").strip()
	print "         Primary Access State: " + tcm_dump_alua_state(alua_state)

	try:
		access_status = tcm_read(tg_pt_gp_base + "/alua_access_status").strip()
		print "         Primary Access Status: " + access_status
	except IOError:
		pass

	preferred = tcm_read(tg_pt_gp_base + "/preferred").strip()
	print "         Preferred Bit: " + preferred

	nonop_delay = tcm_read(tg_pt_gp_base + "/nonop_delay_msecs").strip()
	print "         Active/NonOptimized Delay in milliseconds: " + nonop_delay


	trans_delay = tcm_read(tg_pt_gp_base + "/trans_delay_msecs").strip()
	print "         Transition Delay in milliseconds: " + trans_delay

	p = os.open(tg_pt_gp_base + "/members", 0)
	value = os.read(p, 4096)
	tg_pt_gp_members = value.split('\n');
	os.close(p)

	tg_pt_gp_members = tcm_read(group_path + "/members").strip().split()

	print "         \------> TG Port Group Members"
	if not lu_gp_members:
		print "             No Target Port Group Members"
	else:
		for member in tg_pt_gp_members:
			print "         " + member

def tcm_list_alua_tgptgps(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	for tg_pt_gp in os.listdir(cfs_dev_path + "/alua/"):
		vals = [str(value), tg_pt_gp]
		tcm_list_alua_tgptgp(None, None, vals, None)

def tcm_snapshot_attr_set(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	tmp = str(value[1])
	
	attr, value = tmp.split('=')

	tcm_check_dev_exists(cfs_dev_path)

	tcm_write(cfs_dev_path + "/snap/" + attr, value)
	print "Successfully updated snapshot attribute: %s=%s for %s" % \
		(attr, value, cfs_dev_path)

def tcm_snapshot_attr_show(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	snap_attr_path = cfs_dev_path + "/snap"
	for snap_attr in os.listdir(snap_attr_path):
		print snap_attr + "=" + tcm_read(snap_attr_path + "/" + snap_attr).strip()

def tcm_snapshot_init(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	max_snapshots = int(value[1])
	lv_size = str(value[2])
	snap_interval = str(value[3])

	ret = tcm_snap.snap_set_cfs_defaults(cfs_dev_path, max_snapshots, lv_size, snap_interval)
	if ret:
		tcm_err("Unable to initialize snapshot attributes for " + cfs_dev_path)

def tcm_snapshot_start(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

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
	p = open(enabled_attr, 'w')
	if not p:
		tcm_err("Unable to open enabled_attr: " + enabled_attr)

	val = p.write("1")
	if val:
		p.close()
		tcm_err("Unable to set snap/enabled for " + cfs_dev_path)

	p.close()

def tcm_snapshot_status(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

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

def tcm_snapshot_stop(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

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
	p = open(pid_attr, 'w')
	if not p:
		tcm_err("Unable to open pid_attr: " + pid_attr)

	val = p.write("0")
	if val:
		print "Unable to clear snap pid"
	p.close()

	enabled_attr = cfs_dev_path + "/snap/enabled"
	p = open(enabled_attr, 'w')
	if not p:
		tcm_err("Unable to open enabled_attr: " + enabled_attr)
		
	val = p.write("0")
	if val:
		p.close()
		tcm_err("Unable to set snap/enabled for " + cfs_dev_path)
	p.close()

def tcm_show_persistent_reserve_info(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	for f in os.listdir(cfs_dev_path + "/pr/"):
		info = tcm_read(cfs_dev_path + "/pr/" + f).strip()
		if info:
			print info

def tcm_set_alua_state(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	alua_gp = str(value[1])
	new_alua_state_str = str(value[2]).lower()
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp

	if new_alua_state_str == "o":
		alua_state = 0; # Active/Optimized
	elif new_alua_state_str == "a":
		alua_state = 1 # Active/NonOptimized
	elif new_alua_state_str == "s":
		alua_state = 2 # Standby
	elif new_alua_state_str == "u":
		alua_state = 3 # Unavailable
	else:
		tcm_err("Unknown ALUA access state: " + new_alua_state_str)

	tcm_write(tg_pt_gp_base + "/alua_access_state", str(alua_state))

def tcm_set_alua_type(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	alua_gp = str(value[1])
	new_alua_type_str = str(value[2]).lower()
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp

	if new_alua_type_str == "both":
		alua_type = 3
	elif new_alua_type_str == "explict":
		alua_type = 2
	elif new_alua_type_str == "implict":
		alua_type = 1
	elif new_alua_type_str == "none":
		alua_type = 0
	else:
		tcm_err("Unknown ALUA access type: " + new_alua_type_str)

	tcm_write(tg_pt_gp_base + "/alua_access_type", str(alua_type))

def tcm_set_alua_nonop_delay(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if not os.path.isdir(tg_pt_gp_base):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	delay_msecs = str(value[2])

	tcm_write(tg_pt_gp_base + "/nonop_delay_msecs", delay_msecs)

def tcm_set_alua_trans_delay(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if not os.path.isdir(tg_pt_gp_base):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	delay_msecs = str(value[2])

	tcm_write(tg_pt_gp_base + "/trans_delay_msecs", delay_msecs)

def tcm_clear_alua_tgpt_pref(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if not os.path.isdir(tg_pt_gp_base):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	tcm_write(tg_pt_gp_base + "/preferred", "0")

def tcm_set_alua_tgpt_pref(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if not os.path.isdir(tg_pt_gp_base):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	tcm_write(tg_pt_gp_base + "/preferred", "1")

def tcm_set_alua_lugp(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	lu_gp_name = str(value[1])
	if not os.path.isdir(tcm_root + "/alua/lu_gps/" + lu_gp_name):
		tcm_err("ALUA Logical Unit Group: " + lu_gp_name + " does not exist!")

	tcm_write(cfs_dev_path + "/alua_lu_gp", lu_gp_name)

def tcm_set_dev_attrib(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	attrib = str(value[1])
	value = str(value[2])

	tcm_write(cfs_dev_path + "/attrib/" + attrib, value)

def tcm_set_udev_path(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	tcm_write(cfs_dev_path + "/udev_path", value[1], newline=False)

def tcm_set_wwn_unit_serial(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	tcm_write(cfs_dev_path + "/wwn/vpd_unit_serial", value[1])

def tcm_set_wwn_unit_serial_with_md(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	tcm_set_wwn_unit_serial(None, None, value, None);
	# Process PR APTPL metadata
	tcm_process_aptpl_metadata(None, None, cfs_unsplit, None)
	# Make sure the ALUA metadata directory exists for this storage object
	tcm_alua_check_metadata_dir(cfs_dev_path)

def tcm_show_udev_path(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	print tcm_read(cfs_dev_path + "/udev_path")

def tcm_show_wwn_info(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)

	tcm_check_dev_exists(cfs_dev_path)

	for f in os.listdir(cfs_dev_path + "/wwn/"):
		info = tcm_read(cfs_dev_path + "/wwn/" + f).strip()
		if info:
			print info

def tcm_unload(option, opt_str, value, parser):

	if not os.path.isdir(tcm_root):
		tcm_err("Unable to access tcm_root: " + tcm_root)

	hba_root = os.listdir(tcm_root)

	for f in hba_root:
		if f == "alua":
			continue;

		tcm_delhba(None, None, f, None)

	for lu_gp in os.listdir(tcm_root + "/alua/lu_gps"):
		if lu_gp == "default_lu_gp":
			continue

		tcm_del_alua_lugp(None, None, lu_gp, None)

	# Unload TCM subsystem plugin modules
	for module in ("iblock", "file", "pscsi", "stgt"):
		os.system("rmmod target_core_%s" % module)

	# Unload TCM Core
	rmmod_op = "rmmod target_core_mod"
	ret = os.system(rmmod_op)
	if ret:
		tcm_err("Unable to rmmod target_core_mod")

def tcm_version(option, opt_str, value, parser):
	print tcm_read("/sys/kernel/config/target/version").strip()

cmdline_options = ( \
    dict(opt_str="--addlungp", callback=tcm_add_alua_lugp, nargs=1,
         dest="lu_gp_name", help="Add ALUA Logical Unit Group"),
    dict(opt_str=("--addtgptgp","--addaluatpg"),
         callback=tcm_add_alua_tgptgp, nargs=2,
         dest="HBA/DEV <TG_PT_GP_NAME>",
         help="Add ALUA Target Port Group to Storage Object"),
    dict(opt_str=("--addtgptgpwithmd","--addaluatpgwithmd"), action="callback",
         callback=tcm_add_alua_tgptgp_with_md, nargs=3,
         dest="HBA/DEV <TG_PT_GP_NAME> <TG_PT_GP_ID>",
         help="Add ALUA Target Port Group to Storage Object with ID and process ALUA metadata"),
    dict(opt_str=("--block","--iblock"), callback=tcm_create_iblock, nargs=2,
         dest="HBA/DEV <UDEV_PATH>",
         help="Associate TCM/IBLOCK object with Linux/BLOCK device"),
    dict(opt_str="--clearaluapref", callback=tcm_clear_alua_tgpt_pref,
         nargs=2, dest="HBA/DEV <TG_PT_GP_NAME>",
         help="Clear ALUA Target Port Group Preferred Bit"),
    dict(opt_str="--delhba", callback=tcm_delhba, nargs=1,
         dest="HBA", help="Delete TCM Host Bus Adapter (HBA)"),
    dict(opt_str="--dellungp", callback=tcm_del_alua_lugp, nargs=1,
         dest="lu_gp_name", help="Delete ALUA Logical Unit Group"),
    dict(opt_str=("--deltgptgp","--delaluatpg"), callback=tcm_del_alua_tgptgp, nargs=2,
         dest="HBA/DEV TG_PT_GP_NAME",
         help="Delete ALUA Target Port Group from Storage Object"),
    dict(opt_str="--createdev", callback=tcm_createvirtdev, nargs=2,
         dest="HBA/DEV <SUBSYSTEM_PARAMS>",
         help="Create TCM Storage Object using subsystem dependent parameters,"
         " and generate new T10 Unit Serial for IBLOCK,FILEIO,RAMDISK"),
    dict(opt_str="--establishdev", callback=tcm_establishvirtdev, nargs=2,
         dest="HBA/DEV <SUBSYSTEM_PARAMS>",
         help="Create TCM Storage Object using subsystem dependent parameters, do"
         "not generate new T10 Unit Serial"),
    dict(opt_str="--fileio", callback=tcm_create_fileio, nargs=3,
         dest="HBA/DEV <FILE> <SIZE_IN_BYTES>",
         help="Associate TCM/FILEIO object with Linux/VFS file or underlying"
         " device for buffered FILEIO"),
    dict(opt_str="--freedev", callback=tcm_freevirtdev, nargs=1,
         dest="HBA/DEV", help="Free TCM Storage Object"),
    dict(opt_str="--listdevattr", callback=tcm_list_dev_attribs, nargs=1,
         dest="HBA/DEV", help="List TCM storage object device attributes"),
    dict(opt_str="--listhbas", callback=tcm_list_hbas, nargs=0,
         help="List TCM Host Bus Adapters (HBAs)"),
    dict(opt_str="--listlugps", callback=tcm_list_alua_lugps, nargs=0,
         help="List ALUA Logical Unit Groups"),
    dict(opt_str=("--listtgptgp","--listaluatpg"), callback=tcm_list_alua_tgptgp, nargs=2,
         dest="HBA/DEV <TG_PT_GP_NAME>",
         help="List specific ALUA Target Port Group for Storage Object"),
    dict(opt_str=("--listtgptgps","--listaluatpgs"), callback=tcm_list_alua_tgptgps, nargs=1,
         dest="HBA/DEV", help="List all ALUA Target Port Groups for Storage Object"),
    dict(opt_str="--lvsnapattrset", callback=tcm_snapshot_attr_set, nargs=2,
         dest="HBA/DEV ATTR=VALUE",
         help="Set LV snapshot configfs attributes for TCM/IBLOCK storage object"),
    dict(opt_str="--lvsnapattrshow", callback=tcm_snapshot_attr_show, nargs=1,
         dest="HBA/DEV",
         help="Show LV snapshot configfs attributes for TCM/IBLOCK storage object"),
    dict(opt_str="--lvsnapinit", callback=tcm_snapshot_init, nargs=4,
         dest="HBA/DEV MAX_SNAPSHOTS SNAP_SIZE_STR SNAP_INTERVAL_STR",
         help="Initialize snapshot with default attributes"),
    dict(opt_str="--lvsnapstart", callback=tcm_snapshot_start, nargs=1,
         dest="HBA/DEV", help="Enable snapshot daemon for TCM/IBLOCK LVM storage object"),
    dict(opt_str="--lvsnapstat", callback=tcm_snapshot_status, nargs=1,
         dest="HBA/DEV", help="Display LV snapshot status for TCM/IBLOCK LVM storage object"),
    dict(opt_str="--lvsnapstop", callback=tcm_snapshot_stop, nargs=1,
         dest="HBA/DEV", help="Disable snapshot daemon for TCM/IBLOCK LVM storage object"),
    dict(opt_str="--pr", callback=tcm_show_persistent_reserve_info, nargs=1,
         dest="HBA/DEV", help="Show Persistent Reservation info"),
    dict(opt_str="--praptpl", callback=tcm_process_aptpl_metadata, nargs=1,
         dest="HBA/DEV", help="Process PR APTPL metadata from file"),
    dict(opt_str="--prshowmd", callback=tcm_show_aptpl_metadata, nargs=1,
         dest="HBA/DEV", help="Show APTPL metadata file"),
    dict(opt_str="--ramdisk", callback=tcm_create_ramdisk, nargs=2,
         dest="HBA/DEV <PAGES>", help="Create and associate TCM/RAMDISK object"),
    dict(opt_str=("--scsi","--pscsi"), callback=tcm_create_pscsi, nargs=2,
         dest="HBA/DEV <C:T:L>",
         help="Associate TCM/pSCSI object with Linux/SCSI device by bus location"),
    dict(opt_str=("--scsibyudev", "--pscsibyudev"), callback=tcm_create_pscsibyudev, nargs=2,
         dest="HBA/DEV <UDEV_PATH>",
         help="Associate TCM/pSCSI object with Linux/SCSI device by UDEV Path"),
    dict(opt_str="--setaluadelay", callback=tcm_set_alua_nonop_delay, nargs=3,
         dest="HBA/DEV <TG_PT_GP_NAME> <NON_OP_DELAY_IN_MSECS>",
         help="Set ALUA Target Port Group delay for Active/NonOptimized in milliseconds"),
    dict(opt_str="--setaluapref", callback=tcm_set_alua_tgpt_pref, nargs=2,
         dest="HBA/DEV <TG_PT_GP_NAME>", help="Set ALUA Target Port Group Preferred Bit"),
    dict(opt_str="--setaluastate", callback=tcm_set_alua_state, nargs=3,
         dest="HBA/DEV <TG_PT_GP_NAME> <ALUA_ACCESS_STATE>",
         help="Set ALUA access state for TG_PT_GP_NAME on Storage Object.  The value access"
         " states are \"o\" = active/optimized, \"a\" = active/nonoptimized, \"s\" = standby,"
         " \"u\" = unavailable"),
    dict(opt_str="--setaluatransdelay", callback=tcm_set_alua_trans_delay, nargs=3,
         dest="HBA/DEV <TG_PT_GP_NAME> <TRANS_DELAY_IN_MSECS>",
         help="Set ALUA Target Port Group Transition delay"),
    dict(opt_str="--setaluatype", callback=tcm_set_alua_type, nargs=3,
         dest="HBA/DEV <TG_PT_GP_NAME> <ALUA_ACCESS_TYPE>",
         help="Set ALUA access type for TG_PT_GP_NAME on Storage Object.  The value type"
         " states are \"both\" = implict/explict, \"explict\", \"implict\", or \"none\""),
    dict(opt_str="--setdevattr", callback=tcm_set_dev_attrib, nargs=3,
         dest="HBA/DEV <ATTRIB> <VALUE>",
         help="Set new value for TCM storage object device attribute"),
    dict(opt_str="--setlugp", callback=tcm_set_alua_lugp, nargs=2,
         dest="HBA/DEV LU_GP_NAME", help="Set ALUA Logical Unit Group"),
    dict(opt_str="--setudevpath", callback=tcm_set_udev_path, nargs=2,
         dest="HBA/DEV <udev_path>",
         help="Set UDEV Path Information, only used when --createdev did not contain"
         " <udev_path> as parameter"),
    dict(opt_str="--setunitserial", callback=tcm_set_wwn_unit_serial, nargs=2,
         dest="HBA/DEV <unit_serial>", help="Set T10 EVPD Unit Serial Information"),
    dict(opt_str="--setunitserialwithmd", callback=tcm_set_wwn_unit_serial_with_md, nargs=2,
         dest="HBA/DEV <unit_serial>",
         help="Set T10 EVPD Unit Serial Information and process PR APTPL metadata"),
    dict(opt_str="--udevpath", callback=tcm_show_udev_path, nargs=1,
         dest="HBA/DEV", help="Show UDEV Path Information for TCM storage object"),
    dict(opt_str="--unload", callback=tcm_unload, nargs=0,
         help="Unload target_core_mod"),
    dict(opt_str="--version", callback=tcm_version, nargs=0,
         help="Display target_core_mod version information"),
    dict(opt_str="--wwn", callback=tcm_show_wwn_info, nargs=1,
         dest="HBA/DEV", help="Show WWN info"),
)

def main():

    parser = OptionParser()

    for opt in cmdline_options:
        # cmd_aliases can be string or tuple of strings.
        # we're unpacking below, so convert strings to 1 item tuples
        cmd_aliases = opt["opt_str"]
        if isinstance(cmd_aliases, basestring):
            cmd_aliases = (cmd_aliases,)
        del opt["opt_str"]
        # common params for all options
        opt["action"] = "callback"
        opt["type"] = "string"
        parser.add_option(*cmd_aliases, **opt)

    (options, args) = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    elif not re.search('--', sys.argv[1]):
        tcm_err("Unknown CLI option: " + sys.argv[1])
        
if __name__ == "__main__":
    main()
