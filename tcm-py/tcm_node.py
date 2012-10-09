#!/usr/bin/python

from __future__ import with_statement

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

tcm_root = "/sys/kernel/config/target/core"

def tcm_err(msg):
	print >> sys.stderr, msg
	sys.exit(1)

def tcm_read(filename):
	try:
		with open(filename) as f:
			return f.read()
	except IOError, (errno, strerror):
		if errno == 2:
			tcm_err("%s %s\n%s" % (filename, strerror, "Is kernel module loaded?") )

def tcm_write(filename, value, newline=True):
	try:
		with open(filename, "w") as f:
			f.write(value)
			if newline:
				f.write("\n")
	except IOError, (errno, strerror):
		if errno == 2:
			tcm_err("%s %s\n%s" % (filename, strerror, "Is kernel module loaded?") )

def tcm_full_path(arg):
	return tcm_root + "/" + arg

def tcm_check_dev_exists(dev_path):
	full_path = tcm_full_path(dev_path)
	if not os.path.isdir(full_path):
		tcm_err("TCM/ConfigFS storage object does not exist: " + full_path)

def tcm_add_alua_lugp(gp_name):
	os.makedirs(tcm_root + "/alua/lu_gps/" + gp_name)

	try:
		tcm_write(tcm_root + "/alua/lu_gps/%s/lu_gp_id" % lu_gp_name, lu_gp_name)
	except:
		os.rmdir(tcm_root + "/alua/lu_gps/" + lu_gp_name)
		raise

def tcm_add_alua_tgptgp(dev_path, gp_name):
	tcm_check_dev_exists(dev_path)

	alua_cfs_path = tcm_full_path(dev_path) + "alua/" + gp_name + "/"

	os.makedirs(alua_cfs_path)

	try:
		tcm_write(alua_cfs_path + "tg_pt_gp_id", "0")
	except:
		os.rmdir(alua_cfs_path)
		raise

def tcm_alua_check_metadata_dir(dev_path):
	alua_path = "/var/target/alua/tpgs_" + tcm_get_unit_serial(dev_path) + "/"
	if os.path.isdir(alua_path):
		return

	# Create the ALUA metadata directory for the passed storage object
	# if it does not already exist.
        os.makedirs(alua_path)

def tcm_alua_delete_metadata_dir(unit_serial):
	try:
		os.rmdir("/var/target/alua/tpgs_" + unit_serial + "/")
	except OSError:
		pass

def tcm_alua_process_metadata(dev_path, gp_name, gp_id):
	alua_gp_path = tcm_full_path(dev_path) + "/alua/" + gp_name
	alua_md_path = "/var/target/alua/tpgs_" + tcm_get_unit_serial(dev_path) \
	    + "/" + gp_name

	if not os.path.isfile(alua_md_path):
		# If not pre-existing ALUA metadata exists, go ahead and
		# allow new ALUA state changes to create and update the
		# struct file metadata
		tcm_write(alua_gp_path + "/alua_write_metadata", "1")
		return

	with open(alua_md_path, 'rU') as p:
		d = dict()
		for line in p.readlines():
			name, value = line.split("=")
			d[name.strip()] = value.strip()

	if "tg_pt_gp_id" in d and int(d["tg_pt_gp_id"]) != int(gp_id):
		raise IOError("Passed tg_pt_gp_id: %s does not match extracted: %s" % \
			(gp_id, d["tg_pt_gp_id"]))

	if "alua_access_state" in d:
		tcm_write(alua_gp_path + "/alua_access_state", d["alua_access_state"])

	if "alua_access_status" in d:
		tcm_write(alua_gp_path + "/alua_access_status", d["alua_access_status"])

	# Now allow changes to ALUA target port group update the struct file metadata
	# in /var/target/alua/tpgs_$T10_UNIT_SERIAL/$TG_PT_GP_NAME
	tcm_write(alua_gp_path + "/alua_write_metadata", "1")

