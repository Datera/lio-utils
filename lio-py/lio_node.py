#!/usr/bin/python
import os, sys
import subprocess as sub
import string
import re
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"
lio_root = "/sys/kernel/config/target/iscsi"
alua_secondary_md_dir = "/var/target/alua/iSCSI/"

def lio_err(msg):
	print msg
	sys.exit(1)

def lio_alua_check_secondary_md(iqn, tpgt):
	alua_sec_md_path = alua_secondary_md_dir + iqn + "+" + tpgt + "/"
	if os.path.isdir(alua_sec_md_path) == False:
		mkdir_op = "mkdir -p " + alua_sec_md_path	
		ret = os.system(mkdir_op)
		if ret:
			lio_err("Unable to create secondary ALUA MD directory: " + alua_sec_md_path)

	return

def lio_alua_delete_secondary_md(iqn, tpgt):
	alua_sec_md_path = alua_secondary_md_dir + iqn + "+" + tpgt + "/" 
	if os.path.isdir(alua_sec_md_path) == False:
		return

	rm_op = "rm -rf " + alua_sec_md_path
	ret = os.system(rm_op)
	if ret:
		lio_err("Unable to remove secondary ALUA MD directory: " + alua_sec_md_path)

	return

def lio_alua_delete_secondary_md_port(iqn, tpgt, lun):

	alua_sec_md_file = alua_secondary_md_dir + iqn + "+" + tpgt + "/lun_" + lun
	if os.path.isfile(alua_sec_md_file) == False:
		return

	rm_op = "rm -rf "+ alua_sec_md_file
	ret = os.system(rm_op)
	if ret:
		lio_err("Unable to delete ALUA secondary metadata file: " + alua_sec_md_file)

	return

def lio_alua_set_secondary_write_md(iqn, tpgt, lun):
	alua_write_md_file = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun + "/alua_tg_pt_write_md"
	if os.path.isfile(alua_write_md_file) == False:
		return

	p = open(alua_write_md_file, 'w')
	if not p:
		lio_err("Unable to open: " + alua_write_md_file)

	ret = p.write("1")
	if ret:
		lio_err("Unable to enable writeable ALUA secondary metadata for " + alua_write_md_file)

	p.close()
	return

def lio_alua_process_secondary_md(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);

	alua_sec_md_file = alua_secondary_md_dir + iqn + "+" + tpgt + "/lun_" + lun
	if os.path.isfile(alua_sec_md_file) == False:
		# Use --aluasecmd as a chance to make sure the directory for this
		# LIO-Target endpoint (iqn+tpgt) exists..
		lio_alua_check_secondary_md(iqn, tpgt)
		lio_alua_set_secondary_write_md(iqn, tpgt, lun)
		lio_err("Unable to locate ALUA secondary metadata file: " + alua_sec_md_file)
		return

#	print "Using alua_sec_md_file: " + alua_sec_md_file
	alua_sec_cfs_path = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
#	print "Using alua_sec_cfs_path: " + alua_sec_cfs_path

	p = open(alua_sec_md_file, 'rU')
	if not p:
		print "Unable to process ALUA secondary metadata for: " + alua_sec_md_file

	line = p.readline()
	while line:
		buf = line.rstrip()

		if re.search('alua_tg_pt_offline=', buf):
			alua_tg_pt_offline = buf[19:]
#			print "Extracted alua_tg_pt_offline: " + alua_tg_pt_offline
			cfs = open(alua_sec_cfs_path + "/alua_tg_pt_offline", 'w')
			if not cfs:
				p.close()
				lio_err("Unable to open " + alua_sec_cfs_path + "/alua_tg_pt_offline")

			ret = cfs.write(alua_tg_pt_offline)
			cfs.close()
			if ret:
				p.close()
				lio_err("Unable to write " + alua_sec_cfs_path + "/alua_tg_pt_offline")

		elif re.search('alua_tg_pt_status=', buf):
			alua_tg_pt_status = buf[18:]
#			print "Extracted alua_tg_pt_status: " + alua_tg_pt_status
			cfs = open(alua_sec_cfs_path + "/alua_tg_pt_status", 'w')
			if not cfs:
				p.close()
				lio_err("Unable to open " + alua_sec_cfs_path + "/alua_tg_pt_status")
			
			ret = cfs.write(alua_tg_pt_status)
			cfs.close()
			if ret:
				p.close()
				lio_err("Unable to write " + alua_sec_cfs_path + "/alua_tg_pt_status")

		line = p.readline()

	p.close()
	# Now enable the alua_tg_pt_write_md bit to allow for new updates
	# to ALUA secondary metadata in struct file for this port
	lio_alua_set_secondary_write_md(iqn, tpgt, lun)
	return

def __lio_target_del_iqn(option, opt_str, value, parser, delete_tpg_md):
	iqn = str(value);
	iqn = iqn.lower();

# Loop through LIO-Target IQN+TPGT list
	tpg_root = os.listdir(lio_root + "/" + iqn); 
	for tpgt_tmp in tpg_root:
		if tpgt_tmp == "fabric_statistics":
			continue

		tpgt_tmp2 = tpgt_tmp.split('_')
		tpgt = tpgt_tmp2[1]

		tpg_val = [iqn,tpgt]
		if delete_tpg_md == 1:
			lio_target_del_tpg(None, None, tpg_val, None)   
		else:
			__lio_target_del_tpg(None, None, tpg_val, None, 0)

	rmdir_op = "rmdir " + lio_root + "/" + iqn
#	print "rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op)
	if not ret:
		print "Successfully released iSCSI Target Endpoint IQN: " + iqn
	else:
		lio_err("Unable to release iSCSI Target Endpoint IQN: " + iqn)

	return

