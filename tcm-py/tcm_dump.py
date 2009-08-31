#!/usr/bin/python

import os, sys, shutil
import subprocess as sub
from subprocess import Popen, PIPE
import string
import re
import datetime, time
from optparse import OptionParser

import tcm_node
import tcm_pscsi
import tcm_iblock
import tcm_ramdisk
import tcm_fileio

import lio_dump

tcm_root = "/sys/kernel/config/target/core"

def tcm_dump_hba_devices():
	return	

def tcm_dump_configfs(option, opt_str, value, parser):

	if not os.path.isdir(tcm_root):
		print "Unable to access tcm_root: " + tcm_root
		sys.exit(1)

	print "modprobe target_core_mod"

	# Loop through ALUA Logical Unit Groups
	# Note that the 'default_lu_gp' is automatically created when
	# target_core_mod is loaded.
	print "#### ALUA Logical Unit Groups"
	for lu_gp in os.listdir(tcm_root + "/alua/lu_gps"):	
		if lu_gp == "default_lu_gp":
			continue

		print "mkdir -p " + tcm_root + "/alua/lu_gps/" + lu_gp
		lu_gp_id_file = tcm_root + "/alua/lu_gps/" + lu_gp + "/lu_gp_id"
		p = os.open(lu_gp_id_file, 0)
		value = os.read(p, 8)
		os.close(p)
		if not value:
			continue
		print "echo " + value.rstrip() + " > " + lu_gp_id_file

	# Loop through HBA list
	for f in os.listdir(tcm_root):
		if f == "alua":
			continue;
		
