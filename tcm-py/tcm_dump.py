#!/usr/bin/python

import os
import subprocess as sub
from subprocess import Popen, PIPE
import string
import re
from optparse import OptionParser

import tcm_pscsi
import tcm_iblock
import tcm_ramdisk
import tcm_fileio

tcm_root = "/sys/kernel/config/target/core"

def tcm_dump_hba_devices():
	return	

def tcm_dump_configfs():

	print "modprobe target_core_mod"

	# Loop through ALUA Logical Unit and Target Port groups
	# Note that the 'default_lu_gp' and 'default_tg_pt_gp' are automatically
	# created when target_core_mod is loaded.
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

	print "#### ALUA Target Port Groups"
	for tg_pt_gp in os.listdir(tcm_root + "/alua/tg_pt_gps"):
		if tg_pt_gp == "default_tg_pt_gp":
			continue

		print "mkdir -p " + tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp
		tg_pt_gp_id_file = tcm_root + "/alua/tg_pt_gps/" + tg_pt_gp + "/tg_pt_gp_id"
		p = os.open(tg_pt_gp_id_file, 0)
		value = os.read(p, 8)
		os.close(p)
		if not value:
			continue
		print "echo " + value.rstrip() + " > " + tg_pt_gp_id_file

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
				print "tcm_node --createdev " + f + "/" + g + " " + str(params)
			result = re.search('iblock_', f)
			if result:
				dev = dev_root + g
				params = tcm_iblock.iblock_get_params(dev)
				if not params:
					continue
				print "tcm_node --createdev " + f + "/" + g + " " + str(params)
			result = re.search('rd_dr_', f)
			if result:
				dev = dev_root + g
				params = tcm_ramdisk.rd_get_params(dev)	
				if not params:
					continue
				print "tcm_node --createdev " + f + "/" + g + " " + str(params)
			result = re.search('rd_mcp_', f)
			if result:
				dev = dev_root + g
				params = tcm_ramdisk.rd_get_params(dev)
				if not params:
					continue
				print "tcm_node --createdev " + f + "/" + g + " " + str(params)
			result = re.search('fileio_', f)
			if result:
				dev = dev_root + g
				params = tcm_fileio.fd_get_params(dev)
				if not params:
					continue
				print "tcm_node --createdev " + f + "/" + g + " " + str(params)

			# Dump T10 VP Unit Serial for all non Target_Core_Mod/pSCSI objects
			result = re.search('pscsi_', f)
			if not result:
				unit_serial_file = dev_root + g + "/wwn/vpd_unit_serial"
				p = os.open(unit_serial_file, 0)
				value = os.read(p, 512)
				off = value.index('Number: ')
				off += 8 # Skip over "Number: " 
				unit_serial = value[off:]
				print "echo " + unit_serial.rstrip() + " > " + unit_serial_file
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

	return

tcm_dump_configfs()