def lio_target_del_iqn(option, opt_str, value, parser):
	iqn = str(value);
	iqn = iqn.lower();

	iqn_dir = lio_root + "/" + iqn
	if os.path.isdir(iqn_dir) == False:
		lio_err("Unable to locate iSCSI Target IQN: " + iqn_dir)

	# Passing 1 for delete_tpg_md here means lio_target_del_tpg()
	# with lio_alua_delete_secondary_md() will get called to delete
	# all of the secondary ALUA directories for the LIO-Target endpoint
	# when an explict --deliqn is called.
	__lio_target_del_iqn(option, opt_str, value, parser, 1)

	return

def __lio_target_del_tpg(option, opt_str, value, parser, delete_tpg_md):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	# This will set TPG Status to INACTIVE force all of the iSCSI sessions for this
	# tiqn+tpgt tuple to be released.
	disable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/enable"
	ret = os.system(disable_op)
	if ret:
		print "Unable to disable TPG: " + iqn + " TPGT: " + tpgt

	np_root = os.listdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np")
	for np in np_root:
		np_val = [iqn,tpgt,np]

		lio_target_del_np(None, None, np_val, None)

	nacl_root = os.listdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls")
	for nacl in nacl_root:
		nacl_val = [iqn,tpgt,nacl]

		lio_target_del_nodeacl(None, None, nacl_val, None)

	lun_root = os.listdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun")
	for lun_tmp in lun_root:
		lun_tmp2 = lun_tmp.split('_')
		lun = lun_tmp2[1]

		lun_val = [iqn,tpgt,lun]
		if delete_tpg_md == 1:
			lio_target_del_port(None, None, lun_val, None)
		else:
			__lio_target_del_port(None, None, lun_val, None)


	rmdir_op = "rmdir " + lio_root + "/" + iqn + "/tpgt_" + tpgt
#	print "rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op)
	if not ret:
		print "Successfully released iSCSI Target Portal Group: " + iqn + " TPGT: " + tpgt
	else:
		lio_err("Unable to release iSCSI Target Portal Group: " + iqn + " TPGT: " + tpgt)
	
	return

