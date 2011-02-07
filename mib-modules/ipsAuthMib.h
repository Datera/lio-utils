/*
 * Copyright (c) 2006 SBE, Inc.
 * Copyright (c) 2009-2011 Linux-iSCSI.org
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

/* 
 * ipsAuthMibModule Definitions
 */
#ifndef IPSAUTHMIB_H
#define IPSAUTHMIB_H

#define AUTH_INST_INDEX		1
#define AUTH_ID_NAME_INDEX	1

/*
 * Instance Attributes Table
 */
void initialize_table_ipsAuthInstAttr(void);
Netsnmp_Node_Handler ipsAuthInstAttr_handler;
Netsnmp_First_Data_Point ipsAuthInstAttr_get_first_data_point;
Netsnmp_Next_Data_Point ipsAuthInstAttr_get_next_data_point;
int ipsAuthInstAttr_load(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_IPSAUTHINSTINDEX		1
#define COLUMN_IPSAUTHINSTDESCR		2
#define COLUMN_IPSAUTHINSTSTORAGETYPE	3

/* Data structure for row entry */
struct ipsAuthInstAttr_entry {
    u_long	ipsAuthInstIndex;
    char	ipsAuthInstDescr[AUTH_MAX_NAME_LEN];
    long	ipsAuthInstStorageType;
    struct ipsAuthInstAttr_entry *next;
};

/*
 * User Identity Attributes Table
 */
void initialize_table_ipsAuthIdentAttr(void);
Netsnmp_Node_Handler ipsAuthIdentAttr_handler;
Netsnmp_First_Data_Point ipsAuthIdentAttr_get_first_data_point;
Netsnmp_Next_Data_Point ipsAuthIdentAttr_get_next_data_point;
int ipsAuthIdentAttr_load(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_IPSAUTHIDENTINDEX		1
#define COLUMN_IPSAUTHIDENTDESCRIPTION		2
#define COLUMN_IPSAUTHIDENTROWSTATUS		3
#define COLUMN_IPSAUTHIDENTSTORAGETYPE		4

/* Data structure for row entry */
struct ipsAuthIdentAttr_entry {
    u_long	ipsAuthInstIndex;
    u_long	ipsAuthIdentIndex;
    char	ipsAuthIdentDescription[AUTH_MAX_NAME_LEN];
    long	ipsAuthIdentRowStatus;
    long	ipsAuthIdentStorageType;
    struct ipsAuthIdentAttr_entry *next;
};

/*
 * User Initiator Name Attributes Table
 */
void initialize_table_ipsAuthIdentNameAttr(void);
Netsnmp_Node_Handler ipsAuthIdentNameAttr_handler;
Netsnmp_First_Data_Point ipsAuthIdentNameAttr_get_first_data_point;
Netsnmp_Next_Data_Point ipsAuthIdentNameAttr_get_next_data_point;
int ipsAuthIdentNameAttr_load(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_IPSAUTHIDENTNAMEINDEX		1
#define COLUMN_IPSAUTHIDENTNAME			2
#define COLUMN_IPSAUTHIDENTNAMEROWSTATUS	3
#define COLUMN_IPSAUTHIDENTNAMESTORAGETYPE	4

/* Data structure for row entry */
struct ipsAuthIdentNameAttr_entry {
    u_long	ipsAuthInstIndex;
    u_long	ipsAuthIdentIndex;
    u_long	ipsAuthIdentNameIndex;
    char	ipsAuthIdentName[AUTH_MAX_NAME_LEN];
    long	ipsAuthIdentNameRowStatus;
    long	ipsAuthIdentNameStorageType;
    struct ipsAuthIdentNameAttr_entry *next;
};

/*
 * Credential Attributes Table
 */
void initialize_table_ipsAuthCredAttr(void);
Netsnmp_Node_Handler ipsAuthCredAttr_handler;
Netsnmp_First_Data_Point ipsAuthCredAttr_get_first_data_point;
Netsnmp_Next_Data_Point ipsAuthCredAttr_get_next_data_point;
int ipsAuthCredAttr_load(netsnmp_cache *cache, void *vmagic);
void ipsAuthCredAttr_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_IPSAUTHCREDINDEX		1
#define COLUMN_IPSAUTHCREDAUTHMETHOD	2
#define COLUMN_IPSAUTHCREDROWSTATUS	3
#define COLUMN_IPSAUTHCREDSTORAGETYPE	4

/* Data structure for row entry */
struct ipsAuthCredAttr_entry {
    u_long	ipsAuthInstIndex;
    u_long	ipsAuthIdentIndex;
    u_long	ipsAuthCredIndex;
    oid		ipsAuthCredAuthMethod[MAX_OID_LEN];
    int		ipsAuthCredAuthMethod_len;
    long	ipsAuthCredRowStatus;
    long	ipsAuthCredStorageType;
    struct ipsAuthCredAttr_entry *next;
};

/*
 * Credential Chap-Specific Attributes Table
 */
void initialize_table_ipsAuthCredChapAttr(void);
Netsnmp_Node_Handler ipsAuthCredChapAttr_handler;
Netsnmp_First_Data_Point ipsAuthCredChapAttr_get_first_data_point;
Netsnmp_Next_Data_Point ipsAuthCredChapAttr_get_next_data_point;
int ipsAuthCredChapAttr_load(netsnmp_cache *cache, void *vmagic);
void ipsAuthCredChapAttr_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_IPSAUTHCREDCHAPUSERNAME		1
#define COLUMN_IPSAUTHCREDCHAPROWSTATUS		2
#define COLUMN_IPSAUTHCREDCHAPSTORAGETYPE	3

/* Data structure for row entry */
struct ipsAuthCredChapAttr_entry {
    u_long	ipsAuthInstIndex;
    u_long	ipsAuthIdentIndex;
    u_long	ipsAuthCredIndex;
    char	ipsAuthCredChapUserName[AUTH_MAX_NAME_LEN];
    long	ipsAuthCredChapRowStatus;
    long	ipsAuthCredChapStorageType;
    struct ipsAuthCredChapAttr_entry *next;
};

void ipsDummy_free(netsnmp_cache *cache, void *vmagic);
#endif /* IPSAUTHMIB_H */
