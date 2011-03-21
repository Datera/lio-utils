#!/usr/bin/python
import os, sys
import subprocess as sub
import string
import re
import datetime, time
import smtplib
from optparse import OptionParser

lvcreate_bin = ""
lvdisplay_bin = ""
lvremove_bin = ""
vgdisplay_bin = ""

smtp_server = "localhost"
snap_group = ""
snap_enabled = 0
default_snap_contact = "root@localhost"
snap_contact = "" # Email address contact for messages
default_snap_size = "100M" # Default snapshot volume (block log) size 
snap_size = ""
snap_permissions = "rw" # Default READ-WRITE snapshots
snap_avgr = 0
default_snap_usage_warn = 75 # Default snapshot usage warning
snap_usage_warn = 0
snap_vgs_usage = 0
default_snap_vgs_usage_warn = 80 # Default snapshot vg usage warning
snap_vgs_usage_warn = 0
default_max_snap_count = 10
max_snap_count = 0
default_check_intrvl_sec=60 # Every 1 minute
check_intrvl_sec = 0
default_create_intrvl_sec = 43200 # Every 12 hours
create_intrvl_sec = 0

snap_debug = 0
cfs_attr_debug = 0

def printdbg(str):
	if snap_debug == 1:
		print str

def printattr(str):
	if cfs_attr_debug == 1:
		print str

def get_average(values):
	return sum(values, 0.0) / len(values)

def get_lvcreate_path():
	global lvcreate_bin;

	op = "which lvcreate"
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to locate lvcreate in PATH"
		sys.exit(1)
	
	tmp = p.read();
	if not tmp:
		print "Unable to locate lvcreate in PATH"
		sys.exit(1)

	lvcreate_bin = tmp.rstrip()
	printattr("lvcreate_bin: " + lvcreate_bin)
	p.close()	

def get_lvdisplay_path():
	global lvdisplay_bin

	op = "which lvdisplay"
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to locate lvdisplay in PATH"
		sys.exit(1)

	tmp = p.read();
	if not tmp:
		print "Unable to locate lvdisplay in PATH"
		sys.exit(1)

	lvdisplay_bin = tmp.rstrip()
	printattr("lvdisplay_bin: " + lvdisplay_bin)
	p.close()

def get_lvremove_bin():
	global lvremove_bin

	op = "which lvremove"
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to locate lvremove in PATH"
		sys.exit(1)

	tmp = p.read();
	if not tmp:
		print "Unable to locate lvremove in PATH"
		sys.exit(1)

	lvremove_bin = tmp.rstrip()
	printattr("lvremove_bin: " + lvremove_bin)
	p.close()

def get_vgdisplay_bin():
        global vgdisplay_bin

        op = "which vgdisplay"
        p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
        if not p:
                print "Unable to locate vgdisplay in PATH"
                sys.exit(1)

        tmp = p.read();
        if not tmp:
                print "Unable to locate vgdisplay in PATH"
                sys.exit(1)

        vgdisplay_bin = tmp.rstrip()
	printattr("vgdisplay_bin: " + vgdisplay_bin)
        p.close()

def get_cfs_udev_path(cfs_path):
	
	udev_path_attr = cfs_path + "/udev_path"
	p = open(udev_path_attr, 'rU')
	if not p:
		print "Unable to open udev_path: " + udev_path_attr
		return
	val = p.read()
	if not val:
		print "Unable to read udev_path: " + udev_path_attr
		p.close()
		return

	udev_path = val.rstrip()	
	p.close()
#	print "Located udev_path: " + udev_path + " for " + cfs_path
	return udev_path

def get_cfs_snap_lvgroup(cfs_path):
	global snap_group

	snap_attr = cfs_path + "/snap/lv_group"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return
	val = p.read()
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	snap_group = val.rstrip()
	printattr("Detected snap_group: " + snap_group + " for " + cfs_path)
	return snap_group

def get_cfs_snap_enabled(cfs_path):
	global snap_enabled;

	snap_attr = cfs_path + "/snap/enabled"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return 
	val = p.read()
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	snap_enabled = int(val);
	printattr("Detected snap_enabled: " + str(snap_enabled) + " for " + cfs_path)
	return snap_enabled

