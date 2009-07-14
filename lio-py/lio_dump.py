#!/usr/bin/python
import os
import subprocess as sub
import string
import re
from optparse import OptionParser

lio_root = "/sys/kernel/config/target/iscsi"

def lio_target_configfs_dump():

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

			print "#### Network portals for iSCSI Target Portal Group"
			np_root = os.listdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np")
			for np in np_root:
				print "mkdir -p " + lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np/" + np

			print "#### iSCSI Target Ports"
			lun_root = os.listdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun")
			for lun_tmp in lun_root:
				lun_tmp2 = lun_tmp.split('_')
				lun = lun_tmp2[1]
				
				lun_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
				print "mkdir -p " + lun_dir
				port_root = os.listdir(lun_dir)
				for port in port_root:
					if port == "alua_tg_pt_gp":
						continue

					port_link = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun + "/" + port
					sourcelink = os.readlink(port_link)
					sourcelink2 = os.path.join(os.path.dirname(port_link), sourcelink)
					print "ln -s " + sourcelink2 + " " + port_link
				
			
			# Dump values of iscsi/iqn/tpgt/attrib/
			print "#### Attributes for iSCSI Target Portal Group"
			attrib_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/"
			attrib_root = os.listdir(attrib_dir)
			for attrib in attrib_root:
				attrib_file = attrib_dir + attrib 
				p = os.open(attrib_file, 0)
				value = os.read(p, 16)
				print "echo " + value.rstrip() + " > " + attrib_file
				os.close(p)
	
			# Dump values for iscsi/iqn/tpgt/param
			print "#### Parameters for iSCSI Target Portal Group"
			param_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/param/"
			param_root = os.listdir(param_dir)
			for param in param_root:
				param_file = param_dir + param
				p = os.open(param_file, 0)
				value = os.read(p, 256)
				print "echo \"" + value.rstrip() + "\" > " + param_file
				os.close(p)

			# Dump iSCSI Initiator Node ACLs from iscsi/iqn/tpgt/acls
			print "#### iSCSI Initiator ACLs for iSCSI Target Portal Group"
			nacl_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/"
			nacl_root = os.listdir(nacl_dir)
			for nacl in nacl_root:
				print "mkdir -p " + nacl_dir + nacl
				tcq_depth_file = nacl_dir + nacl + "/cmdsn_depth"
				p = os.open(tcq_depth_file, 0)
				value = os.read(p, 8)
				print "echo " + value.rstrip() + " > " + tcq_depth_file
				os.close(p)

				# Dump iSCSI Initiator ACL authentication info from iscsi/iqn/tpgt/acls/$INITIATOR/auth
				print "#### iSCSI Initiator ACL authentication information"
				auth_dir = nacl_dir + nacl + "/auth"
				for auth in os.listdir(auth_dir):
					if auth == "authenticate_target":
						continue
					auth_file = auth_dir + "/" + auth
					p = os.open(auth_file, 0)
					value = os.read(p, 256)
					ret = value.isspace()
					if ret:
						os.close(p)
						continue
					print "echo -n " + value.rstrip() + " > " + auth_file
					os.close(p)

				# Dump iSCSI Initiator ACL TPG attributes from iscsi/iqn/tpgt/acls/$INITIATOR/attrib
				print "#### iSCSI Initiator ACL TPG attributes"
				nacl_attrib_dir = nacl_dir + nacl + "/attrib"
				for nacl_attrib in os.listdir(nacl_attrib_dir):
					nacl_attrib_file = nacl_attrib_dir + "/" + nacl_attrib
					p = os.open(nacl_attrib_file, 0)
					value = os.read(p, 8)
					print "echo " + value.rstrip() + " > " + nacl_attrib_file
					os.close(p)

				# Dump iSCSI Initiator LUN ACLs from iscsi/iqn/tpgt/acls/$INITIATOR/lun
				print "#### iSCSI Initiator LUN ACLs for iSCSI Target Portal Group"
				lun_acl_dir = nacl_dir + nacl
				for lun_acl in os.listdir(lun_acl_dir):
					ret = re.search('lun_', lun_acl)
					if not ret:
						continue
					lun_link_dir = nacl_dir + nacl + "/" + lun_acl
					print "mkdir -p " + lun_link_dir

					for lun_acl_link in os.listdir(lun_link_dir):
						if lun_acl_link == "write_protect":
							p = os.open(lun_link_dir + "/write_protect", 0)
							value = os.read(p, 4)
							print "echo " + value.rstrip() + " > " + lun_link_dir + "/write_protect"
							os.close(p)
							continue

						sourcelink = os.readlink(lun_link_dir + "/" + lun_acl_link)
						sourcelink2 = os.path.join(os.path.dirname(lun_link_dir + "/" + lun_acl_link), sourcelink)
						print "ln -s " + sourcelink2 + " " + lun_link_dir + "/" + lun_acl_link 

			# Dump value of iscsi/iqn/tpgt/enable
			print "#### Trigger to enable iSCSI Target Portal Group"
			enable_file = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/enable"
			p = os.open(enable_file, 0)
			value = os.read(p, 1)
			print "echo " + value.rstrip() + " > " + enable_file
			os.close(p)

#		lio_target_del_iqn(None, None, iqn, None)

	return

lio_target_configfs_dump()