def lio_target_del_tpg(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	tpgt_file = lio_root + "/" + iqn + "/tpgt_" + tpgt
	if os.path.isdir(tpgt_file) == False:
		lio_err("iSCSI Target Port Group: " + tpgt_file + " does not exist")
	
	__lio_target_del_tpg(option, opt_str, value, parser, 1)
	# Delete the ALUA secondary metadata directory on explict --deltpg or
	# called from --deliqn
	lio_alua_delete_secondary_md(iqn, tpgt)
	return

def lio_target_add_np(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	np = str(value[2]);

	# Append default iSCSI Port is non is given.
	if re.search(']', np)and not re.search(']:', np):
		np = np + ":3260"
	elif re.search(':\\Z', np):
		np = np + "3260"
	elif not re.search(':', np):
		np = np + ":3260"

	# Extract the iSCSI port and make sure it is a valid u16 value
	if re.search(']:', np):
		off = np.index(']:')
		off += 2 
		port = int(np[off:])
	else:
		off = np.index(':')
		off += 1
		port = int(np[off:])

	if port == 0 or port > 65535:
		lio_err("Illegal port value: " + str(port) + " for iSCSI network portal")

	mkdir_op = "mkdir -p " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np/" + np
#	print "mkdir_op: " + mkdir_op
	ret = os.system(mkdir_op)
	if not ret:
		print "Successfully created network portal: " + np + " created " + iqn + " TPGT: " + tpgt 
		lio_alua_check_secondary_md(iqn, tpgt)
	else:
		lio_err("Unable to create network portal: " + np + " created " + iqn + " TPGT: " + tpgt)

	return

def lio_target_del_np(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	np = str(value[2]);

	path = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np/" + np

	path_iser = path + "/iser"
	if os.path.isfile(path_iser):
		fd = open(path_iser, 'r')
		s = fd.read()
		set_iser_attr = s.strip()
		fd.close()
		if set_iser_attr == "1":
			fd = open(path_iser, 'w')
			fd.write("0")
			fd.close()

	rmdir_op = "rmdir " + path
#	print "rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op)
	if not ret:
		print "Successfully released network portal: " + np + " created " + iqn + " TPGT: " + tpgt
	else:
		lio_err("Unable to release network portal: " + np + " created " + iqn + " TPGT: " + tpgt)

	return

def lio_target_add_port(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);
	port_name = str(value[3]);
	tcm_obj = str(value[4]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	if os.path.isdir(lun_dir):
		lio_err("iSCSI Target Logical Unit ConfigFS directory already exists")

	mkdir_op = "mkdir -p " + lun_dir
#	print "mkdir_op: " + mkdir_op
	ret = os.system(mkdir_op)
	if ret:
		lio_err("Unable to create iSCSI Target Logical Unit ConfigFS directory")

	port_src = tcm_root + "/" + tcm_obj
	port_dst = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun + "/" + port_name
	link_op = "ln -s " + port_src + " " + port_dst
#	print "link_op: " + link_op
	ret = os.system(link_op)
	if not ret:
		print "Successfully created iSCSI Target Logical Unit"
		lio_alua_check_secondary_md(iqn, tpgt)
		lio_alua_set_secondary_write_md(iqn, tpgt, lun)
	else:
		os.rmdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun)
		lio_err("Unable to create iSCSI Target Logical Unit symlink")

	return

def lio_target_add_tpg(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	tpg_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt
	if os.path.isdir(tpg_dir):
		lio_err("iSCSI Target Portal Group directory already exists")

	mkdir_op = "mkdir -p " + tpg_dir
	ret = os.system(mkdir_op)
	if ret:
		lio_err("Unable to create iSCSI Target Portal Group ConfigFS directory")
	else:
		print "Successfully created iSCSI Target Portal Group"
		lio_alua_check_secondary_md(iqn, tpgt)

	return

def __lio_target_del_port(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	port_root = os.listdir(lun_dir)

	for port in port_root:
		if port == "alua_tg_pt_gp":
			continue
		if port == "alua_tg_pt_offline":
			continue
		if port == "alua_tg_pt_status":
			continue
		if port == "alua_tg_pt_write_md":
			continue

		if not os.path.islink(lun_dir + "/" + port):
			continue

		unlink_op = lun_dir + "/" + port
#		print "del_portunlink_op: " + unlink_op
		ret = os.unlink(unlink_op)
		if ret:
			lio_err("Unable to unlink iSCSI Target Logical Unit")

	rmdir_op= "rmdir " + lun_dir
#	print "del_port rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op);
	if not ret:
		print "Successfully deleted iSCSI Target Logical Unit"
	else:
		lio_err("Unable to rmdir iSCSI Target Logical Unit configfs directory")

	return

def lio_target_del_port(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	if os.path.isdir(lun_dir) == False:
		lio_err("LIO-Target Port/LUN directory: " + lun_dir + " does not exist")

	__lio_target_del_port(option, opt_str, value, parser)
	# Delete the ALUA secondary metadata file for this Port/LUN
	# during an explict --dellun
	lio_alua_delete_secondary_md_port(iqn, tpgt, lun)

	return

def lio_target_tpg_disableauth(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	
	enable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/authentication"
	ret = os.system(enable_op)
	if ret:
		lio_err("Unable to disable iSCSI Authentication on iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully disabled iSCSI Authentication on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_tpg_demomode(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	enable_op = "echo 1 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/generate_node_acls"
	ret = os.system(enable_op)
	if ret:
		lio_err("Unable to disable Initiator ACL mode (Enable DemoMode) on iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully disabled Initiator ACL mode (Enabled DemoMode) on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_disable_lunwp(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	mapped_lun = str(value[3]);

	disable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun + "/write_protect"
	ret = os.system(disable_op)
	if ret:
		lio_err("Unable to disable WriteProtect for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully disabled WRITE PROTECT for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_enable_auth(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	enable_op = "echo 1 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/authentication"
	ret = os.system(enable_op)
	if ret:
		lio_err("Unable to enable iSCSI Authentication on iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully enabled iSCSI Authentication on iSCSI Target Portal Group: " + iqn + " " + tpgt
	return

def lio_target_enable_lunwp(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	mapped_lun = str(value[3]);

	enable_op = "echo 1 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun + "/write_protect"
	ret = os.system(enable_op)
	if ret:
		lio_err("Unable to enable WriteProtect for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully enabled WRITE PROTECT for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_enable_tpg(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	enable_op = "echo 1 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/enable"
	ret = os.system(enable_op)
	if ret:
		lio_err("Unable to enable iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully enabled iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_disable_tpg(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	disable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/enable"
	ret = os.system(disable_op)
	if ret:
		lio_err("Unable to disable iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully disabled iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_enableaclmode(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	enable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/generate_node_acls"
	ret = os.system(enable_op)
	if ret:
		lio_err("Unable to enable Initiator ACL mode (Disabled DemoMode) on iSCSI Target Portal Group: " + iqn + " " + tpgt)
        else:
                print "Successfully enabled Initiator ACL mode (Disabled DemoMode) on iSCSI Target Portal Group: " + iqn + " " + tpgt
        return


def lio_target_add_lunacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	tpg_lun = str(value[3]);
	mapped_lun = str(value[4]);

	mkdir_op = "mkdir -p " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun
	ret = os.system(mkdir_op)
	if ret:
		lio_err("Unable to add iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)

	addlunacl_op = "ln -s " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + tpg_lun + " " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun + "/lio_lun"

	ret = os.system(addlunacl_op)
	if ret:
		lio_err("Unable to add iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully added iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
		lio_alua_check_secondary_md(iqn, tpgt)

	return

def lio_target_del_lunacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	mapped_lun = str(value[3]);

	lun_link_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun
	for lun_acl_link in os.listdir(lun_link_dir):
		if lun_acl_link == "write_protect":
			continue

		if not os.path.islink(lun_link_dir + "/" + lun_acl_link):
			continue;

		unlink_op = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun + "/" + lun_acl_link
#		print "unlink_op: " + unlink_op
		ret = os.unlink(unlink_op)
		if ret:
			lio_err("Unable to unlink iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
		
	dellunacl_op = "rmdir " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun
	ret = os.system(dellunacl_op)
	if ret:
		lio_err("Unable to delete iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully deleted iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_add_nodeacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	
	addnodeacl_op = "mkdir -p " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn
	ret = os.system(addnodeacl_op)
	if ret:
		lio_err("Unable to add iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully added iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
		lio_alua_check_secondary_md(iqn, tpgt)

	return

def lio_target_del_nodeacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();

	nacl_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn
	lun_acl_root = os.listdir(nacl_dir)
	for lun_acl in lun_acl_root:
		ret = re.search('lun_', lun_acl)
		if not ret:
			continue
		lun_delacl_val = [iqn,tpgt,initiator_iqn,lun_acl[4:]]
		lio_target_del_lunacl(None, None, lun_delacl_val, None)

	delnodeacl_op = "rmdir " + nacl_dir
	ret = os.system(delnodeacl_op)
	if ret:
		lio_err("Unable to delete iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully deleted iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_set_chap_auth(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	user = str(value[3]);
	password = str(value[4]);

	auth_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/auth/"

	if not os.path.isdir(auth_dir):
		lio_err("iSCSI Initiator ACL " + initiator_iqn + " does not exist for iSCSI Target Portal Group: " + iqn + " " + tpgt)

	setuser_op = "echo -n " + user + " > " + auth_dir + "/userid"
	ret = os.system(setuser_op)	
	if ret:
		lio_err("Unable to set CHAP username for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)

	setpassword_op = "echo -n " + password + " > " + auth_dir + "/password"
	ret = os.system(setpassword_op)
	if ret:
		lio_err("Unable to set CHAP password for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully set CHAP authentication for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_set_chap_mutual_auth(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	user_mutual = str(value[3]);
	password_mutual = str(value[4]);

	auth_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/auth/"

	if not os.path.isdir(auth_dir):
		lio_err("iSCSI Initiator ACL " + initiator_iqn + " does not exist for iSCSI Target Portal Group: " + iqn + " " + tpgt)

	setuser_op = "echo -n " + user_mutual + " > " + auth_dir + "/userid_mutual"
	ret = os.system(setuser_op)
	if ret:
		lio_err("Unable to set mutual CHAP username for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)

	setpassword_op = "echo -n " + password_mutual + " > " + auth_dir + "/password_mutual"
	ret = os.system(setpassword_op)
	if ret:
		lio_err("Unable to set mutual CHAP password for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully set mutual CHAP authentication for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt	
	
	return

def lio_target_set_chap_discovery_auth(option, opt_str, value, parser):
	user = str(value[0]);
	password = str(value[1]);

        auth_dir = lio_root + "/discovery_auth"
        if not os.path.isdir(auth_dir):
                lio_err("iSCSI Discovery Authentication directory " + auth_dir + " does not exist")

        setuser_op = "echo -n " + user + " > " + auth_dir + "/userid"
        ret = os.system(setuser_op)
        if ret:
		lio_err("Unable to set CHAP username for iSCSI  Discovery Authentication")

        setpassword_op = "echo -n " + password + " > " + auth_dir + "/password"
        ret = os.system(setpassword_op)
        if ret:
                lio_err("Unable to set CHAP password for iSCSI Discovery Authentication")
        else:
                print "Successfully set CHAP authentication for iSCSI Discovery Authentication"

	return

def lio_target_set_chap_mutual_discovery_auth(option, opt_str, value, parser):
	user_mutual = str(value[0]);
	password_mutual = str(value[1]);

	auth_dir = lio_root + "/discovery_auth"
	if not os.path.isdir(auth_dir):
		lio_err("iSCSI Discovery Authentication directory " + auth_dir + " does not exist")

	setuser_op = "echo -n " + user_mutual + " > " + auth_dir + "/userid_mutual"
	ret = os.system(setuser_op)
	if ret:
		lio_err("Unable to set mutual CHAP username for iSCSI Discovery Authentication")

	setpassword_op = "echo -n " + password_mutual + " > " + auth_dir + "/password_mutual"
	ret = os.system(setpassword_op)
	if ret:
		lio_err("Unable to set mutual CHAP password for iSCSI Discovery Authentication")
	else:
		print "Successfully set mutual CHAP authentication for iSCSI Discovery Authentication"

	return

def lio_target_set_enforce_discovery_auth(option, opt_str, value, parser):
	value = str(value);
	
	da_attr = lio_root + "/discovery_auth/enforce_discovery_auth"
	if not os.path.isfile(da_attr):
		lio_err("iSCSI Discovery Authentication directory does not exist")
	
	da_op = "echo " + value + " > " + da_attr;
	ret = os.system(da_op)
	if ret:
		lio_err("Unable to set da_attr: " + da_attr)

	if value == "1":
		print "Successfully enabled iSCSI Discovery Authentication enforcement"
	else:
		print "Successfully disabled iSCSI Discovery Authentication enforcement"

	return


def lio_target_set_node_tcq(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();
	depth = str(value[3]);

	setnodetcq_op = "echo " + depth + " > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/cmdsn_depth"
	ret = os.system(setnodetcq_op)
	if ret:
		lio_err("Unable to set TCQ: " + depth + " for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt)
	else:
		print "Successfully set TCQ: " + depth + " for iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_alua_set_tgptgp(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);
	tg_pt_gp_name = str(value[3])

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	if not os.path.isdir(lun_dir):
		lio_err("LIO-Target Port/LUN: " + lun + " does not exist on: " + iqn + " " + tpgt)

	set_tp_pt_gp_op = "echo " + tg_pt_gp_name + " > " + lun_dir + "/alua_tg_pt_gp"
	ret = os.system(set_tp_pt_gp_op)
	if ret:
		lio_err("Unable to set ALUA Target Port Group: " + tg_pt_gp_name + " for LUN: " + lun + " on " + iqn + " " + tpgt)
	else:
		print "Successfully set ALUA Target Port Group: " + tg_pt_gp_name + " for LUN: " + lun + " on " + iqn + " " + tpgt

	return

def lio_target_alua_set_tgpt_offline(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	if not os.path.isdir(lun_dir):
		lio_err("LIO-Target Port/LUN: " + lun + " does not exist on: " + iqn + " " + tpgt)

	set_tg_pt_gp_offline_op = "echo 1 > " + lun_dir + "/alua_tg_pt_offline"
	ret = os.system(set_tg_pt_gp_offline_op)
	if ret:
		lio_err("Unable to set ALUA secondary state OFFLINE bit for LUN: " + lun + " on " + iqn + " " + tpgt)
	else:
		print "Successfully set ALUA secondary state OFFLINE for LUN: " + lun + " on " + iqn + " " + tpgt

	return

def lio_target_alua_clear_tgpt_offline(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	if not os.path.isdir(lun_dir):
		lio_err("LIO-Target Port/LUN: " + lun + " does not exist on: " + iqn + " " + tpgt)

	set_tg_pt_gp_offline_op = "echo 0 > " + lun_dir + "/alua_tg_pt_offline"
	ret = os.system(set_tg_pt_gp_offline_op)
	if ret:
		lio_err("Unable to clear ALUA secondary state OFFLINE for LUN: " + lun + " on " + iqn + " " + tpgt)
	else:
		print "Successfully cleared ALUA secondary state OFFLINE for LUN: " + lun + " on " + iqn + " " + tpgt
	return

def lio_target_show_chap_auth(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();

	auth_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/auth/"

	if not os.path.isdir(auth_dir):
		lio_err("iSCSI Initiator ACL " + initiator_iqn + " does not exist for iSCSI Target Portal Group: " + iqn + " " + tpgt)

	for auth in os.listdir(auth_dir):
		p = os.open(auth_dir + "/" + auth, 0)
		value = os.read(p, 256)
		print auth + ": " + value.rstrip()
		os.close(p)	

	return

def lio_target_show_chap_discovery_auth(option, opt_str, value, parser):

	auth_dir = lio_root + "/discovery_auth"
	if not os.path.isdir(auth_dir):
		lio_err("iSCSI Discovery Authentication directory " + auth_dir + " does not exist")

	for auth in os.listdir(auth_dir):
		p = os.open(auth_dir + "/" + auth, 0)
		value = os.read(p, 256)
		print auth + ": " + value.rstrip()
		os.close(p)

	return

def lio_target_show_node_tcq(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	initiator_iqn = initiator_iqn.lower();

	nacl = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn
	if not os.path.isdir(nacl):
		lio_err("iSCSI Initiator ACL: " + initiator_iqn + " does not exist for iSCSI Target Portal Group: " + iqn + " " + tpgt)

	tcq_depth_file = nacl + "/cmdsn_depth"
	p = os.open(tcq_depth_file, 0)
	value = os.read(p, 8)
	print value.rstrip()
	os.close(p)

	return

def lio_target_alua_show_tgptgp(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	lun = str(value[2]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	if not os.path.isdir(lun_dir):
		lio_err("LIO-Target Port/LUN: " + lun + " does not exist on: " + iqn + " " + tpgt)

	show_tp_pt_gp_op = "cat " + lun_dir + "/alua_tg_pt_gp"
	ret = os.system(show_tp_pt_gp_op)
	if ret:
		lio_err("Unable to show ALUA Target Port Group: " + tg_pt_gp_name + " for LUN: " + lun + " on " + iqn + " " + tpgt)

	return

def lio_target_list_endpoints(option, opt_str, value, parser):

	iqn_root = os.listdir(lio_root)
	
	for iqn in iqn_root:
		if iqn == "lio_version":
			continue
		if iqn == "discovery_auth":
			continue

		print "\------> " + iqn

		tpg_root = lio_root + "/" + iqn
		for tpg in os.listdir(tpg_root):
			if tpg == "fabric_statistics":
				continue

			p = os.open(tpg_root + "/" + tpg + "/param/TargetAlias", 0)
			value = os.read(p, 256)
			print "        \-------> " + tpg + "  TargetAlias: " + value.rstrip()
			os.close(p)

			print "         TPG Status:",
			p = os.open(tpg_root + "/" + tpg + "/enable", 0)
			value = os.read(p, 8)
			enable_bit = value.rstrip();
			if enable_bit == '1':
				print "ENABLED"
			else:
				print "DISABLED"
			os.close(p)

			print "         TPG Network Portals:"
			np_root = tpg_root + "/" + tpg + "/np"
			for np in os.listdir(np_root):
				print "                 \-------> " + np

			print "         TPG Logical Units:"
			lun_root = tpg_root + "/" + tpg + "/lun"
			for lun in os.listdir(lun_root):
				port_dir = lun_root + "/" + lun
				for port in os.listdir(port_dir):
					if port == "alua_tg_pt_gp":
						continue
					if port == "alua_tg_pt_offline":
						continue
					if port == "alua_tg_pt_status":
						continue
					if port == "alua_tg_pt_write_md":
						continue
					if port == "statistics":
						continue
					
					port_link = port_dir + "/" + port
					if not os.path.islink(port_link):
						continue

					sourcelink = os.readlink(port_link)
					# Skip over ../../../../../ in sourcelink"		
					print "                 \-------> " + lun + "/" + port + " -> " + sourcelink[18:]
					

	return

def lio_target_list_lunacls(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	iqn_root = os.listdir(lio_root)

	nacl_root_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls"
	nacl_root = os.listdir(nacl_root_dir)
	for nacl in nacl_root:
		print "\------> InitiatorName ACL: " + nacl
		print "         Logical Unit ACLs: "
		lun_root_dir = nacl_root_dir + "/" + nacl
		lun_root = os.listdir(lun_root_dir)
		for lun in lun_root:
			ret = re.search('lun_', lun)
			if not ret:
				continue

			wp_attrib = lun_root_dir + "/" + lun + "/write_protect"
			wp_file = open(wp_attrib);
			line = wp_file.readline()
			wp_bit = line.rstrip()
			if wp_bit == '1':
				wp_info = "ENABLED"
			else:
				wp_info = "DISABLED"
			
			lun_link_dir = lun_root_dir + "/" + lun
			for lun_link in os.listdir(lun_link_dir):
				if lun_link == "write_protect":
					continue
				if lun_link == "statistics":
					continue

				if not os.path.islink(lun_link_dir + "/" + lun_link):
					continue
				
				sourcelink = os.readlink(lun_link_dir + "/" + lun_link)
				# Skip over ../../../../../../ in sourcelink"
				print "         \-------> " + lun + " -> " + sourcelink[21:]
				print "                   \-------> Write Protect for " + lun + ": " + wp_info

	return

def lio_target_list_nodeacls(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	iqn_root = os.listdir(lio_root)
	
	nacl_root_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls"
	nacl_root = os.listdir(nacl_root_dir)
	for nacl in nacl_root:
		print "\------> InitiatorName: " + nacl
		info_attrib = nacl_root_dir + "/" + nacl + "/info"
		file = open(info_attrib, "r")
		line = file.readline()
		ret = re.search('No active iSCSI Session for Initiator Endpoint', line)
		if ret:	
			print "         No active iSCSI Session for Initiator Endpoint"
		else:	
			line = file.readline()
			while line:
				print "         " + line.rstrip()
				line = file.readline()

		file.close()
		
	return

def lio_target_list_nps(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	np_root = os.listdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np")
	for np in np_root:
		print np

	return

def lio_target_list_targetnames(option, opt_str, value, parser):
	
	iqn_root = os.listdir(lio_root)
	
	# Loop through LIO-Target IQN list
	for iqn in iqn_root:
		if iqn == "lio_version":
			continue
		if iqn == "discovery_auth":
			continue

		print iqn	

	return

def lio_target_list_node_attr(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2])

	attr_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/attrib/"
	if os.path.isdir(attr_dir) == False:
		lio_err("Unable to locate node attr_dir: " + attr_dir)

	for attr in os.listdir(attr_dir):
		p = open(attr_dir + "/" + attr, 'rU')
		if not p:
			lio_err("Unable to open attr: " + attr_dir + "/" + attr)

		val = p.read()
		p.close()

		print attr + "=" + val.rstrip()
	
	return

def lio_target_set_node_attr(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2])
	attr = str(value[3])
	val = str(value[4])

	attr_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/attrib/"
	if os.path.isdir(attr_dir) == False:
		lio_err("Unable to locate node attr_dir: " + attr_dir)

	p = open(attr_dir + "/" + attr, 'w')
	if not p:
		lio_err("Unable to open node attr: " + attr_dir + "/" + attr)

	ret = p.write(val)
	if ret:
		lio_err("Unable to set node attr: " + attr_dir + "/" + attr)

	p.close()
	print "Successfully set Initiator Node attribute: " + attr + " to: " + val

	return

def lio_target_list_node_param(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	initiator_iqn = str(value[2])

	param_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/param"
	if os.path.isdir(param_dir) == False:
		lio_err("Unable to locate node param_dir: " + param_dir)

	for param in os.listdir(param_dir):
		p = open(param_dir + "/" + param, 'rU')
		if not p:
			lio_err("Unable to open attr: " + param_dir + "/" + param)

		val = p.read()
		p.close()

		print param + "=" + val.rstrip()

	return


def lio_target_list_tpg_attr(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	attr_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib"
	if os.path.isdir(attr_dir) == False:
		lio_err("Unable to locate tpg attr_dir: " + attr_dir)

	for attr in os.listdir(attr_dir):
		p = open(attr_dir + "/" + attr, 'rU')
		if not p:
			lio_err("Unable to open attr: " + attr_dir + "/" + attr)

		val = p.read()
		p.close()

		print attr + "=" + val.rstrip()

	return

def lio_target_set_tpg_attr(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	attr = str(value[2]);
	val = str(value[3]);

	attr_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib"
	if os.path.isdir(attr_dir) == False:
		lio_err("Unable to locate tpg attr_dir: " + attr_dir)

	p = open(attr_dir + "/" + attr, 'w')
	if not p:
		lio_err("Unable to open tpg attr: " + attr_dir + "/" + attr)

	ret = p.write(val)
	if ret:
		lio_err("Unable to set tpg attr: " + attr_dir + "/" + attr)

	p.close()
	print "Successfully set TPG attribute: " + attr + " to: " + val

	return

def lio_target_list_tpg_param(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);

	param_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/param"
	if os.path.isdir(param_dir) == False:
		lio_err("Unable to locate tpg param dir: " + param_dir)

	for param in os.listdir(param_dir):
		p = open(param_dir + "/" + param, 'rU')
		if not p:
			lio_err("Unable to open param: " + param_dir + "/" + param)

		val = p.read()
		p.close()

		print param + "=" + val.rstrip()

	return

def lio_target_set_tpg_param(option, opt_str, value, parser):
	iqn = str(value[0]);
	iqn = iqn.lower();
	tpgt = str(value[1]);
	param = str(value[2]);
	val = str(value[3]);

	param_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/param"
	if os.path.isdir(param_dir) == False:
		lio_err("Unable to locate tpg param dir: " + param_dir)

	p = open(param_dir + "/" + param, 'w')
	if not p:
		lio_err("Unable to open tpg attr: " + param_dir + "/" + param)

	val = val + " "
	ret = p.write(val)
	if ret:
		lio_err("Unable to write tpg attr: " + param_dir + "/" + param)

	p.close()
	print "Successfully set TPG parameter: " + param + " to: " + val

	return

def lio_target_unload(option, opt_str, value, parser):

	iqn_root = ""
	if os.path.isdir(lio_root):
		iqn_root = os.listdir(lio_root)

	# Loop through LIO-Target IQN list
	for iqn in iqn_root:
		if iqn == "lio_version":
			continue
		if iqn == "discovery_auth":
			continue

		# Loop through LIO-Target IQN+TPGT list
		tpg_root = os.listdir(lio_root + "/" + iqn);
		for tpgt_tmp in tpg_root:
			if tpgt_tmp == "fabric_statistics": 
				continue

			tpgt_tmp2 = tpgt_tmp.split('_')
			tpgt = tpgt_tmp2[1]

			tpg_val = [iqn,tpgt]
			__lio_target_del_tpg(None, None, tpg_val, None, 0)	

		__lio_target_del_iqn(None, None, iqn, None, 0)


	if iqn_root:
		rmdir_op = "rmdir " + lio_root
		ret = os.system(rmdir_op)
		if ret:
			print "Unable to remove lio_root: " + lio_root

	fd = open("/proc/modules", 'r')
	buf = fd.read()
	fd.close()
	if re.search('ib_isert', buf):
	        rmmod_op = "rmmod ib_isert"
	        ret = os.system(rmmod_op)
	        if ret:
	                print "Unable to unload ib_isert"

	rmmod_op = "rmmod iscsi_target_mod"
	ret = os.system(rmmod_op)
	if ret:
		print "Unable to unload iscsi_target_mod"

	return

def lio_target_version(option, opt_str, value, parser):

	os.system("cat /sys/kernel/config/target/iscsi/lio_version")
	return

def main():

	parser = OptionParser()
	parser.add_option("--addlunacl", action="callback", callback=lio_target_add_lunacl, nargs=5,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN TPG_LUN MAPPED_LUN", help="Add iSCSI Initiator LUN ACL to LIO-Target Portal Group LUN")
	parser.add_option("--addnodeacl", action="callback", callback=lio_target_add_nodeacl, nargs=3,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="Add iSCSI Initiator ACL to LIO-Target Portal Group")
	parser.add_option("--addnp", action="callback", callback=lio_target_add_np, nargs=3,
		type="string", dest="TARGET_IQN TPGT IP:PORT", help="Add LIO-Target IPv6 or IPv4 network portal")
	parser.add_option("--addlun", action="callback", callback=lio_target_add_port, nargs=5,
		type="string", dest="TARGET_IQN TPGT LUN PORT_ALIAS TCM_HBA/DEV ", help="Create LIO-Target Logical Unit")
	parser.add_option("--addtpg", action="callback", callback=lio_target_add_tpg, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Create LIO-Target portal group")
	parser.add_option("--aluasecmd", action="callback", callback=lio_alua_process_secondary_md, nargs=3,
		type="string", dest="TARGET_IQN TPGT LUN", help="Process ALUA secondary metadata for Port/LUN");
        parser.add_option("--cleartgptoff","--clearaluaoff", action="callback", callback=lio_target_alua_clear_tgpt_offline, nargs=3,
                type="string", dest="TARGET_IQN TPGT LUN", help="Clear ALUA Target Port Secondary State OFFLINE")
	parser.add_option("--dellunacl", action="callback", callback=lio_target_del_lunacl, nargs=4,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN MAPPED_LUN", help="Delete iSCSI Initiator LUN ACL from LIO-Target Portal Group LUN")
	parser.add_option("--delnodeacl", action="callback", callback=lio_target_del_nodeacl, nargs=3,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="Delete iSCSI Initiator ACL from LIO-Target Portal Group")
	parser.add_option("--delnp", action="callback", callback=lio_target_del_np, nargs=3,
		type="string", dest="TARGET_IQN TPGT IP:PORT", help="Delete LIO-Target IPv6 or IPv4 network portal")
	parser.add_option("--deliqn", action="callback", callback=lio_target_del_iqn, nargs=1,
		type="string", dest="TARGET_IQN", help="Delete LIO-Target IQN Endpoint")
	parser.add_option("--dellun",  action="callback", callback=lio_target_del_port, nargs=3,
		type="string", dest="TARGET_IQN TPGT LUN", help="Delete LIO-Target Logical Unit")
	parser.add_option("--deltpg", action="callback", callback=lio_target_del_tpg, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Delete LIO-Target Portal Group")
	parser.add_option("--demomode", "--permissive", action="callback", callback=lio_target_tpg_demomode, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Disable all iSCSI Initiator ACL requirements (enable DemoMode) for LIO-Target Portal Group (Disabled by default)")
	parser.add_option("--disableauth", action="callback", callback=lio_target_tpg_disableauth, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Disable iSCSI Authentication for LIO-Target Portal Group (Enabled by default)")
	parser.add_option("--disablelunwp", action="callback", callback=lio_target_disable_lunwp, nargs=4,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN MAPPED_LUN", help="Clear Write Protect bit for iSCSI Initiator LUN ACL")
	parser.add_option("--disabletpg", action="callback", callback=lio_target_disable_tpg, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Disable LIO-Target Portal Group")
	parser.add_option("--enableaclmode", action="callback", callback=lio_target_enableaclmode, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Enable iSCSI Initiator ACL requirement mode for LIO-Target Portal Group (Enabled by default)")
	parser.add_option("--enableauth", action="callback", callback=lio_target_enable_auth, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Enable iSCSI Authentication for LIO-Target Portal Group (Enabled by default)")
	parser.add_option("--enablelunwp", action="callback", callback=lio_target_enable_lunwp, nargs=4,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN MAPPED_LUN", help="Set Write Protect bit for iSCSI Initiator LUN ACL")
	parser.add_option("--enabletpg", action="callback", callback=lio_target_enable_tpg, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="Enable LIO-Target Portal Group")
	parser.add_option("--listendpoints", action="callback", callback=lio_target_list_endpoints, nargs=0,
		help="List iSCSI Target Endpoints")
	parser.add_option("--listlunacls", action="callback", callback=lio_target_list_lunacls, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="List iSCSI Initiator LUN ACLs for LIO-Target Portal Group")
	parser.add_option("--listnodeacls", action="callback", callback=lio_target_list_nodeacls, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="List iSCSI Initiator ACLs for LIO-Target Portal Group")
	parser.add_option("--listnodeattr", action="callback", callback=lio_target_list_node_attr, nargs=3,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="List iSCSI Initiator ACL attributes for LIO-Target Portal Group")
	parser.add_option("--listnodeparam", action="callback", callback=lio_target_list_node_param, nargs=3,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="List iSCSI Initiator ACL RFC-3720 parameters for LIO-Target Portal Group")
	parser.add_option("--listnps", action="callback", callback=lio_target_list_nps, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="List LIO-Target Portal Group Network Portals")
	parser.add_option("--listtargetnames", action="callback", callback=lio_target_list_targetnames, nargs=0,
		help="List iSCSI Target Names")
	parser.add_option("--listtpgattr", action="callback", callback=lio_target_list_tpg_attr, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="List LIO-Target Portal Group attributes")
	parser.add_option("--listtpgparam", action="callback", callback=lio_target_list_tpg_param, nargs=2,
		type="string", dest="TARGET_IQN TPGT", help="List LIO-Target Portal Group RFC-3720 parameters")
	parser.add_option("--setchapauth", action="callback", callback=lio_target_set_chap_auth, nargs=5,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN USER PASS", help="Set CHAP authentication information for iSCSI Initiator Node ACL");
	parser.add_option("--setchapmutualauth", action="callback", callback=lio_target_set_chap_mutual_auth, nargs=5,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN USER_IN PASS_IN", help="Set CHAP mutual authentication information for iSCSI Initiator Node ACL");
        parser.add_option("--setchapdiscenforce", action="callback", callback=lio_target_set_enforce_discovery_auth, nargs=1,
                type="string", dest="Enforce=1, NoEnforcement=0", help="Set CHAP authentication enforcement for iSCSI Discovery Sessions");
        parser.add_option("--setchapdiscauth", action="callback", callback=lio_target_set_chap_discovery_auth, nargs=2,
                type="string", dest="USER PASS", help="Set CHAP authentication information for iSCSI Discovery Authentication")
        parser.add_option("--setchapdiscmutualauth", action="callback", callback=lio_target_set_chap_mutual_discovery_auth, nargs=2,
		type="string", dest="USER PASS", help="Set CHAP mutual authentication information for iSCSI Discovery Authentication")
	parser.add_option("--setnodeattr", action="callback", callback=lio_target_set_node_attr, nargs=5,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN <ATTRIBUTE> <VALUE>",  help="Set iSCSI Initiator ACL Attribute")
	parser.add_option("--setnodetcq", action="callback", callback=lio_target_set_node_tcq, nargs=4,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN DEPTH", help="Set iSCSI Initiator ACL TCQ Depth for LIO-Target Portal Group")
	parser.add_option("--settpgattr", action="callback", callback=lio_target_set_tpg_attr, nargs=4,
		type="string", dest="TARGET_IQN TPGT <ATTRIB> <VALUE>", help="Set LIO-Target Port Group Attribute")
	parser.add_option("--settpgparam", action="callback", callback=lio_target_set_tpg_param, nargs=4,
		type="string", dest="TARGET_IQN TPGT <PARAMETER> <VALUE>", help="Set LIO-Target Port Group RFC-3720 parameter")
	parser.add_option("--settgptgp","--setaluatpg", action="callback", callback=lio_target_alua_set_tgptgp, nargs=4,
		type="string", dest="TARGET_IQN TPGT LUN TG_PT_GP_NAME", help="Set ALUA Target Port Group for LIO-Target Port/LUN")
	parser.add_option("--settgptoff","--setaluaoff", action="callback", callback=lio_target_alua_set_tgpt_offline, nargs=3,
		type="string", dest="TARGET_IQN TPGT LUN", help="Set ALUA Target Port Secondary State OFFLINE")
	parser.add_option("--showchapauth", action="callback", callback=lio_target_show_chap_auth, nargs=3,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="Show CHAP authentication information for iSCSI Initiator Node ACL");
	parser.add_option("--showchapdiscauth", action="callback", callback=lio_target_show_chap_discovery_auth, nargs=0,
		help="Show CHAP authentication information for iSCSI Discovery portal");
	parser.add_option("--shownodetcq", action="callback", callback=lio_target_show_node_tcq, nargs=3,
		type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="Show iSCSI Initiator ACL TCQ Depth for LIO-Target Portal Group")
	parser.add_option("--showtgptgp", action="callback", callback=lio_target_alua_show_tgptgp, nargs=3,
		type="string", dest="TARGET_IQN TPGT LUN", help="Show ALUA Target Port Group for LIO-Target Port/LUN")
	parser.add_option("--unload", action="callback", callback=lio_target_unload, nargs=0,
		help="Unload LIO-Target")
	parser.add_option("--version", action="callback", callback=lio_target_version, nargs=0,
		help="Display LIO-Target version information")

	(options, args) = parser.parse_args()
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)
	elif not re.search('--', sys.argv[1]):
		lio_err("Unknown CLI option: " + sys.argv[1])

if __name__ == "__main__":
	main()