def get_cfs_snap_contact(cfs_path):
	global snap_contact;

	snap_attr = cfs_path + "/snap/contact"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return
	val = p.read(128)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	snap_contact = val.rstrip();
	printattr("Detected snap contact: " + snap_contact + " for " + cfs_path)
	return snap_contact	

def get_cfs_snap_size(cfs_path):
	global snap_size;

	snap_attr = cfs_path + "/snap/lvc_size"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return
	val = p.read(64)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	snap_size = val.rstrip();
	printattr("Detected snap_size: " + snap_size + " for " + cfs_path)
	return snap_size	

def get_cfs_snap_permissions(cfs_path):
	global snap_permissions

	snap_attr = cfs_path + "/snap/permissions"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return
	val = p.read(8)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	if int(val) == 1:
		snap_permissions = "rw"
	else:
		snap_permissions = "r"

	printattr("Detected snap_permisions: " + snap_permissions + " for " + cfs_path)
	return snap_permissions

def get_cfs_max_snapshots(cfs_path):
	global max_snap_count

	snap_attr = cfs_path + "/snap/max_snapshots"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return
	val = p.read(8)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	max_snap_count = int(val)
	printattr("Detected max_snap_count: " + str(max_snap_count) + " for " + cfs_path)
	return max_snap_count

def get_cfs_check_interval(cfs_path):
	global check_intrvl_sec

	snap_attr = cfs_path + "/snap/check_interval"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return
	val = p.read(8)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	check_intrvl_sec = int(val)
	printattr("Detected check_interval: " + str(check_intrvl_sec) + " for " + cfs_path)
	return check_intrvl_sec

def get_cfs_create_interval(cfs_path):
	global create_intrvl_sec

	snap_attr = cfs_path + "/snap/create_interval"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return

	val = p.read(8)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	create_intrvl_sec = int(val)
	printattr("Detected create_interval: " + str(create_intrvl_sec) + " for " + cfs_path)
	return create_intrvl_sec

def get_cfs_usage_warn(cfs_path):
	global snap_usage_warn

	snap_attr = cfs_path + "/snap/usage_warn"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return

	val = p.read(8)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	snap_usage_warn = int(val)
	printattr("Detected snap usage_warn: " + str(snap_usage_warn) + " for " + cfs_path)
	return snap_usage_warn

def get_cfs_vgs_usage_warn(cfs_path):
	global snap_vgs_usage_warn

	snap_attr = cfs_path + "/snap/vgs_usage_warn"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return

	val = p.read(8)
	if not val:
		print "Unable to read snap_attr: " + snap_attr
		p.close()
		return

	p.close()
	snap_vgs_usage_warn = int(val)
	printattr("Detected snap vgs_usage_warn: " + str(snap_vgs_usage_warn) + " for " + cfs_path)
	return snap_vgs_usage_warn

def get_cfs_snap_attrs(cfs_path):

	get_cfs_snap_lvgroup(cfs_path)
	get_cfs_snap_enabled(cfs_path)
	get_cfs_snap_contact(cfs_path)
	get_cfs_snap_size(cfs_path)
	get_cfs_snap_permissions(cfs_path)	
	get_cfs_max_snapshots(cfs_path)
	get_cfs_check_interval(cfs_path)
	get_cfs_create_interval(cfs_path)
	get_cfs_usage_warn(cfs_path)
	get_cfs_vgs_usage_warn(cfs_path)

def get_cfs_snap_pid(cfs_path):
	snap_attr = cfs_path + "/snap/pid"
	p = open(snap_attr, 'rU')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return
	val = p.read()
	pid = val.rstrip()
	p.close()

	return pid

def set_cfs_snap_pid(cfs_path):
	pid = os.getpid()

	snap_attr = cfs_path + "/snap/pid"
	p = open(snap_attr, 'w')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return 1
	ret = p.write(str(pid))
	if ret:
		print "Unable to write to snap_attr: " + snap_attr
		return 1

	p.close()

def set_cfs_snap_usage(cfs_path, usage):

	snap_attr = cfs_path + "/snap/usage"
	p = open(snap_attr, 'w')
	if not p:
		print "Unable to open snap_attr: " + snap_attr
		return 1
	ret = p.write(str(usage))
	if ret:
		print "Unable to write to snap_attr: " + snap_attr
		return 1

	p.close()