def tcm_add_alua_tgptgp_with_md(dev_path, gp_name, gp_id):
	alua_gp_path = tcm_full_path(dev_path) + "/alua/" + gp_name

	tcm_check_dev_exists(dev_path)

	# If the default_tg_pt_gp is passed, we skip the creation (as it already exists)
	# and just process ALUA metadata
	if gp_name == 'default_tg_pt_gp' and gp_id == '0':
		tcm_alua_process_metadata(dev_path, gp_name, gp_id)
		return

	os.makedirs(alua_gp_path)

	try:
		tcm_write(alua_gp_path + "/tg_pt_gp_id",  gp_id)
	except:
		os.rmdir(alua_gp_path)
		raise

	# Now process the ALUA metadata for this group
	tcm_alua_process_metadata(dev_path, gp_name, gp_id)

def tcm_delhba(hba_name):
	hba_path = tcm_full_path(hba_name)

	for g in os.listdir(hba_path):
		if g == "hba_info" or g == "hba_mode":
			continue

		__tcm_freevirtdev(hba_name + "/" + g)

	os.rmdir(hba_path)

def tcm_del_alua_lugp(lu_gp_name):
	if not os.path.isdir(tcm_root + "/alua/lu_gps/" + lu_gp_name):
		tcm_err("ALUA Logical Unit Group: " + lu_gp_name + " does not exist!")

	os.rmdir(tcm_root + "/alua/lu_gps/" + lu_gp_name)

def __tcm_del_alua_tgptgp(dev_path, gp_name):
	tcm_check_dev_exists(dev_path)

	full_path = tcm_full_path(dev_path)

	if not os.path.isdir(full_path + "/alua/" + gp_name):
		tcm_err("ALUA Target Port Group: " + gp_name + " does not exist!")

	os.rmdir(full_path + "/alua/" + gp_name)

# deletes configfs entry for alua *and* metadata dir.
def tcm_del_alua_tgptgp(dev_path, gp_name):
	tcm_check_dev_exists(dev_path)

	alua_md_path = "/var/target/alua/tpgs_" + tcm_get_unit_serial(dev_path) \
	    + "/" + gp_name

	__tcm_del_alua_tgptgp(dev_path, gp_name)

	if not os.path.isfile(alua_md_path):
		return

	shutil.rmtree(alua_md_path)

def tcm_generate_uuid_for_unit_serial(dev_path):
	# Generate random uuid
	tcm_set_wwn_unit_serial(dev_path, str(uuid.uuid4()))

tcm_types = ( \
    dict(name="pscsi", module=tcm_pscsi, gen_uuid=False),
    dict(name="iblock", module=tcm_iblock, gen_uuid=True),
    dict(name="rd_dr", module=tcm_ramdisk, gen_uuid=True),
    dict(name="rd_mcp", module=tcm_ramdisk, gen_uuid=True),
    dict(name="fileio", module=tcm_fileio, gen_uuid=True),
)

def tcm_createvirtdev(dev_path, plugin_params, establishdev=False):
	hba_path = dev_path.split('/')[0]

	# create hba if it doesn't exist
	hba_full_path = tcm_full_path(hba_path)
	if not os.path.isdir(hba_full_path):
		os.mkdir(hba_full_path)

	# create dev if it doesn't exist
	full_path = tcm_full_path(dev_path)
	if os.path.isdir(full_path):
		tcm_err("TCM/ConfigFS storage object already exists: " + full_path)
	else:
		os.mkdir(full_path)

	# Determine if --establishdev is being called and we want to skip
	# the T10 Unit Serial Number generation
	gen_uuid = True
	if establishdev:
		gen_uuid = False

	# Calls into submodules depending on target_core_mod subsystem plugin
	for tcm in tcm_types:
		if hba_path.startswith(tcm["name"] + "_"):
			try:
				if tcm["module"]:
					# modules expect plugin_params to be a list, for now.
					tcm["module"].createvirtdev(dev_path, [plugin_params])
				else:
					tcm_err("no module for %s" % tcm["name"])
			except:
				os.rmdir(full_path)
				print "Unable to register TCM/ConfigFS storage object: " \
					+ full_path
				raise

			print tcm_read(full_path + "/info")

			if tcm["gen_uuid"] and gen_uuid:
        	                tcm_generate_uuid_for_unit_serial(dev_path)
				tcm_alua_check_metadata_dir(dev_path)
			break

