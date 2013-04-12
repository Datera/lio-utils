#!/usr/bin/python
import os, sys
import subprocess as sub
import string
import re
import datetime, time
from optparse import OptionParser

lio_root = "/sys/kernel/config/target/iscsi"

def lio_target_configfs_dump(option, opt_str, value, parser):

	if not os.path.isdir(lio_root):
		print "Unable to access lio_root: " + lio_root
		sys.exit(1)

	iqn_root = os.listdir(lio_root)

	# This will load up iscsi_target_mod.ko
	print "mkdir " + lio_root

	print "#### iSCSI Discovery authentication information"
	auth_dir = lio_root + "/discovery_auth"
	if os.path.isdir(auth_dir) == True:
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

			print "#### Network portals for iSCSI Target Portal Group"
			np_root = os.listdir(lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np")
			for np in np_root:
				np_path = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/np/" + np
				print "mkdir -p " + np_path
				np_path_iser = np_path + "/iser"
				if os.path.isfile(np_path_iser):
					iser_fd = open(np_path_iser, 'r')
					iser_attr = iser_fd.read()
					iser_attr = iser_attr.strip()
					if iser_attr == "1":
						print "echo 1 > " + np_path_iser

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
					if port == "alua_tg_pt_offline":
						continue
					if port == "alua_tg_pt_status":
						continue
					if port == "alua_tg_pt_write_md":
						continue
					
					if not os.path.islink(lun_dir + "/" + port):
						continue

					port_link = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun + "/" + port
					sourcelink = os.readlink(port_link)
					sourcelink2 = os.path.join(os.path.dirname(port_link), sourcelink)
					print "ln -s " + sourcelink2 + " " + port_link

				# Dump ALUA Target Port Group
				tg_pt_gp_file = lun_dir + "/alua_tg_pt_gp"
				p = os.open(tg_pt_gp_file, 0)
				try:
					value = os.read(p, 512)
				except:
					os.close(p)
					continue
				os.close(p)
				if value:
					tg_pt_gp_tmp = value.split('\n')
					tg_pt_gp_out = tg_pt_gp_tmp[0]
					off = tg_pt_gp_out.index('Alias: ')
					off += 7 # Skip over "Alias: "
					tg_pt_gp_name = tg_pt_gp_out[off:]
					# Only need to dump if LIO-Target Port is NOT partof
					# the 'default_tg_pt_gp'
					if not re.search(tg_pt_gp_name, 'default_tg_pt_gp'):
						print "#### ALUA Target Port Group"
						print "echo " + tg_pt_gp_name + " > " + tg_pt_gp_file

					print "lio_node --aluasecmd " + iqn + " " + tpgt + " " + lun

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
	
			# Dump values of iscsi/iqn/tpgt/attrib/
			print "#### authentication for iSCSI Target Portal Group"
			auth_dir = lio_root + "/" + iqn + "/tpgt_" + tpgt + "/auth/"
			if os.path.isdir(auth_dir):
				auth_root = os.listdir(auth_dir)
				for auth in auth_root:
					auth_file = auth_dir + auth
					p = os.open(auth_file, 0)
					value = os.read(p, 256)
					ret = value.isspace()
					if ret:
						os.close(p)
						continue
					print "echo -n " + value.rstrip() + " > " + auth_file
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

						if not os.path.islink(lun_link_dir + "/" + lun_acl_link):
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

def lio_backup_to_file(option, opt_str, value, parser):
	now = str(value)

	if not os.path.isdir(lio_root):
		print "Unable to access lio_root: " + lio_root
		sys.exit(1) 

	backup_dir = "/etc/target/backup"
	if not os.path.isdir(backup_dir):
		op = "mkdir " + backup_dir
		ret = os.system(op)
		if ret:
			print "Unable to open backup_dir"
			sys.exit(1)

	op = "lio_dump --stdout"
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to dump LIO-Target/ConfigFS running state"
		sys.exit(1)

	print "Making backup of LIO-Target/ConfigFS with timestamp: " + now
	backup_file = backup_dir + "/lio_backup-" + now + ".sh"
	if os.path.isfile(backup_file): 
		print "LIO-Target backup_file: " + backup_file + "already exists, exiting"
		p.close()
		sys.exit(1)

	back = open(backup_file, 'w')

	line = p.readline()
	while line:
		print >>back, line.rstrip()
		line = p.readline()

	p.close()
	back.close()
	return backup_file

def main():

	parser = OptionParser()
	parser.add_option("--s","--stdout", action="callback", callback=lio_target_configfs_dump, nargs=0,
		help="Dump running LIO-Target/ConfigFS syntax to STDOUT")
	parser.add_option("--t", "--tofile", action="callback", callback=lio_backup_to_file, nargs=1,
		type="string", dest="DATE_TIME", help="Backup running LIO-Target/ConfigFS syntax to /etc/target/backup/lio_backup-<DATE_TIME>.sh")

	(options, args) = parser.parse_args()
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)
	elif not re.search('--', sys.argv[1]):
		print "Unknown CLI option: " + sys.argv[1]
		sys.exit(1)

if __name__ == "__main__":
        main()