#		print "mkdir -p " + tcm_root + "/" + f

		dev_root = tcm_root + "/" + f + "/"
		for g in os.listdir(dev_root):
			if g == "hba_info":
				continue;
			
			# Dump device aka storage object
			print "#### Parameters for TCM subsystem plugin storage object reference"
			
			# Generate subsystem dependent configfs ops for association to
		 	# an target_core_mod storage object.
			result = re.search('pscsi_', f)
			if result:
				dev = dev_root + g
				params = tcm_pscsi.pscsi_get_params(dev)
				if not params:
					continue
				print "tcm_node --establishdev " + f + "/" + g + " " + str(params)
			result = re.search('iblock_', f)
			if result:
				dev = dev_root + g
				params = tcm_iblock.iblock_get_params(dev)
				if not params:
					continue
				print "tcm_node --establishdev " + f + "/" + g + " " + str(params)
			result = re.search('rd_dr_', f)
			if result:
				dev = dev_root + g
				params = tcm_ramdisk.rd_get_params(dev)	
				if not params:
					continue
				print "tcm_node --establishdev " + f + "/" + g + " " + str(params)
			result = re.search('rd_mcp_', f)
			if result:
				dev = dev_root + g
				params = tcm_ramdisk.rd_get_params(dev)
				if not params:
					continue
				print "tcm_node --establishdev " + f + "/" + g + " " + str(params)
			result = re.search('fileio_', f)
			if result:
				dev = dev_root + g
				params = tcm_fileio.fd_get_params(dev)
				if not params:
					continue
				print "tcm_node --establishdev " + f + "/" + g + " " + str(params)

			# Dump T10 VP Unit Serial for all non Target_Core_Mod/pSCSI objects
			result = re.search('pscsi_', f)
			if not result:
				unit_serial_file = dev_root + g + "/wwn/vpd_unit_serial"
				p = os.open(unit_serial_file, 0)
				value = os.read(p, 512)
				off = value.index('Number: ')
				off += 8 # Skip over "Number: " 
				unit_serial = value[off:]
				# Note that this will handle read, parse and set any PR APTPL metadata
				print "tcm_node --setunitserialwithmd " + f + "/" + g + " " + unit_serial.rstrip()
				os.close(p)

			# Dump ALUA Logical Unit Group
			lu_gp_file = dev_root + g + "/alua_lu_gp"
			p = os.open(lu_gp_file, 0)
			value = os.read(p, 512)
			os.close(p)
			if value:
				lu_gp_tmp = value.split('\n')
				lu_gp_out = lu_gp_tmp[0]
				off = lu_gp_out.index('Alias: ')
				off += 7 # Skip over "Alias: "
				lu_gp_name = lu_gp_out[off:]
				# Only need to dump if storage object is NOT part of
				# the 'default_lu_gp'
				if not re.search(lu_gp_name, 'default_lu_gp'):
					print "echo " + lu_gp_name + " > " + lu_gp_file

			# Loop through ALUA Target Port Groups 
			if os.path.isdir(dev_root + g + "/alua/") == True:
				print "#### ALUA Target Port Groups"
				for tg_pt_gp in os.listdir(dev_root + g + "/alua/"):
					tg_pt_gp_id_file = dev_root + g + "/alua/" + tg_pt_gp + "/tg_pt_gp_id"
					p = os.open(tg_pt_gp_id_file, 0)
					value = os.read(p, 8)
					os.close(p)
					if not value:
						continue
					print "tcm_node --addaluatpgwithmd " + f + "/" + g + " " + tg_pt_gp + " " + value.rstrip()
					# Dump the ALUA types
					tg_pt_gp_type_file = dev_root + g + "/alua/" + tg_pt_gp + "/alua_access_type"
					p = os.open(tg_pt_gp_type_file, 0)
					value = os.read(p, 32)
					os.close(p)
					if value:
						value = value.rstrip()
						alua_type = 0

						if re.search('Implict and Explict', value):
							alua_type = 3
						elif re.search('Explict', value):
							alua_type = 2
						elif re.search('Implict', value):
							alua_type = 1

						print "echo " + str(alua_type) + " > " + tg_pt_gp_type_file

					# Dump the preferred bit
					tg_pt_gp_pref_file = dev_root + g + "/alua/" + tg_pt_gp + "/preferred"
					p = os.open(tg_pt_gp_pref_file, 0)
					value = os.read(p, 8)
					os.close(p)
					if value:
						print "echo " + value.rstrip() + " > " + tg_pt_gp_pref_file
					# Dump the Active/NonOptimized Delay
					tg_pt_gp_nonop_delay_file = dev_root + g + "/alua/" + tg_pt_gp + "/nonop_delay_msecs"
					p = os.open(tg_pt_gp_nonop_delay_file, 0)
					value = os.read(p, 8)
					os.close(p)
					if value:
						print "echo " + value.rstrip() + " > " + tg_pt_gp_nonop_delay_file
					# Dump the Transition Delay
					tg_pt_gp_trans_delay_file = dev_root + g + "/alua/" + tg_pt_gp + "/trans_delay_msecs"
					p = os.open(tg_pt_gp_trans_delay_file, 0)
					value = os.read(p, 8)
					os.close(p)
					if value:
						print "echo " + value.rstrip() + " > " + tg_pt_gp_trans_delay_file

			# Dump device attributes
			print "#### Attributes for " + dev_root + g
			dev_attrib_root = dev_root + g + "/attrib/"
			for h in os.listdir(dev_attrib_root):
				# The hw_* prefixed attributes are RO
				if h == "hw_queue_depth":
					continue
				if h == "hw_max_sectors":
					continue
				if h == "hw_block_size":
					continue
				# Do not change block-size for target_core_mod/pSCSI
				if h == "block_size":
					result = re.search('pscsi_', f)
					if result:
						continue

				attrib_file = dev_attrib_root + h
				p = os.open(attrib_file, 0)
				value = os.read(p, 8)
				print "echo " + value.rstrip() + " > " + attrib_file
				os.close(p)

			# Dump snapshot attributes
			snap_attrib_root = dev_root + g + "/snap/"
			if (os.path.isdir(snap_attrib_root) == False):
				continue

			snap_enabled = 0
			enabled_attr_file = snap_attrib_root + "enabled"
			p = open(enabled_attr_file, 'rU')
			if not p:
				continue
			value = p.read()
			enabled = value.rstrip()
			p.close()
			if enabled != "1":
				continue

			snap_enabled = 1
			print "#### Snapshot Attributes for " + dev_root + g
			for s in os.listdir(snap_attrib_root):
				if s == "pid":
					continue
				if s == "usage":
					continue
				if s == "enabled":
					continue

				attrib_file = snap_attrib_root + s
				p = open(attrib_file, 'rU')
				value = p.read()
				p.close()
				attr_val = value.rstrip()
				print "echo " + attr_val + " > " + attrib_file

			if snap_enabled == 1:
				print "tcm_node --lvsnapstart " + f + "/" + g


	return

