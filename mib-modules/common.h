/*
 * Copyright (c) 2006 SBE, Inc.
 * Copyright (c) 2009 Linux-iSCSI.org
 */

#ifndef COMMON_H
#define COMMON_H

#ifdef NETSNMP_CACHE_HANDLER_H
#define HAVE_CACHE_HANDLER	1
#endif
#ifdef CACHE_H
/* v5.1 */
#define HAVE_CACHE_HANDLER	1
#endif

#if !HAVE_CACHE_HANDLER
typedef void * netsnmp_cache;
#endif

#define OID_LIO			1,3,6,1,4,1,1055
#define OID_LIO_ISCSI_PRODUCT	OID_LIO,10
#define OID_LIO_ISCSI_MIB	OID_LIO_ISCSI_PRODUCT,1 
#define OID_LIO_IPS_AUTH_MIB	OID_LIO_ISCSI_PRODUCT,2 
#define OID_LIO_SCSI_MIB	OID_LIO_ISCSI_PRODUCT,3 

#endif /* COMMON_H */
