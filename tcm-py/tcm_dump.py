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

	hba_root = os.listdir(tcm_root)

	print "modprobe target_core_mod"

	# Loop through HBA list
	for f in hba_root:
		if f == "alua":
			continue;
		
#		print "mkdir -p " + tcm_root + "/" + f

		dev_root = tcm_root + "/" + f + "/"
		for g in os.listdir(dev_root):
			if g == "hba_info":
				continue;
			
			# Dump device aka storage object
			print "#### Parameters for TCM subsystem plugin storage object reference"
			print "mkdir -p " + dev_root + g
			result = re.search('pscsi_', f)
			if result:
				dev = dev_root + g
				params = tcm_pscsi.pscsi_get_params(dev)
				print "echo " + params + " > " + dev_root + g + "/control"
			result = re.search('iblock_', f)
			if result:
				dev = dev_root + g
				params = tcm_iblock.iblock_get_params(dev)
				print "echo " + params + " > " + dev_root + g + "/control"
			result = re.search('rd_dr_', f)
			if result:
				dev = dev_root + g
				params = tcm_ramdisk.rd_get_params(dev)	
				print "echo " + params + " > " + dev_root + g + "/control"
			result = re.search('rd_mcp_', f)
			if result:
				dev = dev_root + g
				params = tcm_ramdisk.rd_get_params(dev)
				print "echo " + params + " > " + dev_root + g + "/control"
			result = re.search('fileio_', f)
			if result:
				dev = dev_root + g
				params = tcm_fileio.fd_get_params(dev)
				print "echo " + params + " > " + dev_root + g + "/control"

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

			print "echo 1 > " + dev_root + g + "/enable"

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