def tcm_get_unit_serial(dev_path):
	string = tcm_read(tcm_full_path(dev_path) + "/wwn/vpd_unit_serial")
	return string.split(":")[1].strip()

def tcm_show_aptpl_metadata(dev_path):
	tcm_check_dev_exists(dev_path)

	aptpl_file = "/var/target/pr/aptpl_" + tcm_get_unit_serial(dev_path)
	if not os.path.isfile(aptpl_file):
		tcm_err("Unable to dump PR APTPL metadata file: " + aptpl_file)

	print tcm_read(aptpl_file)

def tcm_delete_aptpl_metadata(unit_serial):
	aptpl_file = "/var/target/pr/aptpl_" + unit_serial
	if not os.path.isfile(aptpl_file):
		return

	shutil.rmtree(aptpl_file)

def tcm_process_aptpl_metadata(dev_path):
	tcm_check_dev_exists(dev_path)

	full_path = tcm_full_path(dev_path)

	aptpl_file = "/var/target/pr/aptpl_" + tcm_get_unit_serial(dev_path)
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
		tcm_write(full_path + "/pr/res_aptpl_metadata", ",".join(res))

def tcm_establishvirtdev(dev_path, plugin_params):
	tcm_createvirtdev(dev_path, plugin_params, True)

def tcm_create_pscsi(dev_path, ctl):
	# convert passed 3-tuple to format pscsi expects
	# "1:3:5" -> "scsi_channel_id=1,scsi_target_id=3..."
	#
	param_names = ("scsi_channel_id", "scsi_target_id", "scsi_lun_id")

	pscsi_params = zip(param_names, ctl.split(":"))
	pscsi_params_str = ",".join([x + "=" + y for x, y in pscsi_params])

	tcm_createvirtdev(dev_path, pscsi_params_str)

def tcm_create_pscsibyudev(dev_path, udev_path):
	tcm_createvirtdev(cfs_dev, udev_path)

def tcm_create_iblock(dev_path, udev_path):
	tcm_createvirtdev(dev_path, udev_path)

def tcm_create_fileio(dev_path, filename, size):
	fileio_params = "fd_dev_name=" + filename + ",fd_dev_size=" + size
	tcm_createvirtdev(dev_path, fileio_params)

def tcm_create_ramdisk(dev_path, pages):
	tcm_createvirtdev(dev_path, pages)

def __tcm_freevirtdev(dev_path):
	tcm_check_dev_exists(dev_path)

	full_path = tcm_full_path(dev_path)

	for tg_pt_gp in os.listdir(full_path + "/alua/"):
		if tg_pt_gp == "default_tg_pt_gp":
			continue
		__tcm_del_alua_tgptgp(dev_path, tg_pt_gp)

	os.rmdir(full_path)

def tcm_freevirtdev(dev_path):
	tcm_check_dev_exists(dev_path)

	unit_serial = tcm_get_unit_serial(dev_path)

	__tcm_freevirtdev(dev_path)
	# For explict tcm_node --freedev, delete any remaining
	# PR APTPL and ALUA metadata
	tcm_delete_aptpl_metadata(unit_serial)
	tcm_alua_delete_metadata_dir(unit_serial)

def tcm_list_dev_attribs(dev_path):
	tcm_check_dev_exists(dev_path)

	full_path = tcm_full_path(dev_path)

	print "TCM Storage Object Attributes for " + full_path
	for attrib in os.listdir(full_path + "/attrib/"):
		print "       %s: %s" % \
		    (attrib, tcm_read(full_path + "/attrib/" + attrib).strip())

def tcm_list_hbas():
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

def tcm_list_alua_lugps():
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

