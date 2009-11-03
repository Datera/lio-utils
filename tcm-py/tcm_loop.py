#!/usr/bin/python
import os, sys
import subprocess as sub
import string
import re
from optparse import OptionParser

tcm_loop_root = "/sys/kernel/config/target/loopback/"
tcm_root = "/sys/kernel/config/target/core"

def tcm_generate_naa_sas_address():
	# Use NAA IEEE Registered Designator prefix, and append WWN UUID below
	sas_address = "naa.6001405"

	uuidgen_op = 'uuidgen'
	p = sub.Popen(uuidgen_op, shell=True, stdout=sub.PIPE).stdout
	uuid = p.readline()
	p.close()

	if not uuid:
		print "Unable to generate UUID using uuidgen, continuing anyway"
		sys.exit(1)

	val = uuid.rstrip();
	sas_address += val[:10]
	sas_address = sas_address.replace('-','')

	return sas_address

def tcm_loop_add_target_www(option, opt_str, value, parser):
	sas_target_address = tcm_generate_naa_sas_address();
	sas_target_tpgt = str(value)
	return

def tcm_loop_del_target_wwn(option, opt_str, value, parser):
	sas_target_address = str(value[0])
	sas_target_tpgt = str(value[1])

	tpgt_dir = tcm_loop_root + sas_target_address + "/tpgt_" + sas_target_tpgt
	delete_op = "rmdir " + tpgt_dir
	ret = os.system(delete_op)
	if ret:
		print "Unable to remove configfs group: " + tpgt_dir

	naa_dir = tcm_loop_root + sas_target_address
	delete_op = "rmdir " + naa_dir
	ret = os.system(delete_op)
	if ret:
		print "Unable to remove configfs group: " + naa_dir
	else:
		print "Successfully removed NAA based SAS Target Address: " + naa_dir + "/" + tpgt_dir

	return

def tcm_loop_create_nexus(option, opt_str, value, parser):
	sas_target_address = tcm_generate_naa_sas_address();	
	sas_target_tpgt = str(value)
	sas_initiator_address = tcm_generate_naa_sas_address();

	create_op = "mkdir -p " + tcm_loop_root + sas_target_address + "/tpgt_" + sas_target_tpgt + "/nexus/" + sas_initiator_address
	ret = os.system(create_op)
	if ret:
		print "Unable to create virtual SAS I_T Nexus: " + create_op
		sys.exit(1)
	else:
		print "Successfully created virtual SCSI I_T Nexus between TCM and Linux/SCSI HBA"
		print "  SAS Target Address: " + sas_target_address
		print "  SAS Initiator Address " + sas_initiator_address

	return

def tcm_loop_delete_nexus(option, opt_str, value, parser):
	sas_target_address = str(value[0])
	sas_target_tpgt = str(value[1])
	sas_initiator_address = "";

	nexus_dir = tcm_loop_root + sas_target_address + "/tpgt_" + sas_target_tpgt + "/nexus/"
	for nexus in os.listdir(nexus_dir):
		delete_op = "rmdir " + nexus_dir + "/" + nexus

		ret = os.system(delete_op)
		if ret:
			print "Unable to delete virtual SCSI I_T Nexus between TCM and Linux/SCSI HBA"
			sys.exit(1)

		print "Successfully deleted virtual SCSI I_T Nexus between TCM and Linux/SCSI HBA"
		break

	return

def tcm_loop_addlun(option, opt_str, value, parser):
	sas_target_address = str(value[0])
	sas_target_tpgt = str(value[1])
	sas_target_lun = str(value[2])

	mkdir_op = "mkdir -p " + tcm_loop_root + sas_target_address + "/tpgt_" + sas_target_tpgt + "/lun/lun_" + sas_target_lun	
	ret = os.system(mkdir_op)
	if ret:
		print "Unable to create SAS Target Port LUN configfs group: " + mkdir_op
		sys.exit(1)

	tcm_obj = str(value[3]);
	port_src = tcm_root + "/" + tcm_obj
	port_dst = tcm_loop_root + sas_target_address + "/tpgt_" + sas_target_tpgt + "/lun/lun_" + sas_target_lun + "/virtual_scsi_port"

	link_op = "ln -s " + port_src + " " + port_dst
	ret = os.system(link_op)
	if not ret:
		print "Successfully created SAS Target Port to local virtual SCSI Logical Unit"
		# FIXME Add tcm_loop_alua_check_secondary_md()
		# FIXME Add tcm_loop_alua_set_secondary_write_md()
	else:
		print "Unable to create SAS Target Port to local virtual SCSI Logical Unit"
		sys.exit(1)

	return

