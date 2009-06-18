#!/usr/bin/python
import os
import subprocess as sub
import string
import re
from optparse import OptionParser

tcm_root = "/sys/kernel/config/target/core"
lio_root = "/sys/kernel/config/target/iscsi"

def lio_target_del_iqn(option, opt_str, value, parser):
	iqn = str(value);

# Loop through LIO-Target IQN+TPGT list
	tpg_root = os.listdir(lio_root + "/" + iqn); 
	for tpgt_tmp in tpg_root:
		tpgt_tmp2 = tpgt_tmp.split('_')
		tpgt = tpgt_tmp2[1]

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
			lio_target_del_port(None, None, lun_val, None)

		tpg_val = [iqn,tpgt]
		lio_target_del_tpg(None, None, tpg_val, None)   

	rmdir_op = "rmdir " + lio_root + "/" + iqn
	print "rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op)
	if not ret:
		print "Successfully released iSCSI Target Endpoint IQN: " + iqn

	return

def lio_target_del_tpg(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);

	rmdir_op = "rmdir " + lio_root + "/" + iqn + "/tpgt_" + tpgt
	print "rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op)
	if not ret:
		print "Successfully released iSCSI Target Portal Group: " + iqn + " TPGT: " + tpgt
	
	return

def lio_target_add_np(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	np = str(value[2]);

	mkdir_op = "mkdir -p " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np/" + np
#	print "mkdir_op: " + mkdir_op
	ret = os.system(mkdir_op)
	if not ret:
		print "Successfully created network portal: " + np + " created " + iqn + " TPGT: " + tpgt 

	return

def lio_target_del_np(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	np = str(value[2]);

	rmdir_op = "rmdir " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np/" + np
	print "rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op)
	if not ret:
		print "Successfully released network portal: " + np + " created " + iqn + " TPGT: " + tpgt

	return

def lio_target_add_port(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	lun = str(value[2]);
	port_name = str(value[3]);
	tcm_obj = str(value[4]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	if os.path.isdir(lun_dir):
		print "iSCSI Target Logical Unit ConfigFS directory already exists"
		return -1

	mkdir_op = "mkdir -p " + lun_dir
#	print "mkdir_op: " + mkdir_op
	ret = os.system(mkdir_op)
	if ret:
		print "Unable to create iSCSI Target Logical Unit ConfigFS directory"
		return -1

	port_src = tcm_root + "/" + tcm_obj
	port_dst = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun + "/" + port_name
	link_op = "ln -s " + port_src + " " + port_dst
#	print "link_op: " + link_op
	ret = os.system(link_op)
	if not ret:
		print "Successfully created iSCSI Target Logical Unit"
	else:
		os.rmdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun)

	return

def lio_target_del_port(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	lun = str(value[2]);

	lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
	port_root = os.listdir(lun_dir)

	for port in port_root:
		if port == "alua_tg_pt_gp":
			continue

		unlink_op = "unlink " + lun_dir + "/" + port
#		print "del_portunlink_op: " + unlink_op
		ret = os.system(unlink_op)
		if ret:
			print "Unable to unlink iSCSI Target Logical Unit"

	rmdir_op= "rmdir " + lun_dir
#	print "del_port rmdir_op: " + rmdir_op
	ret = os.system(rmdir_op);
	if not ret:
		print "Successfully deleted iSCSI Target Logical Unit"

	return

def lio_target_tpg_disableauth(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	
	enable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/authentication"
	ret = os.system(enable_op)
	if ret:
		print "Unable to disable iSCSI Authentication on iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully disabled iSCSI Authentication on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_disable_lunwp(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	mapped_lun = str(value[3]);

	disable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun + "/write_protect"
	ret = os.system(disable_op)
	if ret:
		print "Unable to disable WriteProtect for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully disabled WRITE PROTECT for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_tpg_demomode(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);

	enable_op = "echo 1 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/generate_node_acls"
	ret = os.system(enable_op)
	if ret:
		print "Unable to enable DemoMode on iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully enabled DemoMode on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_enable_lunwp(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);
	mapped_lun = str(value[3]);

	enable_op = "echo 1 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initiator_iqn + "/lun_" + mapped_lun + "/write_protect"
	ret = os.system(enable_op)
	if ret:
		print "Unable to enable WriteProtect for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully enabled WRITE PROTECT for Mapped LUN: " + mapped_lun + " for " + initiator_iqn + " on iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_enable_tpg(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);

	enable_op = "echo 1 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/enable"
	ret = os.system(enable_op)
	if ret:
		print "Unable to enable iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully enabled iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_disable_tpg(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);

	disable_op = "echo 0 > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/enable"
	ret = os.system(disable_op)
	if ret:
		print "Unable to disable iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully disabled iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_add_lunacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initatior_iqn = str(value[2]);
	tpg_lun = str(value[3]);
	mapped_lun = str(value[4]);

	mkdir_op = "mkdir -p " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn + "/lun_" + mapped_lun
	ret = os.system(mkdir_op)
	if ret:
		print "Unable to add iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	addlunacl_op = "ln -s " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + tpg_lun + " " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn + "/lun_" + mapped_lun + "/lio_lun"

	ret = os.system(addlunacl_op)
	if ret:
		print "Unable to add iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
		return 1
	else:
		print "Successfully added iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_del_lunacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initatior_iqn = str(value[2]);
	mapped_lun = str(value[3]);

	lun_link_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn + "/lun_" + mapped_lun
	for lun_acl_link in os.listdir(lun_link_dir):
		if lun_acl_link == "write_protect":
			continue

		unlink_op = "unlink " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn + "/lun_" + mapped_lun + "/" + lun_acl_link
#		print "unlink_op: " + unlink_op
		ret = os.system(unlink_op)
		if ret:
			print "Unable to unlink iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
			return 1
		
	dellunacl_op = "rmdir " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn + "/lun_" + mapped_lun
	ret = os.system(dellunacl_op)
	if ret:
		print "Unable to delete iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
		return 1
	else:
		print "Successfully deleted iSCSI Initiator Mapped LUN: " + mapped_lun + " ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_add_nodeacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initatior_iqn = str(value[2]);
	
	addnodeacl_op = "mkdir -p " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn
	ret = os.system(addnodeacl_op)
	if ret:
		print "Unable to add iSCSI Initaitor ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully added iSCSI Initaitor ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_del_nodeacl(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initiator_iqn = str(value[2]);

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
		print "Unable to delete iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully deleted iSCSI Initaitor ACL " + initiator_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_set_node_tcq(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initatior_iqn = str(value[2]);
	depth = str(value[3]);

	setnodetcq_op = "echo " + depth + " > " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn + "/cmdsn_depth"
	ret = os.system(setnodetcq_op)
	if ret:
		print "Unable to set TCQ: " + depth + " for iSCSI Initaitor ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt
	else:
		print "Successfully set TCQ: " + depth + " for iSCSI Initaitor ACL " + initatior_iqn + " for iSCSI Target Portal Group: " + iqn + " " + tpgt

	return

def lio_target_show_node_tcq(option, opt_str, value, parser):
	iqn = str(value[0]);
	tpgt = str(value[1]);
	initatior_iqn = str(value[2]);

	nacl = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/" + initatior_iqn
	if not os.path.isdir(nacl):
		print "iSCSI Initiator ACL: " + initatior_iqn + " does not exist for iSCSI Target Portal Group: " + iqn + " " + tpgt
		return 1	

	tcq_depth_file = nacl + "/cmdsn_depth"
	p = os.open(tcq_depth_file, 0)
	value = os.read(p, 8)
	print value.rstrip()
	os.close(p)

	return

def lio_target_list_endpoints(option, opt_str, value, parser):

	iqn_root = os.listdir(lio_root)
	
	for iqn in iqn_root:
		if iqn == "lio_version":
			continue

		print "\------> " + iqn

		tpg_root = lio_root + "/" + iqn
		for tpg in os.listdir(tpg_root):
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
					
					port_link = port_dir + "/" + port
					sourcelink = os.readlink(port_link)
					# Skip over ../../../../../ in sourcelink"		
					print "                 \-------> " + lun + "/" + port + " -> " + sourcelink[18:]
					

	return

def lio_target_list_lunacls(option, opt_str, value, parser):
	iqn = str(value[0]);
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
				
				sourcelink = os.readlink(lun_link_dir + "/" + lun_link)
				# Skip over ../../../../../../ in sourcelink"
				print "         \-------> " + lun + " -> " + sourcelink[21:]
				print "                   \-------> Write Protect for " + lun + ": " + wp_info

	return

def lio_target_list_nodeacls(option, opt_str, value, parser):
	iqn = str(value[0]);
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

		print iqn	

	return

def lio_target_unload(option, opt_str, value, parser):

	iqn_root = os.listdir(lio_root)

	# Loop through LIO-Target IQN list
	for iqn in iqn_root:
		if iqn == "lio_version":
			continue

		# Loop through LIO-Target IQN+TPGT list
		tpg_root = os.listdir(lio_root + "/" + iqn);
		for tpgt_tmp in tpg_root:
			tpgt_tmp2 = tpgt_tmp.split('_')
			tpgt = tpgt_tmp2[1]

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
				lio_target_del_port(None, None, lun_val, None)

			tpg_val = [iqn,tpgt]
			lio_target_del_tpg(None, None, tpg_val, None)	

		lio_target_del_iqn(None, None, iqn, None)

	rmdir_op = "rmdir " + lio_root
	ret = os.system(rmdir_op)
	if ret:
		print "Unable to release lio_root: " + lio_root

	rmmod_op = "rmmod iscsi_target_mod"
	ret = os.system(rmmod_op)
	if ret:
		print "Unable to unload iscsi_target_mod"

	return

def lio_target_version(option, opt_str, value, parser):

	os.system("cat /sys/kernel/config/target/iscsi/lio_version")
	return

parser = OptionParser()
parser.add_option("--addlunacl", action="callback", callback=lio_target_add_lunacl, nargs=5,
	type="string", dest="TARGET_IQN TPGT INITIATOR_IQN TPG_LUN MAPPED_LUN", help="Add iSCSI Initiator LUN ACL to LIO-Target Portal Group LUN")
parser.add_option("--addnodeacl", action="callback", callback=lio_target_add_nodeacl, nargs=3,
	type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="Add iSCSI Initiator ACL to LIO-Target Portal Group")
parser.add_option("--addnp", action="callback", callback=lio_target_add_np, nargs=3,
	type="string", dest="TARGET_IQN TPGT IP:PORT", help="Add LIO-Target IPv6 or IPv4 network portal")
parser.add_option("--addlun", action="callback", callback=lio_target_add_port, nargs=5,
	type="string", dest="TARGET_IQN TPGT LUN PORT_ALIAS TCM_HBA/DEV ", help="Create LIO-Target Logical Unit")
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
parser.add_option("--demomode", action="callback", callback=lio_target_tpg_demomode, nargs=2,
	type="string", dest="TARGET_IQN TPGT", help="Enable DemoMode for LIO-Target Portal Group")
parser.add_option("--disableauth", action="callback", callback=lio_target_tpg_disableauth, nargs=2,
	type="string", dest="TARGET_IQN TPGT", help="Disable iSCSI Authentication for LIO-Target Portal Group")
parser.add_option("--disablelunwp", action="callback", callback=lio_target_disable_lunwp, nargs=4,
	type="string", dest="TARGET_IQN TPGT INITIATOR_IQN MAPPED_LUN", help="Clear Write Protect bit for iSCSI Initiator LUN ACL")
parser.add_option("--disabletpg", action="callback", callback=lio_target_disable_tpg, nargs=2,
	type="string", dest="TARGET_IQN TPGT", help="Disable LIO-Target Portal Group")
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
parser.add_option("--listnps", action="callback", callback=lio_target_list_nps, nargs=2,
	type="string", dest="TARGET_IQN TPGT", help="List LIO-Target Portal Group Network Portals")
parser.add_option("--listtargetnames", action="callback", callback=lio_target_list_targetnames, nargs=0,
	help="List iSCSI Target Names")
parser.add_option("--setnodetcq", action="callback", callback=lio_target_set_node_tcq, nargs=4,
	type="string", dest="TARGET_IQN TPGT INITIATOR_IQN DEPTH", help="Set iSCSI Initiator ACL TCQ Depth for LIO-Target Portal Group")
parser.add_option("--shownodetcq", action="callback", callback=lio_target_show_node_tcq, nargs=3,
	type="string", dest="TARGET_IQN TPGT INITIATOR_IQN", help="Show iSCSI Initiator ACL TCQ Depth for LIO-Target Portal Group")
parser.add_option("--unload", action="callback", callback=lio_target_unload, nargs=0,
	help="Unload LIO-Target")
parser.add_option("--version", action="callback", callback=lio_target_version, nargs=0,
	help="Display LIO-Target version information")
parser.parse_args()