def tcm_list_alua_tgptgp(dev_path, gp_name):
	tcm_check_dev_exists(dev_path)

	gp_path = tcm_full_path(dev_path) + "/alua/" + gp_name
	
	gp_id = tcm_read(gp_path + "/tg_pt_gp_id").strip()
	print "\------> " + tg_pt_gp + "  Target Port Group ID: " + tg_pt_gp_id

	alua_type = tcm_read(gp_path + "/alua_access_type").strip()
	print "         Active ALUA Access Type(s): " + alua_type

	alua_state = tcm_read(gp_path + "/alua_access_state").strip()
	print "         Primary Access State: " + tcm_dump_alua_state(alua_state)

	try:
		access_status = tcm_read(gp_path + "/alua_access_status").strip()
		print "         Primary Access Status: " + access_status
	except IOError:
		pass

	preferred = tcm_read(gp_path + "/preferred").strip()
	print "         Preferred Bit: " + preferred

	nonop_delay = tcm_read(gp_path + "/nonop_delay_msecs").strip()
	print "         Active/NonOptimized Delay in milliseconds: " + nonop_delay

	trans_delay = tcm_read(gp_path + "/trans_delay_msecs").strip()
	print "         Transition Delay in milliseconds: " + trans_delay

	gp_members = tcm_read(gp_path + "/members").strip().split()

	print "         \------> TG Port Group Members"
	if not gp_members:
		print "             No Target Port Group Members"
	else:
		for member in gp_members:
			print "         " + member

def tcm_list_alua_tgptgps(dev_path):
	tcm_check_dev_exists(dev_path)

	for tg_pt_gp in os.listdir(tcm_full_path(dev_path) + "/alua/"):
		tcm_list_alua_tgptgp(dev_path, tg_pt_gp)

def tcm_show_persistent_reserve_info(dev_path):
	tcm_check_dev_exists(dev_path)

	full_path = tcm_full_path(dev_path)

	for f in os.listdir(full_path + "/pr/"):
		info = tcm_read(full_path + "/pr/" + f).strip()
		if info:
			print info

def tcm_set_alua_state(dev_path, gp_name, access_state):
	tcm_check_dev_exists(dev_path)

	new_alua_state_str = str(access_state).lower()

	if new_alua_state_str == "o":
		alua_state = 0 # Active/Optimized
	elif new_alua_state_str == "a":
		alua_state = 1 # Active/NonOptimized
	elif new_alua_state_str == "s":
		alua_state = 2 # Standby
	elif new_alua_state_str == "u":
		alua_state = 3 # Unavailable
	else:
		tcm_err("Unknown ALUA access state: " + new_alua_state_str)

	alua_path = tcm_full_path(dev_path) + "/alua/" + gp_name + "/alua_access_state"
	tcm_write(alua_path, str(alua_state))

def tcm_set_alua_type(dev_path, gp_name, access_type):
	tcm_check_dev_exists(dev_path)

	new_alua_type_str = str(access_type).lower()

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

	alua_path = tcm_full_path(dev_path) + "/alua/" + gp_name + "/alua_access_type"
	tcm_write(alua_path, str(alua_type))

def tcm_set_alua_nonop_delay(dev_path, gp_name, msec_delay):
	tcm_check_dev_exists(dev_path)

	if not os.path.isdir(tcm_full_path(dev_path) + "/alua/" + gp_name):
		tcm_err("Unable to locate TG Pt Group: " + gp_name)

	alua_path = tcm_full_path(dev_path) + "/alua/" + gp_name + "/nonop_delay_msecs"
	tcm_write(alua_path, str(msec_delay))

def tcm_set_alua_trans_delay(dev_path, gp_name, msec_delay):
	tcm_check_dev_exists(dev_path)

	if not os.path.isdir(tcm_full_path(dev_path) + "/alua/" + gp_name):
		tcm_err("Unable to locate TG Pt Group: " + gp_name)

	alua_path = tcm_full_path(dev_path) + "/alua/" + gp_name + "/trans_delay_msecs"
	tcm_write(alua_path, str(msec_delay))

def tcm_clear_alua_tgpt_pref(dev_path, gp_name):
	tcm_check_dev_exists(dev_path)

	if not os.path.isdir(tcm_full_path(dev_path) + "/alua/" + gp_name):
		tcm_err("Unable to locate TG Pt Group: " + gp_name)

	alua_path = tcm_full_path(dev_path) + "/alua/" + gp_name + "/preferred"
	tcm_write(alua_path, "0")