def tcm_loop_dellun(option, opt_str, value, parser):
	sas_target_address = str(value[0])
	sas_target_tpgt = str(value[1])
	sas_target_lun = str(value[2])

	port_link = ""

	lun_dir = tcm_loop_root + sas_target_address + "/tpgt_" + sas_target_tpgt + "/lun/lun_" + sas_target_lun
	for port in os.listdir(lun_dir):
		port_link = lun_dir + "/" + port

	unlink_op = "unlink " + port_link
	ret = os.system(unlink_op)
	if ret:
		print "Unable to unlink port for virtual SCSI Logical Unit: " + port
		sys.exit(1)

	rmdir_op = "rmdir " + tcm_loop_root + sas_target_address + "/tpgt_" + sas_target_tpgt + "/lun/lun_" + sas_target_lun
	ret = os.system(rmdir_op)
	if ret:
		print "Unable to rmdir configfs group for virtual SCSI Logical Unit: " + port
		sys.exit(1)
	else:
		print "Succesfully deleted local virtual SCSI Logical Unit from SAS Target Port"
		
	return

def tcm_loop_unload(option, opt_str, value, parser):

	for sas_target_naa in os.listdir(tcm_loop_root):
		print "sas_target_naa: " + sas_target_naa

		if os.path.isfile(tcm_loop_root + sas_target_naa) == True:
			continue

		tpgt_dir = tcm_loop_root + sas_target_naa + "/"
		for sas_target_tpgt in os.listdir(tpgt_dir):

			print "sas_target_tpgt: " + sas_target_tpgt

			lun_dir = tpgt_dir + "/" + sas_target_tpgt + "/lun/"
			for sas_target_lun in os.listdir(lun_dir):

				print "sas_target_lun: " + sas_target_lun
				tpgt = sas_target_tpgt[5:]
				lun = sas_target_lun[4:]
				vals = [sas_target_naa, tpgt, lun]
				tcm_loop_dellun(None, None, vals, None)

			tpgt = sas_target_tpgt[5:]
			vals = [sas_target_naa, tpgt]

			tcm_loop_delete_nexus(None, None, vals, None)

			tcm_loop_del_target_wwn(None, None, vals, None)

	rmdir_op = "rmdir " + tcm_loop_root
	ret = os.system(rmdir_op)
	if ret:
		print "Unable to remove tcm_loop_root configfs group: " + tcm_loop_root
		sys.exit(1)

	rmmod_op = "rmmod tcm_loop"
	ret = os.system(rmmod_op)
	if ret:
		print "Unable to remove tcm_loop kernel module"
		sys.exit(1)

	print "Successfully removed tcm_loop kernel module"
	return

def main():

	parser = OptionParser()
	parser.add_option("--delwwn", action="callback", callback=tcm_loop_del_target_wwn, nargs=2,
		type="string", dest="NAA_TARGET_WWN TPGT", help="Delete a SAS Virtual HBA by WWN+TPGT")
	parser.add_option("--createnexus", action="callback", callback=tcm_loop_create_nexus, nargs=1,
		type="string", dest="TPGT", help="Create a virtual SAS I_T Nexus using generated NAA WWN for SAS Address.  This will create a new Linux/SCSI Host Bus Adapter for the I_T Nexus");
	parser.add_option("--delnexus", action="callback", callback=tcm_loop_delete_nexus, nargs=2,
		type="string", dest="NAA_TARGET_WWN TPGT", help="Delete a virtual SAS I_T Nexus");
	parser.add_option("--addlun", action="callback", callback=tcm_loop_addlun, nargs=4,
		type="string", dest="NAA_TARGET_WWN TPGT LUN HBA/DEV", help="Add virtual SCSI Linux to NAA Target/Initiator Sas Addresses")
	parser.add_option("--dellun", action="callback", callback=tcm_loop_dellun, nargs=3,
		type="string", dest="NAA_TARGET_WWN TPGT LUN", help="Delete Target SAS Port to virtual SCSI Logical unit mapping")
	parser.add_option("--unload", action="callback", callback=tcm_loop_unload, nargs=0,
		help="Shutdown all virtual SCSI LUNs and unload tcm_loop")
	
	(options, args) = parser.parse_args()
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)
	elif not re.search('--', sys.argv[1]):
		lio_err("Unknown CLI option: " + sys.argv[1])

if __name__ == "__main__":
	main()
