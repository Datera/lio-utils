#!/usr/bin/python
import os, sys, shutil
import subprocess as sub
import string
import re
import datetime, time
import optparse

target_root = "/sys/kernel/config/target/"
spec_root = "/var/target/fabric/"

def fabric_err(msg):
	print >> sys.stderr, msg
	sys.exit(1)

def fabric_configfs_dump(fabric_name, fabric_root, module_name):

	if not os.path.isdir(fabric_root):
		print "Unable to access fabric_root: " + fabric_root
		sys.exit(1)

	iqn_root = os.listdir(fabric_root)

	# This will load up the fabric module
	print "modprobe " + module_name
	print "mkdir " + fabric_root

#	print "#### " + fabric_name + " Discovery authentication information"
	auth_dir = fabric_root + "/discovery_auth"
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

	iqn_root = os.listdir(fabric_root)

	# Loop through LIO-Target IQN list
	for iqn in iqn_root:
		if not os.path.isdir(fabric_root + "/" + iqn):
			continue
		if iqn == "lio_version":
			continue
		if iqn == "discovery_auth":
			continue

		# Loop through LIO-Target IQN+TPGT list
		tpg_root = os.listdir(fabric_root + "/" + iqn);
		for tpgt_tmp in tpg_root:
			if tpgt_tmp == "fabric_statistics":
				continue

			tpgt_tmp2 = tpgt_tmp.split('_')
			tpgt = tpgt_tmp2[1]

