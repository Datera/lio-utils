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

def tcm_write(filename, value):
	f = open(tcm_root + "/" + filename, "w")
	f.write(value + "\n")
	f.close()

def tcm_get_cfs_prefix(arg):
	return tcm_root + "/" + arg

def tcm_add_alua_lugp(option, opt_str, value, parser):
	lu_gp_name = str(value)

	os.makedirs(tcm_root + "/alua/lu_gps/" + lu_gp_name)

	try:
		tcm_write("alua/lu_gps/%s/lu_gp_id" % lu_gp_name, lu_gp_name)
	except:
		os.rmdir(tcm_root + "/alua/lu_gps/" + lu_gp_name)
		raise

def tcm_add_alua_tgptgp(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	tg_pt_gp_name = str(value[1])
	alua_cfs_path = cfs_dev_path + "/alua/" + tg_pt_gp_name

	if os.path.isdir(cfs_dev_path + "/alua/" + tg_pt_gp_name):
		tcm_err("ALUA Target Port Group: " + tg_pt_gp_name + " already exists!")

	mkdir_op = "mkdir -p " + cfs_dev_path + "/alua/" + tg_pt_gp_name
	ret = os.system(mkdir_op)
	if ret:
		tcm_err("Unable to create ALUA Target Port Group: " + tg_pt_gp_name)

	set_tg_pt_gp_op = "echo 0 > " + cfs_dev_path + "/alua/" + tg_pt_gp_name + "/tg_pt_gp_id"
	ret = os.system(set_tg_pt_gp_op)
	if ret:
		rmdir_op = "rmdir " + cfs_dev_path + "/alua/" + tg_pt_gp_name
		os.system(rmdir_op)
		tcm_err("Unable to set ID for ALUA Target Port Group: " + tg_pt_gp_name)
	else:
		tcm_alua_set_write_metadata(alua_cfs_path)
		print "Successfully created ALUA Target Port Group: " + tg_pt_gp_name

def tcm_alua_check_metadata_dir(cfs_dev_path):

	unit_serial = tcm_get_unit_serial(cfs_dev_path)
	alua_path = "/var/target/alua/tpgs_" + unit_serial + "/"
	if os.path.isdir(alua_path) == True:
		return

	# Create the ALUA metadata directory for the passed storage object
	# if it does not already exist.
	mkdir_op = "mkdir -p " + alua_path
	ret = os.system(mkdir_op)
	if ret:
		tcm_err("Unable to create ALUA metadata directory: " + alua_path)

def tcm_alua_delete_metadata_dir(unit_serial):

	alua_path = "/var/target/alua/tpgs_" + unit_serial + "/"
	if os.path.isdir(alua_path) == False:
		return

	rm_op = "rm -rf " + alua_path
	ret = os.system(rm_op)
	if ret:
		tcm_err("Unable to remove ALUA metadata directory: " + alua_path)

def tcm_alua_set_write_metadata(alua_cfs_path):
	alua_write_md_file = alua_cfs_path + "/alua_write_metadata"

	p = open(alua_write_md_file, 'w')
	if not p:
		tcm_err("Unable to open: " + alua_write_md_file)
	
	ret = p.write("1")
	if ret:
		tcm_err("Unable to enable writeable ALUA metadata for " + alua_write_md_file)
	
	p.close()

def tcm_alua_process_metadata(cfs_dev_path, tg_pt_gp_name, tg_pt_gp_id):
	alua_cfs_path = cfs_dev_path + "/alua/" + tg_pt_gp_name
	
	unit_serial = tcm_get_unit_serial(cfs_dev_path)
	alua_path = "/var/target/alua/tpgs_" + unit_serial + "/" + tg_pt_gp_name
#	print "Using tg_pt_gp alua_path " + alua_path

	if os.path.isfile(alua_path) == False:
		# If not pre-existing ALUA metadata exists, go ahead and
		# allow new ALUA state changes to create and update the
		# struct file metadata
		tcm_alua_set_write_metadata(alua_cfs_path)
		return

	p = open(alua_path, 'rU')
	if not p:
		print "Unable to process ALUA metadata for: " + alua_path

	line = p.readline()
	while line:
		buf = line.rstrip()
		
		if re.search('tg_pt_gp_id=', buf):
			ex_tg_pt_gp_id = buf[12:]
#			print "Extracted tg_pt_gp_id: " + ex_tg_pt_gp_id

			if int(ex_tg_pt_gp_id) != int(tg_pt_gp_id):
				tcm_err("Passed tg_pt_gp_id: " + tg_pt_gp_id + " does not match extracted: " + ex_tg_pt_gp_id)

		elif re.search('alua_access_state=', buf):
			alua_access_state = buf[21:]
#			print "Extracted alua_access_state: " + alua_access_state
			cfs = open(alua_cfs_path + "/alua_access_state", 'w')
			if not cfs:
				tcm_err("Unable to open " + alua_cfs_path + "/alua_access_state")

			ret = cfs.write(alua_access_state)
			if ret:
				tcm_err("Unable to set: " + alua_cfs_path + "/alua_access_state")

			cfs.close()

		elif re.search('alua_access_status=', buf):
			alua_access_status = buf[22:]
#			print "Extracted alua_access_status " + alua_access_status
			cfs = open(alua_cfs_path + "/alua_access_status", 'w')
			if not cfs:
				tcm_err("Unable to open " + alua_cfs_path + "/alua_access_status")
	
			ret = cfs.write(alua_access_status)
			if ret:
				tcm_err("Unable to set: " + alua_cfs_path + "/alua_access_status")

			cfs.close()

		line = p.readline()

	# Now allow changes to ALUA target port group update the struct file metadata
	# in /var/target/alua/tpgs_$T10_UNIT_SERIAL/$TG_PT_GP_NAME
	tcm_alua_set_write_metadata(alua_cfs_path)
	p.close()

def tcm_add_alua_tgptgp_with_md(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	tg_pt_gp_name = str(value[1])
	tg_pt_gp_id = str(value[2])

	# If the default_tg_pt_gp is passed, we skip the creation (as it already exists)
	# and just process ALUA metadata
	if tg_pt_gp_name == 'default_tg_pt_gp' and tg_pt_gp_id == '0':
		tcm_alua_process_metadata(cfs_dev_path, tg_pt_gp_name, tg_pt_gp_id)
		return

	if os.path.isdir(cfs_dev_path + "/alua/" + tg_pt_gp_name):
		tcm_err("ALUA Target Port Group: " + tg_pt_gp_name + " already exists!")

	mkdir_op = "mkdir -p " + cfs_dev_path + "/alua/" + tg_pt_gp_name
	ret = os.system(mkdir_op)
	if ret:
		tcm_err("Unable to add existing ALUA Target Port Group: " + tg_pt_gp_name)

	set_tg_pt_gp_op = "echo " + tg_pt_gp_id + " > " + cfs_dev_path + "/alua/" + tg_pt_gp_name + "/tg_pt_gp_id"
	ret = os.system(set_tg_pt_gp_op)
	if ret:
		rmdir_op = "rmdir " + cfs_dev_path + "/alua/" + tg_pt_gp_name
		os.system(rmdir_op)
		tcm_err("Unable to set ID for ALUA Target Port Group: " + tg_pt_gp_name)
	else:
		print "Successfully added existing ALUA Target Port Group: " + tg_pt_gp_name + " with tg_pt_gp_id: " + tg_pt_gp_id

	# Now process the ALUA metadata for this group
	tcm_alua_process_metadata(cfs_dev_path, tg_pt_gp_name, tg_pt_gp_id)

def tcm_delhba(option, opt_str, value, parser):
	hba_name = str(value)

	hba_path = tcm_root + "/" + hba_name
	print "hba_path: " + hba_path

	dev_root = tcm_root + "/" + hba_name + "/"
	for g in os.listdir(dev_root):
		if g == "hba_info" or g == "hba_mode":
			continue;

		tmp_str = hba_name + "/"+ g
		__tcm_freevirtdev(None, None, tmp_str, None)

	ret = os.rmdir(hba_path)
	if ret:
		tcm_err("Unable to delete TCM HBA: " + hba_path)
	else:
		print "Successfully released TCM HBA: " + hba_path

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

def __tcm_del_alua_tgptgp(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	tg_pt_gp_name = str(value[1])
	if not os.path.isdir(cfs_dev_path + "/alua/" + tg_pt_gp_name):
		tcm_err("ALUA Target Port Group: " + tg_pt_gp_name + " does not exist!")

	rmdir_op = "rmdir " + cfs_dev_path + "/alua/" + tg_pt_gp_name
	ret = os.system(rmdir_op)
	if ret:
		tcm_err("Unable to delete ALUA Target Port Group: " + tg_pt_gp_name)
	else:
		print "Successfully deleted ALUA Target Port Group: " + tg_pt_gp_name

def tcm_del_alua_tgptgp(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	unit_serial = tcm_get_unit_serial(cfs_dev_path)
	tg_pt_gp_name = str(value[1])
	alua_md_path = "/var/target/alua/tpgs_" + unit_serial + "/" + tg_pt_gp_name

	__tcm_del_alua_tgptgp(option, opt_str, value, parser)

	if os.path.isfile(alua_md_path) == False:
		return
	
	rm_op = "rm -rf " + alua_md_path
	ret = os.system(rm_op)
	if ret:
		tcm_err("Unable to remove ALUA metadata from: " + alua_md_path)

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

	plugin_params = str(value[1]).split(' ')
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
		ret = tcm_pscsi.createvirtdev(cfs_path, plugin_params)
	result = re.search('stgt_', hba_cfs)
	if result:
		print "stgt"
	result = re.search('iblock_', hba_cfs)
	if result:
		ret = tcm_iblock.createvirtdev(cfs_path, plugin_params)
	result = re.search('rd_dr_', hba_cfs)
	if result:
		ret = tcm_ramdisk.createvirtdev(cfs_path, plugin_params)
	result = re.search('rd_mcp_', hba_cfs)
	if result:
		ret = tcm_ramdisk.createvirtdev(cfs_path, plugin_params)
	result = re.search('fileio_', hba_cfs)
	if result:
		ret = tcm_fileio.createvirtdev(cfs_path, plugin_params)

	if not ret:
		info_op = "cat " + cfs_dev_path + "/info"
		ret = os.system(info_op)
		if ret:
			os.rmdir(cfs_dev_path)
			tcm_err("Unable to access " + cfs_dev_path + "/info for TCM storage object")

		if gen_uuid:
                        tcm_generate_uuid_for_unit_serial(cfs_path)
			tcm_alua_check_metadata_dir(cfs_dev_path)
		
		print "Successfully created TCM/ConfigFS storage object: " + cfs_dev_path
	else:
		os.rmdir(cfs_dev_path);
		tcm_err("Unable to register TCM/ConfigFS storage object: " + cfs_dev_path)

def tcm_get_unit_serial(cfs_dev_path):

	unit_serial_file = cfs_dev_path + "/wwn/vpd_unit_serial"
	p = open(unit_serial_file, 'rU')
	if not p:
		tcm_err("Unable to open unit_serial_file: " + unit_serial_file)

	tmp = p.read()
	p.close()
	off = tmp.index('Number: ')
	off += 8 # Skip over "Number: "
	unit_serial = tmp[off:]
	return unit_serial.rstrip()

def tcm_show_aptpl_metadata(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_path = cfs_unsplit.split('/')
	hba_cfs = cfs_path[0]
	dev_vfs_alias = cfs_path[1]

	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	unit_serial = tcm_get_unit_serial(cfs_dev_path)
	aptpl_file = "/var/target/pr/aptpl_" + unit_serial
	if (os.path.isfile(aptpl_file) == False):
		tcm_err("Unable to dump PR APTPL metadata file: " + aptpl_file);
	
	os.system("cat " + aptpl_file)

def tcm_delete_aptpl_metadata(unit_serial):

	aptpl_file = "/var/target/pr/aptpl_" + unit_serial
	if (os.path.isfile(aptpl_file) == False):
		return

	rm_op = "rm -rf " + aptpl_file
	ret = os.system(rm_op)
	if ret:
		tcm_err("Unable to delete PR APTPL metadata: " + aptpl_file)

def tcm_process_aptpl_metadata(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_path = cfs_unsplit.split('/')
	hba_cfs = cfs_path[0]
	dev_vfs_alias = cfs_path[1]

	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	unit_serial = tcm_get_unit_serial(cfs_dev_path)
	aptpl_file = "/var/target/pr/aptpl_" + unit_serial
	if (os.path.isfile(aptpl_file) == False):
		return

	print "Reading APTPL metadata from: " + aptpl_file

	p = open(aptpl_file, 'rU')
	if not p:
		tcm_err("Unable to open aptpl_file: " + aptpl_file)
	
	start = 1
	out = ""

	line = p.readline()
	if re.search('No Registrations or Reservations', line):
		p.close()
		return

	if not re.search('PR_REG_START:', line):
		p.close()
		tcm_err("Unable to find PR_REG_START key in: " + aptpl_file);


	cfs_aptpl_file = cfs_dev_path + "/pr/res_aptpl_metadata"

	while line:
		if start == 1:
			if not re.search('PR_REG_START:', line):
				p.close()
				return

			start = 0
			out = ""
			line = p.readline()
			continue;
		
		if not re.search('PR_REG_END:', line):
			out += line.rstrip()
			out += ","
			line = p.readline()
			continue

		out = out[:-1]

		cfs = open(cfs_aptpl_file, 'w')
		if not cfs:
			p.close()
			tcm_err("Unable to open cfs_aptpl_file: " + cfs_aptpl_file)

		val = cfs.write(out)
		if val:
			print "Failed to write PR APTPL metadata to: " + cfs_aptpl_file
			
		cfs.close()
#		print "Write out to configfs: " + out
		out = ""
		start = 1
		line = p.readline()

	p.close()

def tcm_establishvirtdev(option, opt_str, value, parser):
	cfs_dev = str(value[0])
	plugin_params = str(value[1])

	vals = [cfs_dev, plugin_params, 1]
	tcm_createvirtdev(None, None, vals, None)

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

def __tcm_freevirtdev(option, opt_str, value, parser):
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

	if os.path.isdir(cfs_dev_path + "/alua/") == True:
		for tg_pt_gp in os.listdir(cfs_dev_path + "/alua/"):
			if tg_pt_gp == "default_tg_pt_gp":
				continue

			vals = [value, tg_pt_gp]
			__tcm_del_alua_tgptgp(None, None, vals, None)

	ret = os.rmdir(cfs_dev_path)
	if not ret:
		print "Successfully released TCM/ConfigFS storage object: " + cfs_dev_path
	else:
		tcm_err("Failed to release ConfigFS Storage Object: " + cfs_dev_path + " ret: " + ret)

def tcm_freevirtdev(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	unit_serial = tcm_get_unit_serial(cfs_dev_path)

	__tcm_freevirtdev(option, opt_str, value, parser)
	# For explict tcm_node --freedev, delete any remaining
	# PR APTPL and ALUA metadata
	tcm_delete_aptpl_metadata(unit_serial)
	tcm_alua_delete_metadata_dir(unit_serial)

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
			if dev == "hba_info" or dev == "hba_mode":
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
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	tg_pt_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + tg_pt_gp
	
	if (os.path.isdir(tg_pt_gp_base) == False):
		tcm_err("Unable to access tg_pt_gp_base: " + tg_pt_gp_base)

	p = os.open(tg_pt_gp_base + "/tg_pt_gp_id", 0)
	value = os.read(p, 8)
	tg_pt_gp_id = value.rstrip()
	os.close(p)
	print "\------> " + tg_pt_gp + "  Target Port Group ID: " + tg_pt_gp_id

	p = os.open(tg_pt_gp_base + "/alua_access_type", 0)
	value = os.read(p, 32)
	alua_type = value.rstrip()
	os.close(p)
	print "         Active ALUA Access Type(s): " + alua_type

	p = os.open(tg_pt_gp_base + "/alua_access_state", 0)
	value = os.read(p, 8)
	alua_state = tcm_dump_alua_state(value.rstrip())
	os.close(p)
	print "         Primary Access State: " + alua_state

	if (os.path.isfile(tg_pt_gp_base + "/alua_access_status") == True):
		p = os.open(tg_pt_gp_base + "/alua_access_status", 0)
		value = os.read(p, 32)
		os.close(p)
		print "         Primary Access Status: " + value.rstrip()

	p = os.open(tg_pt_gp_base + "/preferred", 0)
	value = os.read(p, 8)
	os.close(p)
	print "         Preferred Bit: " + value.rstrip()

	p = os.open(tg_pt_gp_base + "/nonop_delay_msecs", 0)
	value = os.read(p, 8)
	os.close(p)
	print "         Active/NonOptimized Delay in milliseconds: " + value.rstrip()

	p = os.open(tg_pt_gp_base + "/trans_delay_msecs", 0)
	value = os.read(p, 8)
	os.close(p)
	print "         Transition Delay in milliseconds: " + value.rstrip()

	p = os.open(tg_pt_gp_base + "/members", 0)
	value = os.read(p, 4096)
	tg_pt_gp_members = value.split('\n');
	os.close(p)

	print "         \------> TG Port Group Members"
	if len(tg_pt_gp_members) == 1:
		print "             No Target Port Group Members"
		return

	i = 0
	while i < len(tg_pt_gp_members) - 1:
		print "             " + tg_pt_gp_members[i]
		i += 1

def tcm_list_alua_tgptgps(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	for tg_pt_gp in os.listdir(cfs_dev_path + "/alua/"):
		vals = [str(value), tg_pt_gp]
		tcm_list_alua_tgptgp(None, None, vals, None)

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
	
	p = open(cfs_dev_path + "/snap/" + attr, 'w')
	val = p.write(value)
	if val:
		p.close()
		tcm_err("Unable to write to snap_attr: " + cfs_dev_path + "/snap/" + attr)

	p.close()
	print "Successfully updated snapshot attribute: " + attr + "=" + value + " for " + cfs_dev_path

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
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	pr_show_op = "cat " + cfs_dev_path + "/pr/*"
	ret = os.system(pr_show_op)
	if ret:
		tcm_err("Unable to disable storage object persistent reservation info")

def tcm_set_alua_state(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	alua_gp = str(value[1])
	new_alua_state_str = str(value[2])
	new_alua_state_str = new_alua_state_str.lower()
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	alua_state = 0;

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

	set_alua_state_op = "echo " + str(alua_state) + " > " + tg_pt_gp_base + "/alua_access_state"
	ret = os.system(set_alua_state_op)
	if ret:
		tcm_err("Unable to set primary ALUA access state for TG PT Group: " + tg_pt_gp_base)
	else:
		print "Successfully set primary ALUA access state for TG PT Group: " + alua_gp + " to " + tcm_dump_alua_state(str(alua_state))

def tcm_set_alua_type(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	alua_gp = str(value[1])
	new_alua_type_str = str(value[2])
	new_alua_type_str = new_alua_type_str.lower()
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	alua_type = 0

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

	set_alua_type_op = "echo " + str(alua_type) + " > " + tg_pt_gp_base + "/alua_access_type"
	ret = os.system(set_alua_type_op)
	if ret:
		tcm_err("Unable to set ALUA access type for TG PT Group: " + tg_pt_gp_base)
	else:
		print "Successfully set ALUA access type for TG PT Group: " + alua_gp + " to " + new_alua_type_str

def tcm_set_alua_nonop_delay(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if (os.path.isdir(tg_pt_gp_base) == False):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	delay_msecs = str(value[2])

	set_nonop_delay_msecs_op = "echo " + delay_msecs + " > " + tg_pt_gp_base + "/nonop_delay_msecs"
	ret = os.system(set_nonop_delay_msecs_op)
	if ret:
		tcm_err("Unable to set ALUA Active/NonOptimized Delay for TG PT Group: " + tg_pt_gp_base)
	else:
		print "Successfully set ALUA Active/NonOptimized Delay to " + delay_msecs + " milliseconds for TG PT Group: " + tg_pt_gp_base

def tcm_set_alua_trans_delay(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if (os.path.isdir(tg_pt_gp_base) == False):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	delay_msecs = str(value[2])

	set_trans_delay_msecs_op = "echo " + delay_msecs + " > " + tg_pt_gp_base + "/trans_delay_msecs"
	ret = os.system(set_trans_delay_msecs_op)
	if ret:
		tcm_err("Unable to set ALUA Transition Delay for TG PT Group: " + tg_pt_gp_base)
	else:
		print "Successfully set ALUA Transition Delay to " + delay_msecs + " milliseconds for TG PT Group: " + tg_pt_gp_base

def tcm_clear_alua_tgpt_pref(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if (os.path.isdir(tg_pt_gp_base) == False):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	set_tg_pt_gp_pref_op = "echo 0 > " + tg_pt_gp_base + "/preferred"
	ret = os.system(set_tg_pt_gp_pref_op)
	if ret:
		tcm_err("Unable to disable PREFERRED bit for TG Pt Group: " + alua_gp)
	else:
		print "Successfully disabled PREFERRED bit for TG Pt Group: " + alua_gp

def tcm_set_alua_tgpt_pref(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	alua_gp = str(value[1])
	tg_pt_gp_base = cfs_dev_path + "/alua/" + alua_gp
	if (os.path.isdir(tg_pt_gp_base) == False):
		tcm_err("Unable to locate TG Pt Group: " + alua_gp)

	set_tg_pt_gp_pref_op = "echo 1 > " + tg_pt_gp_base + "/preferred"
	ret = os.system(set_tg_pt_gp_pref_op)
	if ret:
		tcm_err("Unable to enable PREFERRED bit for TG Pt Group: " + alua_gp)
	else:
		print "Successfully enabled PREFERRED bit for TG Pt Group: " + alua_gp

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

def tcm_set_wwn_unit_serial(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	wwn_set_op = "echo " + value[1] + " > " + cfs_dev_path + "/wwn/vpd_unit_serial"
	ret = os.system(wwn_set_op)
	if ret:
		tcm_err("Unable to set T10 WWN Unit Serial for " + cfs_dev_path)

	print "Set T10 WWN Unit Serial for " + cfs_unsplit + " to: " + value[1]

def tcm_set_wwn_unit_serial_with_md(option, opt_str, value, parser):
	cfs_unsplit = str(value[0])
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	tcm_set_wwn_unit_serial(None, None, value, None);
	# Process PR APTPL metadata
	tcm_process_aptpl_metadata(None, None, cfs_unsplit, None)
	# Make sure the ALUA metadata directory exists for this storage object
	tcm_alua_check_metadata_dir(cfs_dev_path)

def tcm_show_udev_path(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	udev_path_show_op = "cat " + cfs_dev_path + "/udev_path"
	ret = os.system(udev_path_show_op)
	if ret:
		tcm_err("Unable to show UDEV path for " + cfs_dev_path)

def tcm_show_wwn_info(option, opt_str, value, parser):
	cfs_unsplit = str(value)
	cfs_dev_path = tcm_get_cfs_prefix(cfs_unsplit)
	if (os.path.isdir(cfs_dev_path) == False):
		tcm_err("TCM/ConfigFS storage object does not exist: " + cfs_dev_path)

	wwn_show_op = "cat " + cfs_dev_path + "/wwn/*"
	ret = os.system(wwn_show_op)
	if ret:
		tcm_err("Unable to disable storage object WWN info")

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
	os.system("cat /sys/kernel/config/target/version")

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
