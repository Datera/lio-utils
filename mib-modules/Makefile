#CWD=$(shell pwd)
#AUTOCONFIG=$(CWD)/../autoconfig --write-to-file --current-directory=$(CWD)
#include $(shell $(AUTOCONFIG))

#
# Makefile for dynamically loadable module for the Target Mib
#
TOPDIR		= /usr
MIBDIR		= $(TOPDIR)/share/snmp/mibs
DLMODDIR	= $(TOPDIR)/lib/snmp/dlmod
INCLDIR		= $(TOPDIR)/include/net-snmp

MIBS		= LIO-IPS-AUTH-MIB.txt LIO-ISCSI-MIB.txt LIO-SCSI-MIB.txt

TARG		= iscsiTargetMib.so

OBJS		= iscsiTargetMib.o iscsiMib.o scsiMib.o ipsAuthMib.o \
		iscsiAuthData.o

CC		= gcc
CFLAGS		= -I$(INCLDIR) -I$(INCLDIR)/agent -I$(INCLDIR)/agent/mibgroup -shared -fPIC
CFLAGS		+= -I../include -Wall -Werror
#CFLAGS		+=$(AUTO_CFLAGS)

LD		= gcc -shared

INSTALL		= install

all: $(TARG)

%.o: %.c *.h 
	$(CC) $(CFLAGS) -o $@ -c $<

$(TARG): $(OBJS)
	$(LD) -o $@ $(OBJS)

clean:
	rm -f $(OBJS) $(TARG)

install: all
	mkdir -p $(DESTDIR)/$(DLMODDIR)
	$(INSTALL) $(TARG) $(DESTDIR)/$(DLMODDIR)
	mkdir -p $(DESTDIR)/$(MIBDIR)
	(cd mibs ; $(INSTALL) -m 644 $(MIBS) $(DESTDIR)/$(MIBDIR))
