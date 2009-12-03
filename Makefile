include MCONFIG_ALL
CWD=$(shell pwd)

default:: all

all:
	cd tcm-py ; python setup.py build
	cd lio-py ; python setup.py build
	-if test -d tools; then make -C tools; fi;
ifeq ($(SNMP_FEATURE), 1)
	-if test -d mib-modules; then make -C mib-modules; fi;
endif

user_rpms:
	-if test -d tools; then make -C tools; fi;
	./autoconfig make_target_user_rpm
ifeq ($(SNMP_FEATURE), 1)
	-if test -d mib-modules; then make -C mib-modules; fi;
	./autoconfig make_mibs_rpm
endif

conf_install:
	if [ ! -d $(DESTDIR)/etc/target ]; then		\
		mkdir -p $(DESTDIR)/etc/target;		\
	fi
	if [ ! -f $(DESTDIR)/etc/target/tcm_start.sh ]; then	\
		install -m 0755 conf/tcm_start.default $(DESTDIR)/etc/target/tcm_start.sh;	\
	fi
	if [ ! -f $(DESTDIR)/etc/target/lio_start.sh ]; then	\
		install -m 0755 conf/lio_start.default $(DESTDIR)/etc/target/lio_start.sh;	\
	fi						\

initd_install:
	if [ ! -d $(DESTDIR)/etc/init.d ]; then 	\
		mkdir -p $(DESTDIR)/etc/init.d;		\
	fi
	install -m 0755 scripts/rc.target $(DESTDIR)/etc/init.d/target	

install: all initd_install conf_install
	cd tcm-py ; python setup.py install ; sh install.sh
	cd lio-py ; python setup.py install ; sh install.sh
	-if test -d tools; then make -C tools install; fi
ifeq ($(SNMP_FEATURE), 1)
	-if test -d mib-modules; then make -C mib-modules install; fi
endif

deinstall:
	cd tcm-py ; sh uninstall.sh
	cd lio-py ; sh uninstall.sh

clean:
	cd tcm-py ; python setup.py clean ; rm -rf build
	cd lio-py ; python setup.py clean ; rm -rf build
	rm -rf build
	-if test -d tools; then make -C tools clean; fi;
ifeq ($(SNMP_FEATURE), 1)
	-if test -d mib-modules; then make -C mib-modules clean; fi;
endif