#			print "#### Network portals for iSCSI Target Portal Group"
#			np_root = os.listdir(fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/np")
#			for np in np_root:
#				print "mkdir -p " + fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/np/" + np


			# Dump Nexus attribute (when available)
                        nexus_file = fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/nexus"
                        if os.path.isfile(nexus_file):
				print "mkdir -p " + fabric_root + "/" + iqn + "/tpgt_" + tpgt
                                p = os.open(nexus_file, 0)
                                value = os.read(p, 256)
                                print "echo " + value.rstrip() + " > " + nexus_file
                                os.close(p)

			print "#### " + fabric_name + " Target Ports"
			lun_root = os.listdir(fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/lun")
			for lun_tmp in lun_root:
				lun_tmp2 = lun_tmp.split('_')
				lun = lun_tmp2[1]
				
				lun_dir = fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun
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

					port_link = fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/lun/lun_" + lun + "/" + port
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

#FIXME: --aluasecmd support
#					print "lio_node --aluasecmd " + iqn + " " + tpgt + " " + lun

			# Dump values of iscsi/iqn/tpgt/attrib/
			print "#### Attributes for " + fabric_name + " Target Portal Group"
			attrib_dir = fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/attrib/"
			attrib_root = os.listdir(attrib_dir)
			for attrib in attrib_root:
				attrib_file = attrib_dir + attrib 
				p = os.open(attrib_file, 0)
				value = os.read(p, 16)
				print "echo " + value.rstrip() + " > " + attrib_file
				os.close(p)
	
			# Dump values for iscsi/iqn/tpgt/param
			print "#### Parameters for " + fabric_name + " Target Portal Group"
			param_dir = fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/param/"
			param_root = os.listdir(param_dir)
			for param in param_root:
				param_file = param_dir + param
				p = os.open(param_file, 0)
				value = os.read(p, 256)
				print "echo \"" + value.rstrip() + "\" > " + param_file
				os.close(p)

			if os.path.isfile(nexus_file):
				continue

			# Dump fabric Initiator Node ACLs from fabric_root/$WWN/tpgt_$TPGT/acls/
			print "#### " + fabric_name + " Initiator ACLs for " + fabric_name + " Target Portal Group"
			nacl_dir = fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/acls/"
			nacl_root = os.listdir(nacl_dir)
			for nacl in nacl_root:
				print "mkdir -p " + nacl_dir + nacl

				# Dump fabric Initiator ACL authentication info from fabric_root/$WWN/tpgt_$TPGT/acls//$INITIATOR/auth
				print "#### " + fabric_name + " Initiator ACL authentication information"
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

				# Dump fabric Initiator ACL TPG attributes from fabric_root/$WWN/tpgt_$TPGT/acls/$INITIATOR/attrib
				print "#### " + fabric_name + " Initiator ACL TPG attributes"
				nacl_attrib_dir = nacl_dir + nacl + "/attrib"
				for nacl_attrib in os.listdir(nacl_attrib_dir):
					nacl_attrib_file = nacl_attrib_dir + "/" + nacl_attrib
					p = os.open(nacl_attrib_file, 0)
					value = os.read(p, 8)
					print "echo " + value.rstrip() + " > " + nacl_attrib_file
					os.close(p)

				# Dump fabric Initiator LUN ACLs from fabric_root/$WWN/tpgt_$TPGT//acls/$INITIATOR/lun
				print "#### " + fabric_name + " Initiator LUN ACLs for iSCSI Target Portal Group"
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

			# Dump value of fabric_root/$WWN/tpgt_$TPGT//enable
			print "#### Trigger to enable " + fabric_name + " Target Portal Group"
			enable_file = fabric_root + "/" + iqn + "/tpgt_" + tpgt + "/enable"
			if os.path.isfile(enable_file):
				p = os.open(enable_file, 0)
				value = os.read(p, 1)
				print "echo " + value.rstrip() + " > " + enable_file
				os.close(p)


	return

def fabric_configfs_dump_all():

	for fabric_name in os.listdir(target_root):
		if fabric_name == "version":
			continue
		if fabric_name == "core":
			continue
		# FIXME: currently using lio_dump --stdout
		if fabric_name == "iscsi":
			continue

		fabric_root = target_root + fabric_name
#		print "Using fabric_configfs_dump_all: " + fabric_name + ", " + fabric_root
		module_name = fabric_get_module_name(fabric_name)
#		print "module_name: "+ module_name
		
		fabric_configfs_dump(fabric_name, fabric_root, module_name);

	return

def fabric_backup_to_file(date_time, fabric_name, fabric_root, module_name):
	now = date_time

	if not os.path.isdir(fabric_root):
		print "Unable to access fabric_root: " + fabric_root
		sys.exit(1) 

	current_dir = "/etc/target"
	backup_dir = "/etc/target/backup"
	if not os.path.isdir(backup_dir):
		op = "mkdir " + backup_dir
		ret = os.system(op)
		if ret:
			print "Unable to open backup_dir"
			sys.exit(1)

	op = "tcm_fabric --stdout --fabric-name=" + fabric_name + " --fabric-root=" + fabric_root + " --module-name=" + module_name
#	print "Using op: " + op
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to dump " + fabric_name + "/ConfigFS running state"
		sys.exit(1)

	orig_file = current_dir + "/" + fabric_name + "_start.sh"

	print "Making backup of " + fabric_name + "/ConfigFS with timestamp: " + now
	backup_file = backup_dir + "/" + fabric_name + "_backup-" + now + ".sh"
	if os.path.isfile(backup_file): 
		print "" + fabric_name + " backup_file: " + backup_file + "already exists, exiting"
		p.close()
		sys.exit(1)

	back = open(backup_file, 'w')

	line = p.readline()
	while line:
		print >>back, line.rstrip()
		line = p.readline()

	p.close()
	back.close()

	ret = shutil.copyfile(backup_file, orig_file)
	if ret:
		print "Unable to copy " + back_file
		sys.exit(1)

	print "Successfully updated default config " + orig_file

	return backup_file

def fabric_backup_to_file_all(date_time):

	if not os.path.isdir(target_root):
		print "Unable to open target_root: " + target_root
		sys.exit(1)

	for fabric_name in os.listdir(target_root):
		if fabric_name == "version":
			continue
		if fabric_name == "core":
			continue	
		# FIXME: currently using lio_dump
		if fabric_name == "iscsi":
			continue

		fabric_root = target_root + fabric_name
#		print "Using fabric_backup_to_file: " + date_time + ", " + fabric_name + ", " + fabric_root
		module_name = fabric_get_module_name(fabric_name)
#		print "Using module_name: "+ module_name

		fabric_backup_to_file(date_time, fabric_name, fabric_root, module_name)
	

	return

def fabric_unload(fabric_name, fabric_root, module_name):

	if not os.path.isdir(fabric_root):
		print "Unable to access fabric_root: " + fabric_root
		sys.exit(1)

	wwn_root = os.listdir(fabric_root)
	for wwn in wwn_root:
		if not os.path.isdir(fabric_root + "/" + wwn):
			continue
		if wwn == "discovery_auth":
			continue

		tpg_root = fabric_root + "/" + wwn
		for tpgt_tmp in os.listdir(tpg_root):
			if tpgt_tmp == "fabric_statistics":
				continue

			tpgt_tmp2 = tpgt_tmp.split('_')
			tpgt = tpgt_tmp2[1]

			if os.path.isfile(fabric_root + "/" + wwn + "/tpgt_" + tpgt + "/enable"):
				disable_op = "echo 0 > " + fabric_root + "/" + wwn + "/tpgt_" + tpgt + "/enable"
				ret = os.system(disable_op)
				if ret:
					print "Unable to disable TPG: " + wwn + " TPGT: " + tpgt

			nacl_root = fabric_root + "/" + wwn + "/tpgt_" + tpgt + "/acls"
			for nacl in os.listdir(nacl_root):
				lun_acl_root = nacl_root + "/" + nacl + "/"
				for lun_acl in os.listdir(lun_acl_root):
					ret = re.search('lun_', lun_acl)
					if not ret:
						continue
					mapped_lun = lun_acl[4:]

					lun_link_dir = lun_acl_root + "/" + lun_acl + "/"
					for lun_acl_link in os.listdir(lun_link_dir):
						if lun_acl_link == "write_protect":
							continue

						if os.path.islink(lun_link_dir + "/" + lun_acl_link):
							unlink_op = lun_link_dir + "/" + lun_acl_link
							ret = os.unlink(unlink_op)
							if ret:
								print "Unable to unlink MappedLUN: " + lun_link_dir + "/" + lun_acl_link

					dellunacl_op = "rmdir " + lun_link_dir
					ret = os.system(dellunacl_op)
					if ret:
						print "Unable to rmdir fabric mapped_lun"

				delnodeacl_op = "rmdir " + nacl_root + "/" + nacl + "/"
				ret = os.system(delnodeacl_op)
				if ret:
					print "Unable to remove NodeACL: " +  nacl_root + "/" + nacl + "/"
			
			lun_root = fabric_root + "/" + wwn + "/tpgt_" + tpgt + "/lun"
			for lun_tmp in os.listdir(lun_root):
				lun_tmp2 = lun_tmp.split('_')
				lun = lun_tmp2[1]

				lun_dir = lun_root + "/lun_" + lun
				for port in os.listdir(lun_dir):
					if not os.path.islink(lun_dir + "/" + port):
						continue

					unlink_op = lun_dir + "/" + port
					ret = os.unlink(unlink_op)
					if ret:
						print "Unable to unlink fabric port/lun"

				rmdir_op= "rmdir " + lun_dir
				ret = os.system(rmdir_op);
				if ret:
					print "Unable to rmdir fabric port/lun: " + lun_dir

		
			rmdir_op = "rmdir " + fabric_root + "/" + wwn + "/tpgt_" + tpgt + "/"
			ret = os.system(rmdir_op)
			if ret:
				print "Unable to rmdir fabric tpg: " + fabric_root + "/" + wwn + "/tpgt_" + tpgt + "/"

		rmdir_op = "rmdir " + fabric_root + "/" + wwn + "/"
		ret = os.system(rmdir_op)
		if ret:
			print "Unable to rmdir fabric wwn: " + fabric_root + "/" + wwn + "/"
			
			

	rmdir_op = "rmdir " + fabric_root
        ret = os.system(rmdir_op)
        if ret:
                print "Unable to release fabric_root: " + fabric_root

        rmmod_op = "rmmod " + module_name
        ret = os.system(rmmod_op)
        if ret:
               print "Unable to unload " + module_name

	print "Successfully released fabric: " + fabric_root
        return

def fabric_get_module_name(fabric_name):
	kernel_module = ""

	for specs in os.listdir(spec_root):
		if specs == "README":
			continue
#		print "specs: " + specs + ", fabric_name: " + fabric_name

		if not re.search(fabric_name + ".spec", specs) and not re.search("tcm_" + fabric_name + ".spec", specs) and not re.search(fabric_name, specs):
			continue
			
		op = "cat " + spec_root + specs
		p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
		if not p:
			print "Unable to dump " + fabric_name + "/ConfigFS running state"
			sys.exit(1)

	        line = p.readline()
	        while line:
			tmp = line.rstrip()
			# Check for 'kernel_module' line in $FABRIC.spec
	                if re.search('kernel_module', tmp):
				tmp_list = tmp.split('= ')
				p.close()
				return tmp_list[1]
				
	                line = p.readline()
	
	        p.close()

	return kernel_module
		
def fabric_unloadall():

	module_name = ""

	try:
		for fabric_name in os.listdir(target_root):
			if fabric_name == "version":
				continue
			if fabric_name == "core":
				continue
			# FIXME: currently using lio_node --unload
			if fabric_name == "iscsi":
				continue

			fabric_root = target_root + fabric_name
			module_name = fabric_get_module_name(fabric_name)
			#print "fabric_get_module_name() using: " + module_name
		
			if module_name == "":
				continue

			fabric_unload(fabric_name, fabric_root, module_name)
	except OSError, (errno, strerror):
		if errno == 2:
			fabric_err("%s %s\n%s" % (target_root, strerror, "Is kernel module loaded?") )
		

def do_work(stdout_enable, stdout_enable_all, date_time, unload, unloadall, fabric_name, fabric_root, module_name):

	if not stdout_enable == "None":
		fabric_configfs_dump(fabric_name, fabric_root, module_name)
	elif not stdout_enable_all == "None":
		fabric_configfs_dump_all()
	elif not date_time == "None":
		fabric_backup_to_file(date_time, fabric_name, fabric_root, module_name)
	elif not unload == "None":
		fabric_unload(fabric_name, fabric_root, module_name)
	elif not unloadall == "None":
		fabric_unloadall()

	return 0

def main(): 

	parser_fabric = optparse.OptionParser()
	parser_fabric.add_option("--s","--stdout", dest='stdout_enable', action='store', nargs=0,
		help="Dump running Fabric/ConfigFS syntax to STDOUT", type='string')
	parser_fabric.add_option("--z","--stdoutall", dest='stdout_enable_all', action='store', nargs=0,
		help="Dump all running Fabric/ConfigFS syntax to STDOUT", type='string')
	parser_fabric.add_option("--t", "--tofile", dest="date_time", action='store', nargs=1,
		help="Backup running Fabric/ConfigFS syntax to /etc/target/backup/fabricname_backup-<DATE_TIME>.sh",
			type='string')
	parser_fabric.add_option("--u", "--unload", dest="unload",  action='store', nargs=0,
		help="Unload running Fabric/ConfigFS", type='string')
	parser_fabric.add_option("--a", "--unloadall", dest="unloadall",  action='store', nargs=0,
	        help="Unload all running Fabric/ConfigFS", type='string')
	parser_fabric.add_option("--f", "--fabric-name", dest='fabric_name', action='store', nargs=1,
		help="Target fabric name", type='string')
	parser_fabric.add_option("--r", "--fabric-root", dest='fabric_root', action='store', nargs=1,
		help="Target fabric configfs root", type='string')
	parser_fabric.add_option("--m", "--module-name", dest='module_name', action='store', nargs=1,
		help="Target fabric module name ", type='string')

	(opts_fabric, args_fabric) = parser_fabric.parse_args()

	mandatories = ['fabric_name', 'fabric_root', 'module_name']
	for m in mandatories:
	        if not opts_fabric.__dict__[m]:
	                unloadall = str(opts_fabric.__dict__['unloadall'])
	                stdout_enable = str(opts_fabric.__dict__['stdout_enable'])
	                stdout_enable_all = str(opts_fabric.__dict__['stdout_enable_all'])
	                date_time = str(opts_fabric.__dict__['date_time'])
	                if unloadall == "None" and stdout_enable == "None" and stdout_enable_all == "None" and date_time == "None":
	                        print "mandatory option is missing\n"
	                        parser_fabric.print_help()
	                        exit(-1)

        do_work(str(opts_fabric.stdout_enable), str(opts_fabric.stdout_enable_all),
		str(opts_fabric.date_time), str(opts_fabric.unload), str(opts_fabric.unloadall),
		str(opts_fabric.fabric_name), str(opts_fabric.fabric_root),
		str(opts_fabric.module_name))

if __name__ == "__main__":
        main()