def tcm_set_alua_tgpt_pref(dev_path, gp_name):
	tcm_check_dev_exists(dev_path)

	if not os.path.isdir(tcm_full_path(dev_path) + "/alua/" + gp_name):
		tcm_err("Unable to locate TG Pt Group: " + gp_name)

	alua_path = tcm_full_path(dev_path) + "/alua/" + gp_name + "/preferred"
	tcm_write(alua_path, "1")

def tcm_set_alua_lugp(dev_path, gp_name):
	tcm_check_dev_exists(dev_path)

	if not os.path.isdir(tcm_full_path(dev_path) + "/alua/lu_gps/" + gp_name):
		tcm_err("Unable to locate ALUA Logical Unit Group: " + gp_name)

	alua_path = tcm_full_path(dev_path) + "/alua/lu_gps/" + gp_name + "/alua_lu_gp"
	tcm_write(alua_path, gp_name)

def tcm_set_dev_attrib(dev_path, attrib, value):
	tcm_check_dev_exists(dev_path)

	tcm_write(tcm_full_path(dev_path) + "/attrib/" + attrib, value)

def tcm_set_udev_path(dev_path, udev_path):
	tcm_check_dev_exists(dev_path)

	tcm_write(tcm_full_path(dev_path) + "/udev_path", udev_path, newline=False)

def tcm_set_wwn_unit_serial(dev_path, unit_serial):
	tcm_check_dev_exists(dev_path)

	tcm_write(tcm_full_path(dev_path) + "/wwn/vpd_unit_serial", unit_serial)

def tcm_set_wwn_unit_serial_with_md(dev_path, unit_serial):
	tcm_check_dev_exists(dev_path)

	tcm_set_wwn_unit_serial(dev_path, unit_serial)
	# Process PR APTPL metadata
	tcm_process_aptpl_metadata(dev_path)
	# Make sure the ALUA metadata directory exists for this storage object
	tcm_alua_check_metadata_dir(dev_path)

def tcm_show_udev_path(dev_path):
	tcm_check_dev_exists(dev_path)

	print tcm_read(tcm_full_path(dev_path) + "/udev_path")

def tcm_show_wwn_info(dev_path):
	tcm_check_dev_exists(dev_path)

	full_path = tcm_full_path(dev_path) + "/wwn/"

	for f in os.listdir(full_path):
		info = tcm_read(full_path + f).strip()
		if info:
			print info

def tcm_unload_modules(mod):
	p = sub.Popen(["lsmod"], stdout=sub.PIPE)
	o = p.communicate()[0]
	for l in o.splitlines():
		m = l.split()
		if m[0] == mod:
			if len(m) > 3:
				for d in m[3].split(","):
					tcm_unload_modules(d)
			rmmod_op = "rmmod " + mod
			ret = os.system(rmmod_op)
			if ret:
				tcm_err("Unable to " + rmmod_op)
	return

def tcm_unload():
	if not os.path.isdir(tcm_root):
		tcm_err("Unable to access tcm_root: " + tcm_root)

	hba_root = os.listdir(tcm_root)

	for f in hba_root:
		if f == "alua":
			continue

		tcm_delhba(f)

	for lu_gp in os.listdir(tcm_root + "/alua/lu_gps"):
		if lu_gp == "default_lu_gp":
			continue

		tcm_del_alua_lugp(lu_gp)

	# Unload TCM subsystem plugin modules + TCM core
	tcm_unload_modules("target_core_mod")

def tcm_version():
	return tcm_read("/sys/kernel/config/target/version").strip()

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
    dict(opt_str="--wwn", callback=tcm_show_wwn_info, nargs=1,
         dest="HBA/DEV", help="Show WWN info"),
)

def dispatcher(option, opt_str, value, parser, orig_callback):
	if option.nargs == 1:
		value = (value,)
	value = [str(x).strip() for x in value]
	orig_callback(*value)

def main():

    parser = OptionParser(version=tcm_version())

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
        opt["callback_kwargs"] = dict(orig_callback=opt["callback"])
        opt["callback"] = dispatcher
        parser.add_option(*cmd_aliases, **opt)

    (options, args) = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    elif not re.search('--', sys.argv[1]):
        tcm_err("Unknown CLI option: " + sys.argv[1])
        
if __name__ == "__main__":
    main()