def snap_lvcreate(lvm_path):

	now = datetime.datetime.now()
	tmp = str(now)
	tmp2 = tmp.split(' ')
	time = tmp2[1]
	time = time.replace(':','_')
	timestamp = tmp2[0] + "-" + time

	snap_name = "snap-" + timestamp
	op = lvcreate_bin + " --snapshot --size " + snap_size + " --permission " + snap_permissions + " --name " + snap_name + " " + lvm_path
#	print "snap op: " + op
	ret = os.system(op)
	if ret:
		print "lvcreate op failed: " + op
		return 1

	printdbg("Successfully created LVM snapshot: " + snap_name)

def snap_lvremove(snap_path):

	# FIXME: remove all active fabric exports and remove tcm storage object

	op = lvremove_bin + " -f " + snap_path
	ret = os.system(op)
	if ret:
		print "Unable to lvremove: " + snap_path
		return 1

def snap_set_cfs_attrib(cfs_path, attr, val):
	
	attr_file = cfs_path + "/snap/" + attr
	p = open(attr_file, 'w')
	if not p:
		print "Unable to open snap attr_file: " + attr_file
		return 1

	ret = p.write(val)	
	if ret:
		print "Unable to write snap attr_file: " + attr_file
		p.close()
		return 1

	print "Set attribute: " + attr + "=" + val
	p.close()

def snap_get_seconds_from_str(timestr):
	secs = 0	
	type = timestr[-1:]
	type = type.lower()
	val = int(timestr[:-1])
	if type == "m":
		secs = (val * 60)
	elif type == "h":
		secs = (val * 60) * 60
	elif type == "d":
		secs = ((val * 60) * 60) * 24
	else:
		print "Timestring type does not contain m=minute,h=hour or d=day"
		return 

	return secs

def snap_set_cfs_defaults(cfs_path, max_snapshots, lv_size, snap_interval):

	enabled_file = cfs_path + "/snap/enabled"
	p = open(enabled_file, 'rU')
	if not p:
		print "Unable to open enabled_file: " + enabled_file
		return 1

	val = p.read()
	if not val:
		p.close()
		print "Unable to read from enabled_file: " + enabled_file
		return 1
		
	enabled = int(val)
	p.close()

	if enabled == 1:
		print "snapshot already enabled for: " + cfs_path
		return 1

	lvm_path = get_cfs_udev_path(cfs_path)
	if not lvm_path:
		print "Unable to locate UDEV path for " + cfs_path
		return 1

	get_lvdisplay_path()
	op = lvdisplay_bin + " --colon " + lvm_path
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
        if not p:
                print "Unable to find oldest snapshot from: " + lvm_path
                return 1

        lvm_line = p.readline()
	if not lvm_line:
		print "Unable to locate active LVM from udev_path: " + lvm_path
		p.close()
		return 1

	out = lvm_line.split(':')
	volume_group = out[1]
	p.close()

	tmp_create_intrvl_sec = snap_get_seconds_from_str(snap_interval)
	if not tmp_create_intrvl_sec:
		return 1

	snap_set_cfs_attrib(cfs_path, "lv_group", volume_group)
	snap_set_cfs_attrib(cfs_path, "lvc_size", lv_size)
	snap_set_cfs_attrib(cfs_path, "max_snapshots", str(max_snapshots))
	snap_set_cfs_attrib(cfs_path, "contact", default_snap_contact)
	snap_set_cfs_attrib(cfs_path, "check_interval", str(default_check_intrvl_sec))
	snap_set_cfs_attrib(cfs_path, "create_interval", str(tmp_create_intrvl_sec))
	snap_set_cfs_attrib(cfs_path, "usage_warn", str(default_snap_usage_warn))
	snap_set_cfs_attrib(cfs_path, "vgs_usage_warn", str(default_snap_vgs_usage_warn))

	print "Successfully set default snapshot attributes for " + cfs_path
	print "You can futher customize these settings with tcm_node --lvsnapattrset and --lvsnapattrshow"