def tcm_backup_to_file(option, opt_str, value, parser):
	datetime = str(value)
	
	if not os.path.isdir(tcm_root):
		print "Unable to access tcm_root: " + tcm_root
		sys.exit(1)

	backup_dir = "/etc/target/backup"
	if not os.path.isdir(backup_dir):
		op = "mkdir " + backup_dir
		ret = os.system(op)
		if ret:
			print "Unable to open backup_dir"
			sys.exit(1)

	op = "tcm_dump --stdout"
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to dump Target_Core_Mod/ConfigFS running state"
		sys.exit(0)

	print "Making backup of Target_Core_Mod/ConfigFS with timestamp: " + datetime 
	backup_file = backup_dir + "/tcm_backup-" + datetime + ".sh"
	if os.path.isfile(backup_file):
		print "Target_Core_Mod backup_file: " + backup_file + "already exists, exiting"
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

def tcm_full_backup(option, opt_str, value, parser):
	overwrite = str(value)

	now = datetime.datetime.now()
	tmp = str(now)
	tmp2 = tmp.split(' ')
	timestamp = tmp2[0] + "_" + tmp2[1]

	tcm_file = "/etc/target/tcm_start.sh"
	lio_file = "/etc/target/lio_start.sh"
	lio_active = 0
	
	if os.path.isdir("/sys/kernel/config/target/iscsi"):
		lio_file_new = lio_dump.lio_backup_to_file(None, None, timestamp, None)
		if not lio_file_new:
			sys.exit(1)
		lio_active = 1
		print "Generated LIO-Target config: " + lio_file_new


	tcm_file_new = tcm_backup_to_file(None, None, timestamp, None)
	if not tcm_file_new:
		sys.exit(1)

	print "Generated Target_Core_Mod config: " + tcm_file_new
	
	if overwrite != "1":
		print "Not updating default config"
		return

	if lio_active:
		ret = shutil.copyfile(lio_file_new, lio_file)
		if ret:
			print "Unable to copy " + lio_file_new
			sys.exit(1)
		print "Successfully updated default config " + lio_file

	ret = shutil.copyfile(tcm_file_new, tcm_file)
	if ret:
		print "Unable to copy " + tcm_file_new
		sys.exit(1)

	print "Successfully updated default config " + tcm_file 
	return

def tcm_overwrite_default(option, opt_str, value, parser):

	input = raw_input("Are you sure you want to overwrite the default configuration? Type 'yes': ")
	if input != "yes":
		sys.exit(0)

	val = "1"
	tcm_full_backup(None, None, val, None)
	return

def main():
	
	parser = OptionParser()
	parser.add_option("--b","--backup", action="callback", callback=tcm_full_backup, nargs=1,
		type="string", dest="OVERWRITE", help="Do backup of TCM and storage fabric modules, and optionally overwrite default config data")
	parser.add_option("--o","--overwrite", action="callback", callback=tcm_overwrite_default, nargs=0,
		help="Overwrite default config data of TCM and storage fabric modules")
	parser.add_option("--s","--stdout", action="callback", callback=tcm_dump_configfs, nargs=0,
		help="Dump running Target_Core_Mod/ConfigFS syntax to STDOUT")
	parser.add_option("--t", "--tofile", action="callback", callback=tcm_backup_to_file, nargs=1,
		type="string", dest="DATE_TIME", help="Backup running Target_Core_Mod/ConfigFS syntax to /etc/target/backup/tcm_backup-<DATE_TIME>.sh")

	(options, args) = parser.parse_args()
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)
	elif not re.search('--', sys.argv[1]):
		print "Unknown CLI option: " + sys.argv[1]
		sys.exit(1)

if __name__ == "__main__":
        main()