def snap_dump_lvs_info(vg_group, lv_name):
	snap_percent_list = []

	get_vgdisplay_bin()

	op = "lvs --separator=: " + vg_group
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to execute op: " + op
		return 1

	lvs_line = p.readline()
	val = lvs_line.split(':')
	print val[0] + " " + val[1] + " " + val[2] + " " + val[3] + " " + val[4] + " " + val[5] + " " + val[6] + " " + val[7] + " " + val[8].rstrip()
	lvs_line = p.readline()

	while lvs_line:
		val = lvs_line.split(':')
		lvm = val[0].strip()
		origin = val[4]

		# Print snapshot volumes matching LVM origin
		if origin == lv_name:
			percent = val[5]
			percent = percent[:-1]
			snap_percent_list.append(float(percent))
			print val[0] + " " + val[1] + " " + val[2] + " " + val[3] + " " + val[4] + " " + val[5] + " " + val[6] + " " + val[7] + " " + val[8].rstrip()
		elif lvm == lv_name:
			print "Origin LV: " + val[0].lstrip() + " " + val[1] + " " + val[2] + " " + val[3] + " " + val[4]

		lvs_line = p.readline()

	p.close()
	print "Total snapshot usage percentage for LV: " + str(get_average(snap_percent_list))
	check_vgs_extents_usage()
	print "Total volume group usage percentage: " + str(float(snap_vgs_usage))

def snap_check_status(lvm_path, cfs_path):
	global snap_avgr

	active_snaps = 0
	found_snap = 0
	snap_highest_usage = -1
	snap_highest_path = ""
	snap_lowest_usage = 100
	snap_lowest_path = ""
	snap_list = []
	snap_status_list = []
	snap_average_list = []

	op = lvdisplay_bin + " " + lvm_path
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to find oldest snapshot from: " + lvm_path
		return 1

	i = 0
	lvm_line = p.readline()
	while lvm_line:
		if not re.search('LV snapshot status', lvm_line):
			lvm_line = p.readline()
			continue
		# Skip to next line containing the list of Linux LVM snapshots..
		lvm_line = p.readline()
		while lvm_line:
#			print "lvm_line: " + lvm_line
			if re.search('LV Status', lvm_line):
				break

			tmp = lvm_line.split(' [')
			if not tmp:
				continue 

			snap_path = tmp[0]
			snap_status = tmp[1]
			snap_status = snap_status[:-2]
#			print "snap_path: " + snap_path.strip()
#			print "snap_status: " + snap_status.strip()
			snap_list.append(snap_path.strip())
			snap_status_list.append(snap_status.strip())
			if snap_status.strip() == "active":
				active_snaps += 1

			i += 1
			lvm_line = p.readline()
		
	p.close()

	total_snaps = len(snap_list)
	printdbg("Detected total snapshot " + str(total_snaps) + " snapshots for LVM: " + lvm_path)
	printdbg("Total snapshots with active status: " + str(active_snaps))

	i = 0
	while i < total_snaps:
		snap_path = snap_list[i]
		snap_status = snap_status_list[i]
		i += 1
		# Remove INACTIVE snapshots that have run out of space
		if snap_status == "INACTIVE":
			snap_lvremove(snap_path)
			continue

		# Determine percentage of snapshot usage 
		op = lvdisplay_bin + " " + snap_path
		q = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
		if not q:
			print "lvdisplay op failed for snap_path: " + snap_path
			continue

		snap_line = q.readline()
		while snap_line:
			if not re.search('Allocated to snapshot', snap_line):
				snap_line = q.readline()
				continue
			
			tmp = snap_line.split('Allocated to snapshot')
			snap_percent_str = tmp[1].rstrip()
			# Strip trailing '%'
			snap_percent_str = snap_percent_str[:-1]
			snap_percent = float(snap_percent_str.rstrip())
			snap_average_list.append(snap_percent)

#			print "snap_path: " + snap_path
#			print "snap_percent: " + str(snap_percent)
			if (snap_percent > snap_highest_usage):
				snap_highest_path = snap_path
				snap_highest_usage = snap_percent

			if (snap_percent < snap_lowest_usage):
				snap_lowest_path = snap_path
				snap_lowest_usage = snap_percent

			break

		q.close()

	if snap_highest_usage == -1:
		print "Unable to locate highest usage snapshot"
		return 1

	snap_avgr = get_average(snap_average_list)
	set_cfs_snap_usage(cfs_path, int(snap_avgr))

	printdbg("Highest snap usage: " + snap_highest_path + " Percent: " + str(snap_highest_usage))
	printdbg("Lowest snap usage: " + snap_lowest_path + " Percent: " + str(snap_lowest_usage))
	printdbg("Snapshot usage average: " + str(snap_avgr) + " ......................")

	if (active_snaps > max_snap_count):
		printdbg("Removing oldest snapshot: " + snap_highest_path)
		snap_lvremove(snap_highest_path)	

def send_snap_usage_warn(cfs_path, warning):

	if not snap_contact:
		print "No snapshot daemon contact email address set!"
		return 1

	source = "snapdaemon@target.linux-iscsi.org"
	sink = [snap_contact]

	sub = "Snapshot message for: " + cfs_path
	out = warning
	message = """\
	From: %s
	To: %s
	Subject: %s

	%s
	""" % (source, ", ".join(sink), sub, out)

	printdbg("Outgoing email message: ")
	printdbg(message)
	
#	s = smtplib.SMTP(smtp_server)
#	s.sendmail(source, sink, message)
#	s.quit()

def check_for_usage_warn(cfs_path):

	if (snap_usage_warn != 0):
		if (snap_avgr >= snap_usage_warn):
			warning = "WARNING: Snapshot on: " + cfs_path + " Snap Average: " + str(snap_avgr) + " exceeds snap_usage_warn: " + str(snap_usage_warn)
			send_snap_usage_warn(cfs_path, warning)

def check_vgs_extents_usage():
	global snap_vgs_usage

	vg_size = 0
	vg_free = 0

	op = vgdisplay_bin + " --colon " + snap_group
	p = sub.Popen(op, shell=True, stdout=sub.PIPE).stdout
	if not p:
		print "Unable to find oldest snapshot from: " + lvm_path
		return 1

	vgs_line = p.readline()
	p.close()
	# Use colon seperated values from vgdisplay
	vals = vgs_line.split(':')
	extents_total = long(vals[13])
#	print "extents_total: " + str(extents_total)
	extents_used = long(vals[14])
#	print "extents_used: " + str(extents_used)
	snap_vgs_usage = ((extents_used*100) / extents_total)
	printdbg("VG Usage average: " + str(snap_vgs_usage))

	if (snap_vgs_usage >= snap_vgs_usage_warn):
		return 1

def check_for_vgs_usage_warn(cfs_path):

	if (snap_vgs_usage_warn != 0):	
		ret = check_vgs_extents_usage()
		if ret:
			warning = "WARNING: Snapshot volume group: " + snap_group + " has reached allocated PE extent usage: " + str(snap_vgs_usage) + " %"
			send_snap_usage_warn(cfs_path, warning)

def main():
	global snap_debug
	count = 0
	cfs_path = ""

	# Get path to LVM userspace CLI
	get_lvcreate_path()
	get_lvdisplay_path()
	get_lvremove_bin()
	get_vgdisplay_bin()

	parser = OptionParser()
	parser.add_option("--p", dest="tcmdevpath", help="target_core_mod configfs device path", nargs=1)
	parser.add_option("--d", action="store_true", dest="snapdebug", help="Enable snap daemon debug messages")	
	(options, args) = parser.parse_args()
	
	if len(sys.argv) == 1:
                parser.print_help()
		sys.exit(1)

	if not options.tcmdevpath:
                parser.print_help()
		sys.exit(1)

	if options.snapdebug:
		snap_debug = 1

	cfs_path = options.tcmdevpath

	# Set out process ID (PID) with configfs
	set_cfs_snap_pid(cfs_path)
	# Read the current snap attribute values from configfs
	get_cfs_snap_attrs(cfs_path)

	lvm_src = get_cfs_udev_path(cfs_path)
	if not lvm_src:
		print "Unable to locate udev_path from target_core_mod"
		sys.exit(1)

	printdbg("Located udev_path for LVM: " + lvm_src)

	while [ 1 ]:
		ret = snap_check_status(lvm_src, cfs_path)
		if ret:
			snap_lvcreate(lvm_src)

		check_for_usage_warn(cfs_path)

		time.sleep(check_intrvl_sec)
		count += check_intrvl_sec

		get_cfs_snap_attrs(cfs_path)

		if (count >= create_intrvl_sec):
			count = 0
			snap_lvcreate(lvm_src)
			check_for_vgs_usage_warn(cfs_path)

if __name__ == "__main__":
	main()

