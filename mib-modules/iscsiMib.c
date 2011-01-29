/*
 * Copyright (c) 2006 SBE, Inc.
 * Copyright (c) 2009-2011 Linux-iSCSI.org
 *
 * Nicholas A. Bellinger <nab@kernel.org>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */
#include <net-snmp/net-snmp-config.h>
#include <net-snmp/net-snmp-includes.h>
#include <net-snmp/agent/net-snmp-agent-includes.h>
#include "common.h"
#include "iscsiMib.h"
#include "iscsiAuthData.h"

static oid snmptrap_oid[] = {1, 3, 6, 1, 6, 3, 1, 1, 4, 1, 0};
static oid iscsiInstSsnErrStats_oid[] = {OID_LIO_ISCSI_MIB,1,1,2,1};

/*
 * Initializes the iscsiMib module
 */
void
init_iscsiMib(void)
{
    /* Initialize all tables */
    initialize_table_iscsiInstAttributes();
    initialize_table_iscsiInstSsnErrStats();
    initialize_table_iscsiPortalAttributes();
    initialize_table_iscsiTgtPortalAttributes();
    initialize_table_iscsiNodeAttributes();
    initialize_table_iscsiTgtLoginStats();
    initialize_table_iscsiTgtLogoutStats();
    initialize_table_iscsiTgtAuthAttributes();
    initialize_table_iscsiSessionAttributes();
    initialize_table_iscsiSessionStats();
    initialize_table_iscsiSsnCxnErrStats();
    initialize_table_iscsiCxnAttributes();
    initialize_iscsiTargetAttributes();
    initialize_iscsiInstSessionFailure();
}

/*
 * Instance Attributes Table
 */

#define ISCSI_INST_ATTR_CACHE_TIMEOUT 5

/*
 * Initialize the iscsiInstAttributes table
 */
void
initialize_table_iscsiInstAttributes(void)
{
    static oid iscsiInstAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,1,1};
    size_t iscsiInstAttributes_oid_len = OID_LENGTH(iscsiInstAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiInstAttributes",    
                                              iscsiInstAttributes_handler,
                                              iscsiInstAttributes_oid,
                                              iscsiInstAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* index: iscsiInstIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 13;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiInstAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiInstAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(ISCSI_INST_ATTR_CACHE_TIMEOUT,
                                             iscsiInstAttributes_load,
                                             iscsiInstAttributes_free,
                                             iscsiInstAttributes_oid,
                                             iscsiInstAttributes_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiInstAttributes_cache_update(void)
{
    static marker_t iscsiInstAttributes_cache_marker = NULL;

    if (iscsiInstAttributes_cache_marker &&
        (!atime_ready(iscsiInstAttributes_cache_marker,
                      ISCSI_INST_ATTR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiInstAttributes_cache_marker)
        atime_setMarker(iscsiInstAttributes_cache_marker);
    else
        iscsiInstAttributes_cache_marker = atime_newMarker();

    iscsiInstAttributes_load(NULL, NULL);
}
#endif

struct iscsiInstAttributes_entry *iscsiInstAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiInstAttributes_get_first_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiInstAttributes_cache_update();
#endif
    *my_loop_context = iscsiInstAttributes_head;
    return iscsiInstAttributes_get_next_data_point(my_loop_context,
                                                   my_data_context,
                                                   put_index_data, mydata);
}

netsnmp_variable_list *
iscsiInstAttributes_get_next_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
    struct iscsiInstAttributes_entry *entry =
                           (struct iscsiInstAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}


/*
 * Handles requests for the iscsiInstAttributes table
 */
int
iscsiInstAttributes_handler(netsnmp_mib_handler *handler,
                            netsnmp_handler_registration *reginfo,
                            netsnmp_agent_request_info *reqinfo,
                            netsnmp_request_info *requests)
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiInstAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiInstAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info =  netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {

            case COLUMN_ISCSIINSTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiInstIndex,
                          sizeof(table_entry->iscsiInstIndex));
                break;

            case COLUMN_ISCSIINSTDESCR:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiInstDescr,
                          strlen(table_entry->iscsiInstDescr));
                break;

            case COLUMN_ISCSIINSTVERSIONMIN:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiInstVersionMin,
                          sizeof(table_entry->iscsiInstVersionMin));
                break;

            case COLUMN_ISCSIINSTVERSIONMAX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiInstVersionMax,
                          sizeof(table_entry->iscsiInstVersionMax));
                break;
            case COLUMN_ISCSIINSTVENDORID:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiInstVendorID,
                          strlen(table_entry->iscsiInstVendorID));
                break;
            case COLUMN_ISCSIINSTVENDORVERSION:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiInstVendorVersion,
                          strlen(table_entry->iscsiInstVendorVersion));
                break;
            case COLUMN_ISCSIINSTPORTALNUMBER:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiInstPortalNumber,
                          sizeof(table_entry->iscsiInstPortalNumber));
                break;
            case COLUMN_ISCSIINSTNODENUMBER:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiInstNodeNumber,
                          sizeof(table_entry->iscsiInstNodeNumber));
                break;
            case COLUMN_ISCSIINSTSESSIONNUMBER:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiInstSessionNumber,
                          sizeof(table_entry->iscsiInstSessionNumber));
                break;
            case COLUMN_ISCSIINSTSSNFAILURES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiInstSsnFailures,
                          sizeof(table_entry->iscsiInstSsnFailures));
                break;
            case COLUMN_ISCSIINSTLASTSSNFAILURETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                          (u_char *)&table_entry->iscsiInstLastSsnFailureType,
                          table_entry->iscsiInstLastSsnFailureType_len *
                          sizeof(oid));
                break;
            case COLUMN_ISCSIINSTLASTSSNRMTNODENAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiInstLastSsnRmtNodeName,
                          strlen(table_entry->iscsiInstLastSsnRmtNodeName));
                break;
            case COLUMN_ISCSIINSTDISCONTINUITYTIME:
                snmp_set_var_typed_value(request->requestvb, ASN_TIMETICKS,
                          (u_char *)&table_entry->iscsiInstDiscontinuityTime,
                          sizeof(table_entry->iscsiInstDiscontinuityTime));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_INST_ATTR "/proc/iscsi_target/mib/inst_attr"
#define ISCSI_INST_ATTR_LINE "%lu %lu %lu %lu %lu %lu %lu %u %s %lu"

int
iscsiInstAttributes_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    struct iscsiInstAttributes_entry tmp, *entry;
    u_int failType;

    if (iscsiInstAttributes_head)
        iscsiInstAttributes_free(NULL, NULL);

    if (!(fp = fopen(PROC_INST_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_INST_ATTR);
        return -1;
    }

    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_INST_ATTR_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiInstVersionMin, &tmp.iscsiInstVersionMax,
                   &tmp.iscsiInstPortalNumber, &tmp.iscsiInstNodeNumber,
                   &tmp.iscsiInstSessionNumber, &tmp.iscsiInstSsnFailures,
                   &failType, tmp.iscsiInstLastSsnRmtNodeName, 
                   &tmp.iscsiInstDiscontinuityTime) != 10)
            continue;

        if (failType) {
            int oidLen = OID_LENGTH(iscsiInstSsnErrStats_oid);
            memcpy(tmp.iscsiInstLastSsnFailureType, iscsiInstSsnErrStats_oid,
                   sizeof(iscsiInstSsnErrStats_oid)); 
            tmp.iscsiInstLastSsnFailureType[oidLen] = failType;
            tmp.iscsiInstLastSsnFailureType_len = oidLen + 1;
        }
        else {
            /* return {0.0} */
            tmp.iscsiInstLastSsnFailureType_len = 2;
        }

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "description: %s", tmp.iscsiInstDescr) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.iscsiInstDescr, line + strlen("description: "));
        }
        else
            break;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "vendor: %s", tmp.iscsiInstVendorID) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.iscsiInstVendorID, line + strlen("vendor: "));
        }
        else
            break;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "version: %s", tmp.iscsiInstVendorVersion) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.iscsiInstVendorVersion, line + strlen("version: "));
        }
        else
            break;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiInstAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiInstAttributes_head;
        iscsiInstAttributes_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiInstAttributes_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiInstAttributes_entry *entry;

    while (iscsiInstAttributes_head) {
        entry = iscsiInstAttributes_head;
        iscsiInstAttributes_head = iscsiInstAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Instance Session Failure Stats Table
 */

#define ISCSI_INST_SSN_ERR_CACHE_TIMEOUT 5

/*
 * Initialize the iscsiInstSsnErrStats table
 */
void
initialize_table_iscsiInstSsnErrStats(void)
{
    static oid iscsiInstSsnErrStats_oid[] = {OID_LIO_ISCSI_MIB,1,1,2};
    size_t iscsiInstSsnErrStats_oid_len   =
                                      OID_LENGTH(iscsiInstSsnErrStats_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiInstSsnErrStats",
                                              iscsiInstSsnErrStats_handler,
                                              iscsiInstSsnErrStats_oid,
                                              iscsiInstSsnErrStats_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF( netsnmp_table_registration_info );
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* index: iscsiInstIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 4;
    
    iinfo = SNMP_MALLOC_TYPEDEF( netsnmp_iterator_info );
    iinfo->get_first_data_point= iscsiInstSsnErrStats_get_first_data_point;
    iinfo->get_next_data_point = iscsiInstSsnErrStats_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator( reg, iinfo );

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg,
                     netsnmp_get_cache_handler(ISCSI_INST_SSN_ERR_CACHE_TIMEOUT,
                                               iscsiInstSsnErrStats_load,
                                               iscsiInstSsnErrStats_free,
                                               iscsiInstSsnErrStats_oid,
                                               iscsiInstSsnErrStats_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiInstSsnErrStats_cache_update(void)
{
    static marker_t iscsiInstSsnErrStats_cache_marker = NULL;

    if (iscsiInstSsnErrStats_cache_marker &&
        (!atime_ready(iscsiInstSsnErrStats_cache_marker,
                      ISCSI_INST_SSN_ERR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiInstSsnErrStats_cache_marker)
        atime_setMarker(iscsiInstSsnErrStats_cache_marker);
    else
        iscsiInstSsnErrStats_cache_marker = atime_newMarker();

    iscsiInstSsnErrStats_load(NULL, NULL);
}
#endif

struct iscsiInstSsnErrStats_entry  *iscsiInstSsnErrStats_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiInstSsnErrStats_get_first_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiInstSsnErrStats_cache_update();
#endif
    *my_loop_context = iscsiInstSsnErrStats_head;
    return iscsiInstSsnErrStats_get_next_data_point(my_loop_context,
                                                    my_data_context,
                                                    put_index_data, mydata);
}

netsnmp_variable_list *
iscsiInstSsnErrStats_get_next_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
    struct iscsiInstSsnErrStats_entry *entry =
                    (struct iscsiInstSsnErrStats_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiInstSsnErrStats table
 */
int
iscsiInstSsnErrStats_handler(netsnmp_mib_handler *handler,
                             netsnmp_handler_registration *reginfo,
                             netsnmp_agent_request_info *reqinfo,
                             netsnmp_request_info *requests)
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiInstSsnErrStats_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiInstSsnErrStats_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSIINSTSSNDIGESTERRORS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiInstSsnDigestErrors,
                          sizeof(table_entry->iscsiInstSsnDigestErrors));
                break;
            case COLUMN_ISCSIINSTSSNCXNTIMEOUTERRORS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiInstSsnCxnTimeoutErrors,
                          sizeof(table_entry->iscsiInstSsnCxnTimeoutErrors));
                break;
            case COLUMN_ISCSIINSTSSNFORMATERRORS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiInstSsnFormatErrors,
                          sizeof(table_entry->iscsiInstSsnFormatErrors));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SESS_ERR_STATS "/proc/iscsi_target/mib/sess_err_stats"
#define ISCSI_SESS_ERR_STATS_LINE "%lu %lu %lu %lu"
int
iscsiInstSsnErrStats_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[64];
    struct iscsiInstSsnErrStats_entry tmp, *entry;

    if (iscsiInstSsnErrStats_head)
        iscsiInstSsnErrStats_free(NULL, NULL);

    if (!(fp = fopen(PROC_SESS_ERR_STATS, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SESS_ERR_STATS);
        return -1;
    }

    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_SESS_ERR_STATS_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiInstSsnDigestErrors,
                   &tmp.iscsiInstSsnCxnTimeoutErrors,
                   &tmp.iscsiInstSsnFormatErrors) != 4)
            continue;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiInstSsnErrStats_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiInstSsnErrStats_head;
        iscsiInstSsnErrStats_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiInstSsnErrStats_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiInstSsnErrStats_entry *entry;

    while (iscsiInstSsnErrStats_head) {
        entry = iscsiInstSsnErrStats_head;
        iscsiInstSsnErrStats_head = iscsiInstSsnErrStats_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Portal Attributes Table
 */

#define ISCSI_PORTAL_ATTR_CACHE_TIMEOUT 10

/*
 * Initialize the iscsiPortalAttributes table
 */
void
initialize_table_iscsiPortalAttributes(void)
{
    static oid iscsiPortalAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,2,1};
    size_t iscsiPortalAttributes_oid_len =
                                         OID_LENGTH(iscsiPortalAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiPortalAttributes",
                                              iscsiPortalAttributes_handler,
                                              iscsiPortalAttributes_oid,
                                              iscsiPortalAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* index: iscsiInstIndex */
                                     ASN_UNSIGNED,  /* index: iscsiPortalIndex*/
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 14;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiPortalAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiPortalAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg,
                   netsnmp_get_cache_handler(ISCSI_PORTAL_ATTR_CACHE_TIMEOUT,
                                             iscsiPortalAttributes_load,
                                             iscsiPortalAttributes_free,
                                             iscsiPortalAttributes_oid,
                                             iscsiPortalAttributes_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiPortalAttributes_cache_update(void)
{
    static marker_t iscsiPortalAttributes_cache_marker = NULL;

    if (iscsiPortalAttributes_cache_marker &&
        (!atime_ready(iscsiPortalAttributes_cache_marker,
                      ISCSI_PORTAL_ATTR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiPortalAttributes_cache_marker)
        atime_setMarker(iscsiPortalAttributes_cache_marker);
    else
        iscsiPortalAttributes_cache_marker = atime_newMarker();

    iscsiPortalAttributes_load(NULL, NULL);
}
#endif

struct iscsiPortalAttributes_entry *iscsiPortalAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiPortalAttributes_get_first_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiPortalAttributes_cache_update();
#endif
    *my_loop_context = iscsiPortalAttributes_head;
    return iscsiPortalAttributes_get_next_data_point(my_loop_context,
                                                     my_data_context,
                                                     put_index_data, mydata);
}

netsnmp_variable_list *
iscsiPortalAttributes_get_next_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
    struct iscsiPortalAttributes_entry *entry = 
                         (struct iscsiPortalAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiPortalIndex,
                           sizeof(entry->iscsiPortalIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}


/*
 * Handles requests for the iscsiPortalAttributes table
 */
int
iscsiPortalAttributes_handler(netsnmp_mib_handler *handler,
                              netsnmp_handler_registration *reginfo,
                              netsnmp_agent_request_info *reqinfo,
                              netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiPortalAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiPortalAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSIPORTALINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiPortalIndex,
                          sizeof(table_entry->iscsiPortalIndex));
                break;
            case COLUMN_ISCSIPORTALROWSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiPortalRowStatus,
                          sizeof(table_entry->iscsiPortalRowStatus));
                break;
            case COLUMN_ISCSIPORTALROLES:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)&table_entry->iscsiPortalRoles,
                          sizeof(table_entry->iscsiPortalRoles));
                break;
            case COLUMN_ISCSIPORTALADDRTYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiPortalAddrType,
                          sizeof(table_entry->iscsiPortalAddrType));
                break;
            case COLUMN_ISCSIPORTALADDR:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                      (u_char *)table_entry->iscsiPortalAddr,
                      (table_entry->iscsiPortalAddrType == INET_ADDR_TYPE_IPV4)?
                       INET_ADDR_TYPE_IPV4_LEN:
                       sizeof(table_entry->iscsiPortalAddr));
                break;
            case COLUMN_ISCSIPORTALPROTOCOL:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiPortalProtocol,
                          sizeof(table_entry->iscsiPortalProtocol));
                break;
            case COLUMN_ISCSIPORTALMAXRECVDATASEGLENGTH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                      (u_char *)&table_entry->iscsiPortalMaxRecvDataSegLength,
                      sizeof(table_entry->iscsiPortalMaxRecvDataSegLength));
                break;
            case COLUMN_ISCSIPORTALPRIMARYHDRDIGEST:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiPortalPrimaryHdrDigest,
                          sizeof(table_entry->iscsiPortalPrimaryHdrDigest));
                break;
            case COLUMN_ISCSIPORTALPRIMARYDATADIGEST:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiPortalPrimaryDataDigest,
                          sizeof(table_entry->iscsiPortalPrimaryDataDigest));
                break;
            case COLUMN_ISCSIPORTALSECONDARYHDRDIGEST:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiPortalSecondaryHdrDigest,
                          sizeof(table_entry->iscsiPortalSecondaryHdrDigest));
                break;
            case COLUMN_ISCSIPORTALSECONDARYDATADIGEST:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                      (u_char *)&table_entry->iscsiPortalSecondaryDataDigest,
                      sizeof(table_entry->iscsiPortalSecondaryDataDigest));
                break;
            case COLUMN_ISCSIPORTALRECVMARKER:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiPortalRecvMarker,
                          sizeof(table_entry->iscsiPortalRecvMarker));
                break;
            case COLUMN_ISCSIPORTALSTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiPortalStorageType,
                          sizeof(table_entry->iscsiPortalStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_PORTAL_ATTR "/proc/iscsi_target/mib/portal_attr"
#define ISCSI_PORTAL_ATTR_LINE "%lu %lu %s %s %08X %s %lu %s %s %s"

int 
iscsiPortalAttributes_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[128];
    struct iscsiPortalAttributes_entry tmp, *entry;
    char roles[16];
    char addrType[8];
    char proto[8];
    char hdrDigest[16];
    char dataDigest[16];
    char rcvMarker[4];
    char *secDigest;
    uint32_t addr;

    if (iscsiPortalAttributes_head)
        iscsiPortalAttributes_free(NULL, NULL);

    if (!(fp = fopen(PROC_PORTAL_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_PORTAL_ATTR);
        return -1;
    }

    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_PORTAL_ATTR_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiPortalIndex, roles, addrType,
                   (u_int *)tmp.iscsiPortalAddr, proto, 
                   &tmp.iscsiPortalMaxRecvDataSegLength, hdrDigest,
                   dataDigest, rcvMarker) != 10)
            continue;

        tmp.iscsiPortalRowStatus = RS_ACTIVE;
        tmp.iscsiPortalRoles = NODE_ROLE_TARGET;
        if (!strcmp(addrType, "ipv4")) {
            tmp.iscsiPortalAddrType = INET_ADDR_TYPE_IPV4;
            addr = htonl(*(uint32_t *)&tmp.iscsiPortalAddr);
            *(uint32_t *)tmp.iscsiPortalAddr = addr;
        }

        if (!strcmp(proto, "TCP"))
            tmp.iscsiPortalProtocol = TRANSPORT_PROTO_TCP;
        else if (!strcmp(proto, "SCTP"))
            tmp.iscsiPortalProtocol = TRANSPORT_PROTO_SCTP;

        if (!strncmp(hdrDigest, "CRC32C", 6))
            tmp.iscsiPortalPrimaryHdrDigest = ISCSI_DIGEST_CRC32C;
        else if (!strncmp(hdrDigest, "None", 4))
            tmp.iscsiPortalPrimaryHdrDigest = ISCSI_DIGEST_NODIGEST;
        else
            tmp.iscsiPortalPrimaryHdrDigest = ISCSI_DIGEST_OTHER;

        if (!strncmp(dataDigest, "CRC32C", 6))
            tmp.iscsiPortalPrimaryDataDigest = ISCSI_DIGEST_CRC32C;
        else if (!strncmp(dataDigest, "None", 4))
            tmp.iscsiPortalPrimaryDataDigest = ISCSI_DIGEST_NODIGEST;
        else
            tmp.iscsiPortalPrimaryDataDigest = ISCSI_DIGEST_OTHER;

        if ((secDigest = strchr(hdrDigest, ','))) {
            secDigest++;
            if (!strcmp(secDigest, "CRC32C"))
                tmp.iscsiPortalSecondaryHdrDigest = ISCSI_DIGEST_CRC32C;
            else if (!strcmp(secDigest, "None"))
                tmp.iscsiPortalSecondaryHdrDigest = ISCSI_DIGEST_NODIGEST;
            else
                tmp.iscsiPortalSecondaryHdrDigest = ISCSI_DIGEST_OTHER;
        }
        else {
                tmp.iscsiPortalSecondaryHdrDigest = ISCSI_DIGEST_OTHER;
                snmp_log(LOG_DEBUG, "portal_attr: SecHdrDigest not found\n");
        }

        if ((secDigest = strchr(hdrDigest, ','))) {
            secDigest++;
            if (!strcmp(secDigest, "CRC32C"))
                tmp.iscsiPortalSecondaryDataDigest = ISCSI_DIGEST_CRC32C;
            else if (!strcmp(secDigest, "None"))
                tmp.iscsiPortalSecondaryDataDigest = ISCSI_DIGEST_NODIGEST;
            else
                tmp.iscsiPortalSecondaryDataDigest = ISCSI_DIGEST_OTHER;
        }
        else {
                tmp.iscsiPortalSecondaryDataDigest = ISCSI_DIGEST_OTHER;
                snmp_log(LOG_DEBUG, "portal_attr: SecDataDigest not found\n");
        }

        if (!strcmp(rcvMarker, "Yes"))
            tmp.iscsiPortalRecvMarker = TV_TRUE;
        else
            tmp.iscsiPortalRecvMarker = TV_FALSE;

        tmp.iscsiPortalStorageType = ST_READONLY;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiPortalAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiPortalAttributes_head;
        iscsiPortalAttributes_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiPortalAttributes_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiPortalAttributes_entry *entry;

    while (iscsiPortalAttributes_head) {
        entry = iscsiPortalAttributes_head;
        iscsiPortalAttributes_head = iscsiPortalAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Target Portal Attributes Table
 */

#define ISCSI_TGT_PORTAL_ATTR_CACHE_TIMEOUT 10

/*
 * Initialize the iscsiTgtPortalAttributes table
 */
void
initialize_table_iscsiTgtPortalAttributes(void)
{
    static oid iscsiTgtPortalAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,3,1};
    size_t iscsiTgtPortalAttributes_oid_len =
                                       OID_LENGTH(iscsiTgtPortalAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiTgtPortalAttributes",
                                              iscsiTgtPortalAttributes_handler,
                                              iscsiTgtPortalAttributes_oid,
                                              iscsiTgtPortalAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiPortalIndex */
                                     ASN_UNSIGNED,  /* iscsiTgtPortalNodeIndex*/
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 5;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiTgtPortalAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiTgtPortalAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                  netsnmp_get_cache_handler(ISCSI_TGT_PORTAL_ATTR_CACHE_TIMEOUT,
                                            iscsiTgtPortalAttributes_load, 
                                            iscsiTgtPortalAttributes_free,
                                            iscsiTgtPortalAttributes_oid, 
                                            iscsiTgtPortalAttributes_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiTgtPortalAttributes_cache_update(void)
{
    static marker_t iscsiTgtPortalAttributes_cache_marker = NULL;

    if (iscsiTgtPortalAttributes_cache_marker &&
        (!atime_ready(iscsiTgtPortalAttributes_cache_marker,
                      ISCSI_TGT_PORTAL_ATTR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiTgtPortalAttributes_cache_marker)
        atime_setMarker(iscsiTgtPortalAttributes_cache_marker);
    else
        iscsiTgtPortalAttributes_cache_marker = atime_newMarker();

    iscsiTgtPortalAttributes_load(NULL, NULL);
}
#endif

struct iscsiTgtPortalAttributes_entry *iscsiTgtPortalAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiTgtPortalAttributes_get_first_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiTgtPortalAttributes_cache_update();
#endif
    *my_loop_context = iscsiTgtPortalAttributes_head;
    return iscsiTgtPortalAttributes_get_next_data_point(my_loop_context,
                                                        my_data_context,
                                                        put_index_data, mydata);
}

netsnmp_variable_list *
iscsiTgtPortalAttributes_get_next_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
    struct iscsiTgtPortalAttributes_entry *entry =
                      (struct iscsiTgtPortalAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiPortalIndex,
                           sizeof(entry->iscsiPortalIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiTgtPortalNodeIndexOrZero,
                           sizeof(entry->iscsiTgtPortalNodeIndexOrZero));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiTgtPortalAttributes table
 */
int
iscsiTgtPortalAttributes_handler(netsnmp_mib_handler *handler,
                                 netsnmp_handler_registration *reginfo,
                                 netsnmp_agent_request_info *reqinfo,
                                 netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiTgtPortalAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiTgtPortalAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSITGTPORTALNODEINDEXORZERO:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiTgtPortalNodeIndexOrZero,
                          sizeof(table_entry->iscsiTgtPortalNodeIndexOrZero));
                break;
            case COLUMN_ISCSITGTPORTALPORT:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiTgtPortalPort,
                          sizeof(table_entry->iscsiTgtPortalPort));
                break;
            case COLUMN_ISCSITGTPORTALTAG:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiTgtPortalTag,
                          sizeof(table_entry->iscsiTgtPortalTag));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_TGT_PORTAL_ATTR "/proc/iscsi_target/mib/tgt_portal_attr"
#define ISCSI_TGT_PORTAL_ATTR_LINE "%lu %lu %lu %lu %lu"

int 
iscsiTgtPortalAttributes_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[64];
    struct iscsiTgtPortalAttributes_entry tmp, *entry;

    if (iscsiTgtPortalAttributes_head)
        iscsiTgtPortalAttributes_free(NULL, NULL);

    if (!(fp = fopen(PROC_TGT_PORTAL_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_TGT_PORTAL_ATTR);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_TGT_PORTAL_ATTR_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiPortalIndex, &tmp.iscsiTgtPortalNodeIndexOrZero,
                   &tmp.iscsiTgtPortalPort, &tmp.iscsiTgtPortalTag) != 5)
            continue;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiTgtPortalAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiTgtPortalAttributes_head;
        iscsiTgtPortalAttributes_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiTgtPortalAttributes_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiTgtPortalAttributes_entry *entry;

    while (iscsiTgtPortalAttributes_head) {
        entry = iscsiTgtPortalAttributes_head;
        iscsiTgtPortalAttributes_head = iscsiTgtPortalAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Node Attributes Table
 */

#define ISCSI_NODE_ATTR_CACHE_TIMEOUT 10

/*
 * Initialize the iscsiNodeAttributes table
 */
void
initialize_table_iscsiNodeAttributes(void)
{
    static oid iscsiNodeAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,5,1};
    size_t iscsiNodeAttributes_oid_len = OID_LENGTH(iscsiNodeAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiNodeAttributes",
                                              iscsiNodeAttributes_handler,
                                              iscsiNodeAttributes_oid,
                                              iscsiNodeAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiNodeIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 19;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiNodeAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiNodeAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(ISCSI_NODE_ATTR_CACHE_TIMEOUT,
                                             iscsiNodeAttributes_load, 
                                             iscsiNodeAttributes_free,
                                             iscsiNodeAttributes_oid, 
                                             iscsiNodeAttributes_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiNodeAttributes_cache_update(void)
{
    static marker_t iscsiNodeAttributes_cache_marker = NULL;

    if (iscsiNodeAttributes_cache_marker &&
        (!atime_ready(iscsiNodeAttributes_cache_marker,
                      ISCSI_NODE_ATTR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiNodeAttributes_cache_marker)
        atime_setMarker(iscsiNodeAttributes_cache_marker);
    else
        iscsiNodeAttributes_cache_marker = atime_newMarker();

    iscsiNodeAttributes_load(NULL, NULL);
}
#endif

struct iscsiNodeAttributes_entry *iscsiNodeAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiNodeAttributes_get_first_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiNodeAttributes_cache_update();
#endif
    *my_loop_context = iscsiNodeAttributes_head;
    return iscsiNodeAttributes_get_next_data_point(my_loop_context,
                                                   my_data_context,
                                                   put_index_data, mydata);
}

netsnmp_variable_list *
iscsiNodeAttributes_get_next_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
    struct iscsiNodeAttributes_entry *entry =
                           (struct iscsiNodeAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiNodeIndex,
                           sizeof(entry->iscsiNodeIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiNodeAttributes table
 */
int
iscsiNodeAttributes_handler(netsnmp_mib_handler *handler,
                            netsnmp_handler_registration *reginfo,
                            netsnmp_agent_request_info *reqinfo,
                            netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiNodeAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiNodeAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSINODEINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeIndex,
                          sizeof(table_entry->iscsiNodeIndex));
                break;
            case COLUMN_ISCSINODENAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiNodeName,
                          strlen(table_entry->iscsiNodeName));
                break;
            case COLUMN_ISCSINODEALIAS:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiNodeAlias,
                          strlen(table_entry->iscsiNodeAlias));
                break;
            case COLUMN_ISCSINODEROLES:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)&table_entry->iscsiNodeRoles,
                          sizeof(table_entry->iscsiNodeRoles));
                break;
            case COLUMN_ISCSINODETRANSPORTTYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                         (u_char *)&table_entry->iscsiNodeTransportType,
                         table_entry->iscsiNodeTransportType_len * sizeof(oid));
                break;
            case COLUMN_ISCSINODEINITIALR2T:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiNodeInitialR2T,
                          sizeof(table_entry->iscsiNodeInitialR2T));
                break;
            case COLUMN_ISCSINODEIMMEDIATEDATA:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiNodeImmediateData,
                          sizeof(table_entry->iscsiNodeImmediateData));
                break;
            case COLUMN_ISCSINODEMAXOUTSTANDINGR2T:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeMaxOutstandingR2T,
                          sizeof(table_entry->iscsiNodeMaxOutstandingR2T));
                break;
            case COLUMN_ISCSINODEFIRSTBURSTLENGTH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeFirstBurstLength,
                          sizeof(table_entry->iscsiNodeFirstBurstLength));
                break;
            case COLUMN_ISCSINODEMAXBURSTLENGTH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeMaxBurstLength,
                          sizeof(table_entry->iscsiNodeMaxBurstLength));
                break;
            case COLUMN_ISCSINODEMAXCONNECTIONS:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeMaxConnections,
                          sizeof(table_entry->iscsiNodeMaxConnections));
                break;
            case COLUMN_ISCSINODEDATASEQUENCEINORDER:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiNodeDataSequenceInOrder,
                          sizeof(table_entry->iscsiNodeDataSequenceInOrder));
                break;
            case COLUMN_ISCSINODEDATAPDUINORDER:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiNodeDataPDUInOrder,
                          sizeof(table_entry->iscsiNodeDataPDUInOrder));
                break;
            case COLUMN_ISCSINODEDEFAULTTIME2WAIT:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeDefaultTime2Wait,
                          sizeof(table_entry->iscsiNodeDefaultTime2Wait));
                break;
            case COLUMN_ISCSINODEDEFAULTTIME2RETAIN:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeDefaultTime2Retain,
                          sizeof(table_entry->iscsiNodeDefaultTime2Retain));
                break;
            case COLUMN_ISCSINODEERRORRECOVERYLEVEL:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiNodeErrorRecoveryLevel,
                          sizeof(table_entry->iscsiNodeErrorRecoveryLevel));
                break;
            case COLUMN_ISCSINODEDISCONTINUITYTIME:
                snmp_set_var_typed_value(request->requestvb, ASN_TIMETICKS,
                          (u_char *)&table_entry->iscsiNodeDiscontinuityTime,
                          sizeof(table_entry->iscsiNodeDiscontinuityTime));
                break;
            case COLUMN_ISCSINODESTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiNodeStorageType,
                          sizeof(table_entry->iscsiNodeStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_NODE_ATTR "/proc/iscsi_target/mib/node_attr"
#define ISCSI_NODE_ATTR_LINE "%lu %lu %s %s %s %s %lu %lu %lu %lu %s %s %lu %lu %lu %lu"
static oid scsiInstanceAlias_oid[] = {OID_LIO_SCSI_MIB,2,1,1,1,2,1};
int 
iscsiNodeAttributes_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp, *alias_fp;
    char line[512];
    char roles[16];
    char r2t[4];
    char immData[4];
    char seqOrder[4];
    char pduOrder[4];
    struct iscsiNodeAttributes_entry tmp, *entry;

    if (iscsiNodeAttributes_head)
        iscsiNodeAttributes_free(NULL, NULL);

    if (!(fp = fopen(PROC_NODE_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_NODE_ATTR);
        return -1;
    }

    alias_fp = fopen("/etc/iscsi.alias", "r");
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_NODE_ATTR_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiNodeIndex, tmp.iscsiNodeName, roles, r2t,
                   immData, &tmp.iscsiNodeMaxOutstandingR2T,
                   &tmp.iscsiNodeFirstBurstLength, &tmp.iscsiNodeMaxBurstLength,
                   &tmp.iscsiNodeMaxConnections, seqOrder, pduOrder,
                   &tmp.iscsiNodeDefaultTime2Wait,
                   &tmp.iscsiNodeDefaultTime2Retain,
                   &tmp.iscsiNodeErrorRecoveryLevel,
                   &tmp.iscsiNodeDiscontinuityTime) != 16)
            continue;

        tmp.iscsiNodeRoles = NODE_ROLE_TARGET;

        /* As PyX stack supports multiple devices within a node, set the 
           row pointer to the scsi instance instead of scsi transport */
        tmp.iscsiNodeTransportType_len = OID_LENGTH(scsiInstanceAlias_oid);
        memcpy(tmp.iscsiNodeTransportType, scsiInstanceAlias_oid,
               sizeof(scsiInstanceAlias_oid));

        if (!strcmp(r2t, "Yes"))
            tmp.iscsiNodeInitialR2T = TV_TRUE;
        else
            tmp.iscsiNodeInitialR2T = TV_FALSE;

        if (!strcmp(immData, "Yes"))
            tmp.iscsiNodeImmediateData = TV_TRUE;
        else
            tmp.iscsiNodeImmediateData = TV_FALSE;

        if (!strcmp(seqOrder, "Yes"))
            tmp.iscsiNodeDataSequenceInOrder = TV_TRUE;
        else
            tmp.iscsiNodeDataSequenceInOrder = TV_FALSE;

        if (!strcmp(pduOrder, "Yes"))
            tmp.iscsiNodeDataPDUInOrder = TV_TRUE;
        else
            tmp.iscsiNodeDataPDUInOrder = TV_FALSE;

        tmp.iscsiNodeStorageType = ST_READONLY;

        if (alias_fp && (line == fgets(line, sizeof(line), alias_fp)))
            sscanf(line, "%s", tmp.iscsiNodeAlias);

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiNodeAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiNodeAttributes_head;
        iscsiNodeAttributes_head = entry;
    }
    fclose(fp);
    if (alias_fp)
        fclose(alias_fp);

    return 0;
}

void
iscsiNodeAttributes_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiNodeAttributes_entry *entry;

    while (iscsiNodeAttributes_head) {
        entry = iscsiNodeAttributes_head;
        iscsiNodeAttributes_head = iscsiNodeAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Target Attributes Table and Target Login Failure Notification
 */

/* Use 3 sec poll recommended by the draft */
#define ISCSI_TGT_LOGIN_FAIL_POLL_INTERVAL 3

/* Initializes the iscsiTargetAttributes */
void
initialize_iscsiTargetAttributes(void)
{
    /* Initialize the table */
    initialize_table_iscsiTargetAttributes();

    /* Setup callback for polling for login failure */
    snmp_alarm_register(ISCSI_TGT_LOGIN_FAIL_POLL_INTERVAL, SA_REPEAT,
                        iscsiTargetAttributes_load, NULL);

    /* Initial load */
    iscsiTargetAttributes_load(0, NULL);
}

/*
 * Initialize the iscsiTargetAttributes table
 */
void
initialize_table_iscsiTargetAttributes(void)
{
    static oid iscsiTargetAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,6,1};
    size_t iscsiTargetAttributes_oid_len = 
                                         OID_LENGTH(iscsiTargetAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiTargetAttributes",
                                              iscsiTargetAttributes_handler,
                                              iscsiTargetAttributes_oid,
                                              iscsiTargetAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiNodeIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 8;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiTargetAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiTargetAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);
}

struct iscsiTargetAttributes_entry *iscsiTargetAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiTargetAttributes_get_first_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
    *my_loop_context = iscsiTargetAttributes_head;
    return iscsiTargetAttributes_get_next_data_point(my_loop_context,
                                                     my_data_context,
                                                     put_index_data, mydata);
}

netsnmp_variable_list *
iscsiTargetAttributes_get_next_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
    struct iscsiTargetAttributes_entry *entry =
                         (struct iscsiTargetAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiNodeIndex,
                           sizeof(entry->iscsiNodeIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiTargetAttributes table
 */
int
iscsiTargetAttributes_handler(netsnmp_mib_handler *handler,
                              netsnmp_handler_registration *reginfo,
                              netsnmp_agent_request_info *reqinfo,
                              netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiTargetAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiTargetAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSITGTLOGINFAILURES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLoginFailures,
                          sizeof(table_entry->iscsiTgtLoginFailures));
                break;
            case COLUMN_ISCSITGTLASTFAILURETIME:
                snmp_set_var_typed_value(request->requestvb, ASN_TIMETICKS,
                          (u_char *)&table_entry->iscsiTgtLastFailureTime,
                          sizeof(table_entry->iscsiTgtLastFailureTime));
                break;
            case COLUMN_ISCSITGTLASTFAILURETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                        (u_char *)table_entry->iscsiTgtLastFailureType,
                        table_entry->iscsiTgtLastFailureType_len * sizeof(oid));
                break;
            case COLUMN_ISCSITGTLASTINTRFAILURENAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiTgtLastIntrFailureName,
                          strlen(table_entry->iscsiTgtLastIntrFailureName));
                break;
            case COLUMN_ISCSITGTLASTINTRFAILUREADDRTYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                        (u_char *)&table_entry->iscsiTgtLastIntrFailureAddrType,
                        sizeof(table_entry->iscsiTgtLastIntrFailureAddrType));
                break;
            case COLUMN_ISCSITGTLASTINTRFAILUREADDR:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiTgtLastIntrFailureAddr,
                          (table_entry->iscsiTgtLastIntrFailureAddrType ==
                           INET_ADDR_TYPE_IPV4)?  INET_ADDR_TYPE_IPV4_LEN:
                          sizeof(table_entry->iscsiTgtLastIntrFailureAddr));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

/* 
 * Notification code 
 */
struct iscsiTargetAttributes_entry lastTrap;
int
send_iscsiTgtLoginFailure_trap(struct iscsiTargetAttributes_entry *entry)
{
    netsnmp_variable_list  *var_list = NULL;
    oid iscsiTgtLoginFailure_oid[] = {OID_LIO_ISCSI_MIB,0,1};
    oid iscsiTgtLoginFailures_oid[] = {OID_LIO_ISCSI_MIB,1,6,1,1,1,
                                       entry->iscsiInstIndex,
                                       entry->iscsiNodeIndex};
    oid iscsiTgtLastFailureType_oid[] = {OID_LIO_ISCSI_MIB,1,6,1,1,3,
                                         entry->iscsiInstIndex,
                                         entry->iscsiNodeIndex};
    oid iscsiTgtLastIntrFailureName_oid[] = {OID_LIO_ISCSI_MIB,1,6,1,1,4,
                                             entry->iscsiInstIndex,
                                             entry->iscsiNodeIndex};
    oid iscsiTgtLastIntrFailureAddrType_oid[] = {OID_LIO_ISCSI_MIB,1,6,1,1,5,
                                                 entry->iscsiInstIndex,
                                                 entry->iscsiNodeIndex};
    oid iscsiTgtLastIntrFailureAddr_oid[] = {OID_LIO_ISCSI_MIB,1,6,1,1,6,
                                             entry->iscsiInstIndex,
                                             entry->iscsiNodeIndex};
    int fail_type_idx = entry->iscsiTgtLastFailureType_len - 1;

    /*
     * Prevent generating multiple traps within a short interval if an
     * initiator retries login over and over.
     */
    if (!strcmp(entry->iscsiTgtLastIntrFailureName,
                lastTrap.iscsiTgtLastIntrFailureName) &&
        (entry->iscsiTgtLastFailureType[fail_type_idx] ==
         lastTrap.iscsiTgtLastFailureType[fail_type_idx]) &&
        ((entry->iscsiTgtLastFailureTime - lastTrap.iscsiTgtLastFailureTime) <
         (120 * 100))) {
        return SNMP_ERR_NOERROR;
    }
    else {
        /* Save the failure info */
        memcpy(&lastTrap, entry, sizeof(lastTrap));
    }

    /*
     * Set the snmpTrapOid.0 value
     */
    snmp_varlist_add_variable(&var_list, snmptrap_oid, OID_LENGTH(snmptrap_oid),
                              ASN_OBJECT_ID, (u_char *)iscsiTgtLoginFailure_oid,
                              sizeof(iscsiTgtLoginFailure_oid));
    
    /*
     * Add objects from the trap definition
     */
    snmp_varlist_add_variable(&var_list, iscsiTgtLoginFailures_oid,
                              OID_LENGTH(iscsiTgtLoginFailures_oid),ASN_COUNTER,
                              (u_char *)&entry->iscsiTgtLoginFailures, 
                              sizeof(entry->iscsiTgtLoginFailures));
    snmp_varlist_add_variable(&var_list, iscsiTgtLastFailureType_oid,
                              OID_LENGTH(iscsiTgtLastFailureType_oid),
                              ASN_OBJECT_ID, 
                              (u_char *)entry->iscsiTgtLastFailureType, 
                              entry->iscsiTgtLastFailureType_len * sizeof(oid));
    snmp_varlist_add_variable(&var_list, iscsiTgtLastIntrFailureName_oid,
                              OID_LENGTH(iscsiTgtLastIntrFailureName_oid),
                              ASN_OCTET_STR, 
                              (u_char *)entry->iscsiTgtLastIntrFailureName,
                              strlen(entry->iscsiTgtLastIntrFailureName));
    snmp_varlist_add_variable(&var_list, iscsiTgtLastIntrFailureAddrType_oid,
                              OID_LENGTH(iscsiTgtLastIntrFailureAddrType_oid),
                              ASN_INTEGER,
                              (u_char *)&entry->iscsiTgtLastIntrFailureAddrType,
                              sizeof(entry->iscsiTgtLastIntrFailureAddrType));
    snmp_varlist_add_variable(&var_list, iscsiTgtLastIntrFailureAddr_oid,
                              OID_LENGTH(iscsiTgtLastIntrFailureAddr_oid),
                              ASN_OCTET_STR, 
                              (u_char *)entry->iscsiTgtLastIntrFailureAddr,
                              (entry->iscsiTgtLastIntrFailureAddrType ==
                              INET_ADDR_TYPE_IPV4)?  INET_ADDR_TYPE_IPV4_LEN:
                              sizeof(entry->iscsiTgtLastIntrFailureAddr));
    /*
     * Send the trap to the list of configured destinations and clean up
     */
    send_v2trap(var_list);
    snmp_free_varbind(var_list);

    return SNMP_ERR_NOERROR;
}


#define PROC_TARGET_ATTR "/proc/iscsi_target/mib/tgt_attr"
#define ISCSI_TARGET_ATTR_LINE "%lu %lu %lu %lu %u %s %s %08X"
static uint32_t numFailures[ISCSI_NUM_INSTANCES + 1][ISCSI_NUM_NODES + 1];
static oid iscsiTgtLoginStats_oid[] = {OID_LIO_ISCSI_MIB,1,6,2,1};

void
iscsiTargetAttributes_load(unsigned int clientreg, void *clientarg)
{
    FILE *fp;
    char line[300];
    struct iscsiTargetAttributes_entry tmp, *entry;
    char addrType[8];
    uint32_t addr;
    uint32_t failType;

    if (iscsiTargetAttributes_head)
        iscsiTargetAttributes_free();

    if (!(fp = fopen(PROC_TARGET_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_TARGET_ATTR);
        return;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_TARGET_ATTR_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiNodeIndex, &tmp.iscsiTgtLoginFailures,
                   &tmp.iscsiTgtLastFailureTime, &failType,
                   tmp.iscsiTgtLastIntrFailureName, addrType,
                   (u_int *)tmp.iscsiTgtLastIntrFailureAddr) != 8)
            continue;

        memcpy(tmp.iscsiTgtLastFailureType, iscsiTgtLoginStats_oid,
               sizeof(iscsiTgtLoginStats_oid)); 
        tmp.iscsiTgtLastFailureType[OID_LENGTH(iscsiTgtLoginStats_oid)] = 
                                                                       failType;
        tmp.iscsiTgtLastFailureType_len = OID_LENGTH(iscsiTgtLoginStats_oid)+1;

        if (!strcmp(addrType, "ipv4")) {
            tmp.iscsiTgtLastIntrFailureAddrType = INET_ADDR_TYPE_IPV4;
            addr = htonl(*(uint32_t *)tmp.iscsiTgtLastIntrFailureAddr);
            *(uint32_t *)tmp.iscsiTgtLastIntrFailureAddr = addr;
        }

        /* Send a trap on failures */
        if ((tmp.iscsiInstIndex <= ISCSI_NUM_INSTANCES) && 
            (tmp.iscsiNodeIndex <= ISCSI_NUM_NODES) &&
            (tmp.iscsiTgtLoginFailures > 
                        numFailures[tmp.iscsiInstIndex][tmp.iscsiNodeIndex])) {
            if ((clientreg) && ((failType == ISCSI_LOGIN_FAIL_AUTHORIZE) ||
                (failType == ISCSI_LOGIN_FAIL_AUTHENTICATE) ||
                (failType == ISCSI_LOGIN_FAIL_NEGOTIATE))) 
                send_iscsiTgtLoginFailure_trap(&tmp);
        }
        /* Update the counter to the current value from the stack */
        if (numFailures[tmp.iscsiInstIndex][tmp.iscsiNodeIndex] != 
                                                   tmp.iscsiTgtLoginFailures)
            numFailures[tmp.iscsiInstIndex][tmp.iscsiNodeIndex] = 
                                                   tmp.iscsiTgtLoginFailures;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiTargetAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiTargetAttributes_head;
        iscsiTargetAttributes_head = entry;
    }
    fclose(fp);
}

void
iscsiTargetAttributes_free(void)
{
    struct iscsiTargetAttributes_entry *entry;

    while (iscsiTargetAttributes_head) {
        entry = iscsiTargetAttributes_head;
        iscsiTargetAttributes_head = iscsiTargetAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Target Login Stats Table
 */
#define ISCSI_TGT_LOGIN_STATS_CACHE_TIMEOUT 5

/*
 * Initialize the iscsiTgtLoginStats table
 */
void
initialize_table_iscsiTgtLoginStats(void)
{
    static oid iscsiTgtLoginStats_oid[] = {OID_LIO_ISCSI_MIB,1,6,2};
    size_t iscsiTgtLoginStats_oid_len = OID_LENGTH(iscsiTgtLoginStats_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiTgtLoginStats",
                                              iscsiTgtLoginStats_handler,
                                              iscsiTgtLoginStats_oid,
                                              iscsiTgtLoginStats_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiNodeIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 8;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiTgtLoginStats_get_first_data_point;
    iinfo->get_next_data_point = iscsiTgtLoginStats_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                  netsnmp_get_cache_handler(ISCSI_TGT_LOGIN_STATS_CACHE_TIMEOUT,
                                            iscsiTgtLoginStats_load, 
                                            iscsiTgtLoginStats_free,
                                            iscsiTgtLoginStats_oid, 
                                            iscsiTgtLoginStats_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiTgtLoginStats_cache_update(void)
{
    static marker_t iscsiTgtLoginStats_cache_marker = NULL;

    if (iscsiTgtLoginStats_cache_marker &&
        (!atime_ready(iscsiTgtLoginStats_cache_marker,
                      ISCSI_TGT_LOGIN_STATS_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiTgtLoginStats_cache_marker)
        atime_setMarker(iscsiTgtLoginStats_cache_marker);
    else
        iscsiTgtLoginStats_cache_marker = atime_newMarker();

    iscsiTgtLoginStats_load(NULL, NULL);
}
#endif

struct iscsiTgtLoginStats_entry *iscsiTgtLoginStats_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiTgtLoginStats_get_first_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiTgtLoginStats_cache_update();
#endif
    *my_loop_context = iscsiTgtLoginStats_head;
    return iscsiTgtLoginStats_get_next_data_point(my_loop_context,
                                                  my_data_context,
                                                  put_index_data, mydata);
}

netsnmp_variable_list *
iscsiTgtLoginStats_get_next_data_point(void **my_loop_context,
                                       void **my_data_context,
                                       netsnmp_variable_list *put_index_data,
                                       netsnmp_iterator_info *mydata)
{
    struct iscsiTgtLoginStats_entry *entry =
                            (struct iscsiTgtLoginStats_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiNodeIndex,
                           sizeof(entry->iscsiNodeIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiTgtLoginStats table
 */
int
iscsiTgtLoginStats_handler(netsnmp_mib_handler *handler,
                           netsnmp_handler_registration *reginfo,
                           netsnmp_agent_request_info *reqinfo,
                           netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiTgtLoginStats_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiTgtLoginStats_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSITGTLOGINACCEPTS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLoginAccepts,
                          sizeof(table_entry->iscsiTgtLoginAccepts));
                break;
            case COLUMN_ISCSITGTLOGINOTHERFAILS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLoginOtherFails,
                          sizeof(table_entry->iscsiTgtLoginOtherFails));
                break;
            case COLUMN_ISCSITGTLOGINREDIRECTS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLoginRedirects,
                          sizeof(table_entry->iscsiTgtLoginRedirects));
                break;
            case COLUMN_ISCSITGTLOGINAUTHORIZEFAILS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLoginAuthorizeFails,
                          sizeof(table_entry->iscsiTgtLoginAuthorizeFails));
                break;
            case COLUMN_ISCSITGTLOGINAUTHENTICATEFAILS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                         (u_char *)&table_entry->iscsiTgtLoginAuthenticateFails,
                         sizeof(table_entry->iscsiTgtLoginAuthenticateFails));
                break;
            case COLUMN_ISCSITGTLOGINNEGOTIATEFAILS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLoginNegotiateFails,
                          sizeof(table_entry->iscsiTgtLoginNegotiateFails));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_TGT_LOGIN_STATS "/proc/iscsi_target/mib/login_stats"
#define ISCSI_TGT_LOGIN_STATS_LINE "%lu %lu %lu %lu %lu %lu %lu %lu"

int 
iscsiTgtLoginStats_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[128];
    struct iscsiTgtLoginStats_entry tmp, *entry;

    if (iscsiTgtLoginStats_head)
        iscsiTgtLoginStats_free(NULL, NULL);

    if (!(fp = fopen(PROC_TGT_LOGIN_STATS, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_TGT_LOGIN_STATS);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_TGT_LOGIN_STATS_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiNodeIndex, &tmp.iscsiTgtLoginAccepts,
                   &tmp.iscsiTgtLoginOtherFails, &tmp.iscsiTgtLoginRedirects,
                   &tmp.iscsiTgtLoginAuthorizeFails,
                   &tmp.iscsiTgtLoginAuthenticateFails,
                   &tmp.iscsiTgtLoginNegotiateFails) != 8)
            continue;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiTgtLoginStats_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiTgtLoginStats_head;
        iscsiTgtLoginStats_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiTgtLoginStats_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiTgtLoginStats_entry *entry;

    while (iscsiTgtLoginStats_head) {
        entry = iscsiTgtLoginStats_head;
        iscsiTgtLoginStats_head = iscsiTgtLoginStats_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Target Logout Stats Table
 */

#define ISCSI_TGT_LOGOUT_STATS_CACHE_TIMEOUT 5

/*
 * Initialize the iscsiTgtLogoutStats table
 */
void
initialize_table_iscsiTgtLogoutStats(void)
{
    static oid iscsiTgtLogoutStats_oid[] = {OID_LIO_ISCSI_MIB,1,6,3};
    size_t iscsiTgtLogoutStats_oid_len = OID_LENGTH(iscsiTgtLogoutStats_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiTgtLogoutStats",
                                              iscsiTgtLogoutStats_handler,
                                              iscsiTgtLogoutStats_oid,
                                              iscsiTgtLogoutStats_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiNodeIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 4;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiTgtLogoutStats_get_first_data_point;
    iinfo->get_next_data_point = iscsiTgtLogoutStats_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                 netsnmp_get_cache_handler(ISCSI_TGT_LOGOUT_STATS_CACHE_TIMEOUT,
                                           iscsiTgtLogoutStats_load, 
                                           iscsiTgtLogoutStats_free,
                                           iscsiTgtLogoutStats_oid, 
                                           iscsiTgtLogoutStats_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiTgtLogoutStats_cache_update(void)
{
    static marker_t iscsiTgtLogoutStats_cache_marker = NULL;

    if (iscsiTgtLogoutStats_cache_marker &&
        (!atime_ready(iscsiTgtLogoutStats_cache_marker,
                      ISCSI_TGT_LOGOUT_STATS_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiTgtLogoutStats_cache_marker)
        atime_setMarker(iscsiTgtLogoutStats_cache_marker);
    else
        iscsiTgtLogoutStats_cache_marker = atime_newMarker();

    iscsiTgtLogoutStats_load(NULL, NULL);
}
#endif

struct iscsiTgtLogoutStats_entry *iscsiTgtLogoutStats_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiTgtLogoutStats_get_first_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiTgtLogoutStats_cache_update();
#endif
    *my_loop_context = iscsiTgtLogoutStats_head;
    return iscsiTgtLogoutStats_get_next_data_point(my_loop_context,
                                                   my_data_context,
                                                   put_index_data, mydata);
}

netsnmp_variable_list *
iscsiTgtLogoutStats_get_next_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
    struct iscsiTgtLogoutStats_entry *entry =
                          (struct iscsiTgtLogoutStats_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiNodeIndex,
                           sizeof(entry->iscsiNodeIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiTgtLogoutStats table
 */
int
iscsiTgtLogoutStats_handler(netsnmp_mib_handler *handler,
                            netsnmp_handler_registration *reginfo,
                            netsnmp_agent_request_info *reqinfo,
                            netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiTgtLogoutStats_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiTgtLogoutStats_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSITGTLOGOUTNORMALS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLogoutNormals,
                          sizeof(table_entry->iscsiTgtLogoutNormals));
                break;
            case COLUMN_ISCSITGTLOGOUTOTHERS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiTgtLogoutOthers,
                          sizeof(table_entry->iscsiTgtLogoutOthers));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_TGT_LOGOUT_STATS "/proc/iscsi_target/mib/logout_stats"
#define ISCSI_TGT_LOGOUT_STATS_LINE "%lu %lu %lu %lu"

int 
iscsiTgtLogoutStats_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[64];
    struct iscsiTgtLogoutStats_entry tmp, *entry;

    if (iscsiTgtLogoutStats_head)
        iscsiTgtLogoutStats_free(NULL, NULL);

    if (!(fp = fopen(PROC_TGT_LOGOUT_STATS, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_TGT_LOGOUT_STATS);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_TGT_LOGOUT_STATS_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiNodeIndex, &tmp.iscsiTgtLogoutNormals,
                   &tmp.iscsiTgtLogoutOthers) != 4)
            continue;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiTgtLogoutStats_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiTgtLogoutStats_head;
        iscsiTgtLogoutStats_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiTgtLogoutStats_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiTgtLogoutStats_entry *entry;

    while (iscsiTgtLogoutStats_head) {
        entry = iscsiTgtLogoutStats_head;
        iscsiTgtLogoutStats_head = iscsiTgtLogoutStats_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Target Authorization Attributes Table
 */
#define ISCSI_TGT_AUTH_CACHE_TIMEOUT 10

/*
 * Initialize the iscsiTgtAuthAttributes table
 */
void
initialize_table_iscsiTgtAuthAttributes(void)
{
    static oid iscsiTgtAuthAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,7,1};
    size_t iscsiTgtAuthAttributes_oid_len =
                                        OID_LENGTH(iscsiTgtAuthAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiTgtAuthAttributes",
                                              iscsiTgtAuthAttributes_handler,
                                              iscsiTgtAuthAttributes_oid,
                                              iscsiTgtAuthAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiNodeIndex */
                                     ASN_UNSIGNED,  /* iscsiTgtAuthIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiTgtAuthAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiTgtAuthAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(ISCSI_TGT_AUTH_CACHE_TIMEOUT,
                                             iscsiTgtAuthAttributes_load, 
                                             iscsiTgtAuthAttributes_free,
                                             iscsiTgtAuthAttributes_oid, 
                                             iscsiTgtAuthAttributes_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiTgtAuthAttributes_cache_update(void)
{
    static marker_t iscsiTgtAuthAttributes_cache_marker = NULL;

    if (iscsiTgtAuthAttributes_cache_marker &&
        (!atime_ready(iscsiTgtAuthAttributes_cache_marker,
                      ISCSI_TGT_AUTH_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiTgtAuthAttributes_cache_marker)
        atime_setMarker(iscsiTgtAuthAttributes_cache_marker);
    else
        iscsiTgtAuthAttributes_cache_marker = atime_newMarker();

    iscsiTgtAuthAttributes_load(NULL, NULL);
}
#endif

struct iscsiTgtAuthAttributes_entry *iscsiTgtAuthAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiTgtAuthAttributes_get_first_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiTgtAuthAttributes_cache_update();
#endif
    *my_loop_context = iscsiTgtAuthAttributes_head;
    return iscsiTgtAuthAttributes_get_next_data_point(my_loop_context,
                                                      my_data_context,
                                                      put_index_data, mydata);
}

netsnmp_variable_list *
iscsiTgtAuthAttributes_get_next_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
    struct iscsiTgtAuthAttributes_entry *entry =
                        (struct iscsiTgtAuthAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiNodeIndex,
                           sizeof(entry->iscsiNodeIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiTgtAuthIndex,
                           sizeof(entry->iscsiTgtAuthIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiTgtAuthAttributes table
 */
int
iscsiTgtAuthAttributes_handler(netsnmp_mib_handler *handler,
                               netsnmp_handler_registration *reginfo,
                               netsnmp_agent_request_info *reqinfo,
                               netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiTgtAuthAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiTgtAuthAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSITGTAUTHINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiTgtAuthIndex,
                          sizeof(table_entry->iscsiTgtAuthIndex));
                break;
            case COLUMN_ISCSITGTAUTHROWSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiTgtAuthRowStatus,
                          sizeof(table_entry->iscsiTgtAuthRowStatus));
                break;
            case COLUMN_ISCSITGTAUTHIDENTITY:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                          (u_char *)&table_entry->iscsiTgtAuthIdentity,
                          table_entry->iscsiTgtAuthIdentity_len * sizeof(oid));
                break;
            case COLUMN_ISCSITGTAUTHSTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiTgtAuthStorageType,
                          sizeof(table_entry->iscsiTgtAuthStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_ISCSI_TGT_AUTH "/proc/iscsi_target/mib/tgt_auth"
#define ISCSI_TGT_AUTH_LINE "%lu %lu %lu %s"
static oid ipsAuthIdentDesc_oid[] = {OID_LIO_IPS_AUTH_MIB,1,3,1,1,2};

int 
iscsiTgtAuthAttributes_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    char intrName[ISCSI_MAX_NAME_LEN];
    struct iscsiTgtAuthAttributes_entry tmp, *entry;

    if (iscsiTgtAuthAttributes_head)
        iscsiTgtAuthAttributes_free(NULL, NULL);

    if (!(fp = fopen(PROC_ISCSI_TGT_AUTH, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_ISCSI_TGT_AUTH);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        uint32_t idenIndex = 0;
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_TGT_AUTH_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiNodeIndex, &tmp.iscsiTgtAuthIndex, intrName) != 4)
            continue;

	if (intrName[0]) {
            idenIndex = find_authId_index(intrName);
        }
        if (idenIndex) {
            int oidLen = OID_LENGTH(ipsAuthIdentDesc_oid);
            memcpy(tmp.iscsiTgtAuthIdentity, ipsAuthIdentDesc_oid,
                   sizeof(ipsAuthIdentDesc_oid)); 
            tmp.iscsiTgtAuthIdentity[oidLen] = idenIndex;
            tmp.iscsiTgtAuthIdentity_len = oidLen + 1;
        }
        else {
            /* return {0.0} */
            tmp.iscsiTgtAuthIdentity_len = 2;
        }
        tmp.iscsiTgtAuthRowStatus = RS_ACTIVE;
        tmp.iscsiTgtAuthStorageType = ST_READONLY;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiTgtAuthAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiTgtAuthAttributes_head;
        iscsiTgtAuthAttributes_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiTgtAuthAttributes_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiTgtAuthAttributes_entry *entry;

    while (iscsiTgtAuthAttributes_head) {
        entry = iscsiTgtAuthAttributes_head;
        iscsiTgtAuthAttributes_head = iscsiTgtAuthAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Session Attributes Table
 */

#define ISCSI_SESSION_ATTR_CACHE_TIMEOUT 10

/*
 * Initialize the iscsiSessionAttributes table
 */
void
initialize_table_iscsiSessionAttributes(void)
{
    static oid iscsiSessionAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,10,1};
    size_t iscsiSessionAttributes_oid_len =
                                         OID_LENGTH(iscsiSessionAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiSessionAttributes",
                                              iscsiSessionAttributes_handler,
                                              iscsiSessionAttributes_oid,
                                              iscsiSessionAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                           ASN_UNSIGNED,  /* iscsiInstIndex */
                           ASN_UNSIGNED,  /* iscsiSsnNodeIndex */
                           ASN_UNSIGNED,  /* iscsiSsnIndex */
                           0);
    table_info->min_column = 1;
    table_info->max_column = 22;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiSessionAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiSessionAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(ISCSI_SESSION_ATTR_CACHE_TIMEOUT,
                                             iscsiSessionAttributes_load, 
                                             iscsiSessionAttributes_free,
                                             iscsiSessionAttributes_oid, 
                                             iscsiSessionAttributes_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiSessionAttributes_cache_update(void)
{
    static marker_t iscsiSessionAttributes_cache_marker = NULL;

    if (iscsiSessionAttributes_cache_marker &&
        (!atime_ready(iscsiSessionAttributes_cache_marker,
                      ISCSI_SESSION_ATTR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiSessionAttributes_cache_marker)
        atime_setMarker(iscsiSessionAttributes_cache_marker);
    else
        iscsiSessionAttributes_cache_marker = atime_newMarker();

    iscsiSessionAttributes_load(NULL, NULL);
}
#endif

struct iscsiSessionAttributes_entry *iscsiSessionAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiSessionAttributes_get_first_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiSessionAttributes_cache_update();
#endif
    *my_loop_context = iscsiSessionAttributes_head;
    return iscsiSessionAttributes_get_next_data_point(my_loop_context,
                                                      my_data_context,
                                                      put_index_data, mydata);
}

netsnmp_variable_list *
iscsiSessionAttributes_get_next_data_point(void **my_loop_context,
                          void **my_data_context,
                          netsnmp_variable_list *put_index_data,
                          netsnmp_iterator_info *mydata)
{
    struct iscsiSessionAttributes_entry *entry =
                        (struct iscsiSessionAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnNodeIndex,
                           sizeof(entry->iscsiSsnNodeIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnIndex,
                           sizeof(entry->iscsiSsnIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiSessionAttributes table
 */
int
iscsiSessionAttributes_handler(netsnmp_mib_handler *handler,
                               netsnmp_handler_registration *reginfo,
                               netsnmp_agent_request_info *reqinfo,
                               netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiSessionAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiSessionAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSISSNNODEINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiSsnNodeIndex,
                          sizeof(table_entry->iscsiSsnNodeIndex));
                break;
            case COLUMN_ISCSISSNINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiSsnIndex,
                          sizeof(table_entry->iscsiSsnIndex));
                break;
            case COLUMN_ISCSISSNDIRECTION:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiSsnDirection,
                          sizeof(table_entry->iscsiSsnDirection));
                break;
            case COLUMN_ISCSISSNINITIATORNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiSsnInitiatorName,
                          strlen(table_entry->iscsiSsnInitiatorName));
                break;
            case COLUMN_ISCSISSNTARGETNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiSsnTargetName,
                          strlen(table_entry->iscsiSsnTargetName));
                break;
            case COLUMN_ISCSISSNTSIH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiSsnTSIH,
                          sizeof(table_entry->iscsiSsnTSIH));
                break;
            case COLUMN_ISCSISSNISID:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiSsnISID,
                          sizeof(table_entry->iscsiSsnISID));
                break;
            case COLUMN_ISCSISSNINITIATORALIAS:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiSsnInitiatorAlias,
                          strlen(table_entry->iscsiSsnInitiatorAlias));
                break;
            case COLUMN_ISCSISSNTARGETALIAS:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->iscsiSsnTargetAlias,
                          strlen(table_entry->iscsiSsnTargetAlias));
                break;
            case COLUMN_ISCSISSNINITIALR2T:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiSsnInitialR2T,
                          sizeof(table_entry->iscsiSsnInitialR2T));
                break;
            case COLUMN_ISCSISSNIMMEDIATEDATA:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiSsnImmediateData,
                          sizeof(table_entry->iscsiSsnImmediateData));
                break;
            case COLUMN_ISCSISSNTYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiSsnType,
                          sizeof(table_entry->iscsiSsnType));
                break;
            case COLUMN_ISCSISSNMAXOUTSTANDINGR2T:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiSsnMaxOutstandingR2T,
                          sizeof(table_entry->iscsiSsnMaxOutstandingR2T));
                break;
            case COLUMN_ISCSISSNFIRSTBURSTLENGTH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiSsnFirstBurstLength,
                          sizeof(table_entry->iscsiSsnFirstBurstLength));
                break;
            case COLUMN_ISCSISSNMAXBURSTLENGTH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiSsnMaxBurstLength,
                          sizeof(table_entry->iscsiSsnMaxBurstLength));
                break;
            case COLUMN_ISCSISSNCONNECTIONNUMBER:
                snmp_set_var_typed_value(request->requestvb, ASN_GAUGE,
                          (u_char *)&table_entry->iscsiSsnConnectionNumber,
                          sizeof(table_entry->iscsiSsnConnectionNumber));
                break;
            case COLUMN_ISCSISSNAUTHIDENTITY:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                          (u_char *)&table_entry->iscsiSsnAuthIdentity,
                          table_entry->iscsiSsnAuthIdentity_len * sizeof(oid));
                break;
            case COLUMN_ISCSISSNDATASEQUENCEINORDER:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiSsnDataSequenceInOrder,
                          sizeof(table_entry->iscsiSsnDataSequenceInOrder));
                break;
            case COLUMN_ISCSISSNDATAPDUINORDER:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiSsnDataPDUInOrder,
                          sizeof(table_entry->iscsiSsnDataPDUInOrder));
                break;
            case COLUMN_ISCSISSNERRORRECOVERYLEVEL:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiSsnErrorRecoveryLevel,
                          sizeof(table_entry->iscsiSsnErrorRecoveryLevel));
                break;
            case COLUMN_ISCSISSNDISCONTINUITYTIME:
                snmp_set_var_typed_value(request->requestvb, ASN_TIMETICKS,
                          (u_char *)&table_entry->iscsiSsnDiscontinuityTime,
                          sizeof(table_entry->iscsiSsnDiscontinuityTime));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SESSION_ATTR "/proc/iscsi_target/mib/sess_attr"
#define ISCSI_SESSION_ATTR_LINE "%lu %lu %lu %s %s %s %lu %02X %02X %02X %02X %02X %02X %s %s %s %lu %lu %lu %lu %s %s %s %lu %lu"
static oid ipsAuthMethodNone_oid[] = {OID_LIO_IPS_AUTH_MIB,1,1,1,1};

int 
iscsiSessionAttributes_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    char direction[12];
    char r2t[4];
    char immData[4];
    char ssnType[12];
    char seqOrder[4];
    char pduOrder[4];
    char authType[8]; 
    struct iscsiSessionAttributes_entry tmp, *entry;

    if (iscsiSessionAttributes_head)
        iscsiSessionAttributes_free(NULL, NULL);

    if (!(fp = fopen(PROC_SESSION_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SESSION_ATTR);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_SESSION_ATTR_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiSsnNodeIndex, &tmp.iscsiSsnIndex, direction,
                   tmp.iscsiSsnInitiatorName, tmp.iscsiSsnTargetName,
                   &tmp.iscsiSsnTSIH, (u_int *)&tmp.iscsiSsnISID[0], 
                   (u_int *)&tmp.iscsiSsnISID[1], (u_int *)&tmp.iscsiSsnISID[2],
                   (u_int *)&tmp.iscsiSsnISID[3], (u_int *)&tmp.iscsiSsnISID[4],
                   (u_int *)&tmp.iscsiSsnISID[5], r2t, immData, ssnType,
                   &tmp.iscsiSsnMaxOutstandingR2T, 
                   &tmp.iscsiSsnFirstBurstLength, &tmp.iscsiSsnMaxBurstLength,
                   &tmp.iscsiSsnConnectionNumber, authType, seqOrder, pduOrder,
                   &tmp.iscsiSsnErrorRecoveryLevel,
                   &tmp.iscsiSsnDiscontinuityTime) != 25)
            continue;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "intr_alias: %s", tmp.iscsiSsnInitiatorAlias) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.iscsiSsnInitiatorAlias, line + strlen("intr_alias: "));
            if (!strcmp(tmp.iscsiSsnInitiatorAlias, "None"))
                tmp.iscsiSsnInitiatorAlias[0] = 0;
        }
        else
            break;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "tgt_alias: %s", tmp.iscsiSsnTargetAlias) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.iscsiSsnTargetAlias, line + strlen("tgt_alias: "));
        }
        else
            break;

        tmp.iscsiSsnDirection = SSN_DIR_INBOUND;

        if (!strcmp(r2t, "Yes"))
            tmp.iscsiSsnInitialR2T = TV_TRUE;
        else
            tmp.iscsiSsnInitialR2T = TV_FALSE;

        if (!strcmp(immData, "Yes"))
            tmp.iscsiSsnImmediateData = TV_TRUE;
        else
            tmp.iscsiSsnImmediateData = TV_FALSE;

        if (!strcmp(ssnType, "Normal"))
            tmp.iscsiSsnType = SSN_TYPE_NORMAL;
        else if (!strcmp(ssnType, "Discovery"))
            tmp.iscsiSsnType = SSN_TYPE_DISCOVERY;

        tmp.iscsiSsnAuthIdentity_len = OID_LENGTH(ipsAuthMethodNone_oid);
        memcpy(tmp.iscsiSsnAuthIdentity, ipsAuthMethodNone_oid,
               sizeof(ipsAuthMethodNone_oid));
        if (!strcmp(authType, "CHAP")) {
            tmp.iscsiSsnAuthIdentity[tmp.iscsiSsnAuthIdentity_len - 1] = 3;
        }

        if (!strcmp(seqOrder, "Yes"))
            tmp.iscsiSsnDataSequenceInOrder = TV_TRUE;
        else
            tmp.iscsiSsnDataSequenceInOrder = TV_FALSE;

        if (!strcmp(pduOrder, "Yes"))
            tmp.iscsiSsnDataPDUInOrder = TV_TRUE;
        else
            tmp.iscsiSsnDataPDUInOrder = TV_FALSE;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiSessionAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiSessionAttributes_head;
        iscsiSessionAttributes_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiSessionAttributes_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiSessionAttributes_entry *entry;

    while (iscsiSessionAttributes_head) {
        entry = iscsiSessionAttributes_head;
        iscsiSessionAttributes_head = iscsiSessionAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Session Stats Table
 */

#define ISCSI_SESSION_STATS_CACHE_TIMEOUT 5

/*
 * Initialize the iscsiSessionStats table
 */
void
initialize_table_iscsiSessionStats(void)
{
    static oid iscsiSessionStats_oid[] = {OID_LIO_ISCSI_MIB,1,10,2};
    size_t iscsiSessionStats_oid_len = OID_LENGTH(iscsiSessionStats_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiSessionStats",
                                              iscsiSessionStats_handler,
                                              iscsiSessionStats_oid,
                                              iscsiSessionStats_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiSsnNodeIndex */
                                     ASN_UNSIGNED,  /* iscsiSsnIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 9;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiSessionStats_get_first_data_point;
    iinfo->get_next_data_point = iscsiSessionStats_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(ISCSI_SESSION_STATS_CACHE_TIMEOUT,
                                             iscsiSessionStats_load, 
                                             iscsiSessionStats_free,
                                             iscsiSessionStats_oid, 
                                             iscsiSessionStats_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiSessionStats_cache_update(void)
{
    static marker_t iscsiSessionStats_cache_marker = NULL;

    if (iscsiSessionStats_cache_marker &&
        (!atime_ready(iscsiSessionStats_cache_marker,
                      ISCSI_SESSION_STATS_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiSessionStats_cache_marker)
        atime_setMarker(iscsiSessionStats_cache_marker);
    else
        iscsiSessionStats_cache_marker = atime_newMarker();

    iscsiSessionStats_load(NULL, NULL);
}
#endif

struct iscsiSessionStats_entry *iscsiSessionStats_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiSessionStats_get_first_data_point(void **my_loop_context,
                                       void **my_data_context,
                                       netsnmp_variable_list *put_index_data,
                                       netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiSessionStats_cache_update();
#endif
    *my_loop_context = iscsiSessionStats_head;
    return iscsiSessionStats_get_next_data_point(my_loop_context,
                                                 my_data_context,
                                                 put_index_data, mydata);
}

netsnmp_variable_list *
iscsiSessionStats_get_next_data_point(void **my_loop_context,
                                      void **my_data_context,
                                      netsnmp_variable_list *put_index_data,
                                      netsnmp_iterator_info *mydata)
{
    struct iscsiSessionStats_entry *entry =
                            (struct iscsiSessionStats_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnNodeIndex,
                           sizeof(entry->iscsiSsnNodeIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnIndex,
                           sizeof(entry->iscsiSsnIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiSessionStats table
 */
int
iscsiSessionStats_handler(netsnmp_mib_handler *handler,
                          netsnmp_handler_registration *reginfo,
                          netsnmp_agent_request_info *reqinfo,
                          netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiSessionStats_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiSessionStats_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;

            switch (table_info->colnum) {
            case COLUMN_ISCSISSNCMDPDUS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiSsnCmdPDUs,
                          sizeof(table_entry->iscsiSsnCmdPDUs));
                break;
            case COLUMN_ISCSISSNRSPPDUS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiSsnRspPDUs,
                          sizeof(table_entry->iscsiSsnRspPDUs));
                break;
            case COLUMN_ISCSISSNTXDATAOCTETS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER64,
                          (u_char *)&table_entry->iscsiSsnTxDataOctets,
                          sizeof(table_entry->iscsiSsnTxDataOctets));
                break;
            case COLUMN_ISCSISSNRXDATAOCTETS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER64,
                          (u_char *)&table_entry->iscsiSsnRxDataOctets,
                          sizeof(table_entry->iscsiSsnRxDataOctets));
                break;
            case COLUMN_ISCSISSNLCTXDATAOCTETS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiSsnLCTxDataOctets,
                          sizeof(table_entry->iscsiSsnLCTxDataOctets));
                break;
            case COLUMN_ISCSISSNLCRXDATAOCTETS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiSsnLCRxDataOctets,
                          sizeof(table_entry->iscsiSsnLCRxDataOctets));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SESSION_STATS "/proc/iscsi_target/mib/sess_stats"
#define ISCSI_SESSION_STATS_LINE_32 "%lu %lu %lu %lu %lu %llu %llu"
#define ISCSI_SESSION_STATS_LINE_64 "%lu %lu %lu %lu %lu %lu %lu"

int 
iscsiSessionStats_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[128];
    struct iscsiSessionStats_entry tmp, *entry;
    u_int64_t txOctets, rxOctets;

    if (iscsiSessionStats_head)
        iscsiSessionStats_free(NULL, NULL);

    if (!(fp = fopen(PROC_SESSION_STATS, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SESSION_STATS);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, (sizeof(long) == 8)? ISCSI_SESSION_STATS_LINE_64 :
                   ISCSI_SESSION_STATS_LINE_32, &tmp.iscsiInstIndex,
                   &tmp.iscsiSsnNodeIndex, &tmp.iscsiSsnIndex, 
                   &tmp.iscsiSsnCmdPDUs, &tmp.iscsiSsnRspPDUs,
                   &txOctets, &rxOctets) != 7)
            continue;

        tmp.iscsiSsnTxDataOctets.high = (txOctets >> 32) & 0xffffffff;
        tmp.iscsiSsnTxDataOctets.low = txOctets & 0xffffffff;

        tmp.iscsiSsnRxDataOctets.high = (rxOctets >> 32) & 0xffffffff;
        tmp.iscsiSsnRxDataOctets.low = rxOctets & 0xffffffff;

        tmp.iscsiSsnLCTxDataOctets = tmp.iscsiSsnTxDataOctets.low;
        tmp.iscsiSsnLCRxDataOctets = tmp.iscsiSsnRxDataOctets.low;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiSessionStats_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiSessionStats_head;
        iscsiSessionStats_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiSessionStats_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiSessionStats_entry *entry;

    while (iscsiSessionStats_head) {
        entry = iscsiSessionStats_head;
        iscsiSessionStats_head = iscsiSessionStats_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Session Connection Error Stats Table
 */

#define ISCSI_SSN_CXN_ERR_CACHE_TIMEOUT 5

/*
 * Initialize the iscsiSsnCxnErrStats table
 */
void
initialize_table_iscsiSsnCxnErrStats(void)
{
    static oid iscsiSsnCxnErrStats_oid[] = {OID_LIO_ISCSI_MIB,1,10,3};
    size_t iscsiSsnCxnErrStats_oid_len = OID_LENGTH(iscsiSsnCxnErrStats_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiSsnCxnErrStats",
                                              iscsiSsnCxnErrStats_handler,
                                              iscsiSsnCxnErrStats_oid,
                                              iscsiSsnCxnErrStats_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiSsnNodeIndex */
                                     ASN_UNSIGNED,  /* iscsiSsnIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 5;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiSsnCxnErrStats_get_first_data_point;
    iinfo->get_next_data_point = iscsiSsnCxnErrStats_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(ISCSI_SSN_CXN_ERR_CACHE_TIMEOUT,
                                             iscsiSsnCxnErrStats_load, 
                                             iscsiSsnCxnErrStats_free,
                                             iscsiSsnCxnErrStats_oid, 
                                             iscsiSsnCxnErrStats_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiSsnCxnErrStats_cache_update(void)
{
    static marker_t iscsiSsnCxnErrStats_cache_marker = NULL;

    if (iscsiSsnCxnErrStats_cache_marker &&
        (!atime_ready(iscsiSsnCxnErrStats_cache_marker,
                      ISCSI_SSN_CXN_ERR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiSsnCxnErrStats_cache_marker)
        atime_setMarker(iscsiSsnCxnErrStats_cache_marker);
    else
        iscsiSsnCxnErrStats_cache_marker = atime_newMarker();

    iscsiSsnCxnErrStats_load(NULL, NULL);
}
#endif

struct iscsiSsnCxnErrStats_entry *iscsiSsnCxnErrStats_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiSsnCxnErrStats_get_first_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiSsnCxnErrStats_cache_update();
#endif
    *my_loop_context = iscsiSsnCxnErrStats_head;
    return iscsiSsnCxnErrStats_get_next_data_point(my_loop_context,
                                                   my_data_context,
                                                   put_index_data, mydata);
}

netsnmp_variable_list *
iscsiSsnCxnErrStats_get_next_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
    struct iscsiSsnCxnErrStats_entry *entry =
                          (struct iscsiSsnCxnErrStats_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnNodeIndex,
                           sizeof(entry->iscsiSsnNodeIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnIndex,
                           sizeof(entry->iscsiSsnIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiSsnCxnErrStats table
 */
int
iscsiSsnCxnErrStats_handler(netsnmp_mib_handler *handler,
                            netsnmp_handler_registration *reginfo,
                            netsnmp_agent_request_info *reqinfo,
                            netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiSsnCxnErrStats_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiSsnCxnErrStats_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSISSNCXNDIGESTERRORS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiSsnCxnDigestErrors,
                          sizeof(table_entry->iscsiSsnCxnDigestErrors));
                break;
            case COLUMN_ISCSISSNCXNTIMEOUTERRORS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->iscsiSsnCxnTimeoutErrors,
                          sizeof(table_entry->iscsiSsnCxnTimeoutErrors));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SSN_CXN_ERR_STATS "/proc/iscsi_target/mib/sess_conn_err_stats"
#define ISCSI_SSN_CXN_ERR_STATS_LINE "%lu %lu %lu %lu %lu"

int 
iscsiSsnCxnErrStats_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[64];
    struct iscsiSsnCxnErrStats_entry tmp, *entry;

    if (iscsiSsnCxnErrStats_head)
        iscsiSsnCxnErrStats_free(NULL, NULL);

    if (!(fp = fopen(PROC_SSN_CXN_ERR_STATS, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n",PROC_SSN_CXN_ERR_STATS);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_SSN_CXN_ERR_STATS_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiSsnNodeIndex, &tmp.iscsiSsnIndex, 
                   &tmp.iscsiSsnCxnDigestErrors, 
                   &tmp.iscsiSsnCxnTimeoutErrors) != 5)
            continue;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiSsnCxnErrStats_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiSsnCxnErrStats_head;
        iscsiSsnCxnErrStats_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiSsnCxnErrStats_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiSsnCxnErrStats_entry *entry;

    while (iscsiSsnCxnErrStats_head) {
        entry = iscsiSsnCxnErrStats_head;
        iscsiSsnCxnErrStats_head = iscsiSsnCxnErrStats_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Connection Attributes Table
 */

#define ISCSI_CXN_ATTR_CACHE_TIMEOUT 10

/*
 * Initialize the iscsiCxnAttributes table
 */
void
initialize_table_iscsiCxnAttributes(void)
{
    static oid iscsiCxnAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,11,1};
    size_t iscsiCxnAttributes_oid_len = OID_LENGTH(iscsiCxnAttributes_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("iscsiCxnAttributes",
                                              iscsiCxnAttributes_handler,
                                              iscsiCxnAttributes_oid,
                                              iscsiCxnAttributes_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* iscsiInstIndex */
                                     ASN_UNSIGNED,  /* iscsiSsnNodeIndex */
                                     ASN_UNSIGNED,  /* iscsiSsnIndex */
                                     ASN_UNSIGNED,  /* iscsiCxnIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 19;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = iscsiCxnAttributes_get_first_data_point;
    iinfo->get_next_data_point = iscsiCxnAttributes_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(ISCSI_CXN_ATTR_CACHE_TIMEOUT,
                                             iscsiCxnAttributes_load, 
                                             iscsiCxnAttributes_free,
                                             iscsiCxnAttributes_oid, 
                                             iscsiCxnAttributes_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
iscsiCxnAttributes_cache_update(void)
{
    static marker_t iscsiCxnAttributes_cache_marker = NULL;

    if (iscsiCxnAttributes_cache_marker &&
        (!atime_ready(iscsiCxnAttributes_cache_marker,
                      ISCSI_CXN_ATTR_CACHE_TIMEOUT * 1000)))
        return;

    if (iscsiCxnAttributes_cache_marker)
        atime_setMarker(iscsiCxnAttributes_cache_marker);
    else
        iscsiCxnAttributes_cache_marker = atime_newMarker();

    iscsiCxnAttributes_load(NULL, NULL);
}
#endif

struct iscsiCxnAttributes_entry *iscsiCxnAttributes_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
iscsiCxnAttributes_get_first_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    iscsiCxnAttributes_cache_update();
#endif
    *my_loop_context = iscsiCxnAttributes_head;
    return iscsiCxnAttributes_get_next_data_point(my_loop_context,
                                                  my_data_context,
                                                  put_index_data, mydata);
}

netsnmp_variable_list *
iscsiCxnAttributes_get_next_data_point(void **my_loop_context,
                                       void **my_data_context,
                                       netsnmp_variable_list *put_index_data,
                                       netsnmp_iterator_info *mydata)
{
    struct iscsiCxnAttributes_entry *entry =
                           (struct iscsiCxnAttributes_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->iscsiInstIndex,
                           sizeof(entry->iscsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnNodeIndex,
                           sizeof(entry->iscsiSsnNodeIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiSsnIndex,
                           sizeof(entry->iscsiSsnIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->iscsiCxnIndex,
                           sizeof(entry->iscsiCxnIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the iscsiCxnAttributes table
 */
int
iscsiCxnAttributes_handler(netsnmp_mib_handler *handler,
                           netsnmp_handler_registration *reginfo,
                           netsnmp_agent_request_info *reqinfo,
                           netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct iscsiCxnAttributes_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct iscsiCxnAttributes_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_ISCSICXNINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnIndex,
                          sizeof(table_entry->iscsiCxnIndex));
                break;
            case COLUMN_ISCSICXNCID:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnCid,
                          sizeof(table_entry->iscsiCxnCid));
                break;
            case COLUMN_ISCSICXNSTATE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiCxnState,
                          sizeof(table_entry->iscsiCxnState));
                break;
            case COLUMN_ISCSICXNADDRTYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiCxnAddrType,
                          sizeof(table_entry->iscsiCxnAddrType));
                break;
            case COLUMN_ISCSICXNLOCALADDR:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                        (u_char *)table_entry->iscsiCxnLocalAddr,
                        (table_entry->iscsiCxnAddrType == INET_ADDR_TYPE_IPV4)?
                        INET_ADDR_TYPE_IPV4_LEN:
                        sizeof(table_entry->iscsiCxnLocalAddr));
                break;
            case COLUMN_ISCSICXNPROTOCOL:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnProtocol,
                          sizeof(table_entry->iscsiCxnProtocol));
                break;
            case COLUMN_ISCSICXNLOCALPORT:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnLocalPort,
                          sizeof(table_entry->iscsiCxnLocalPort));
                break;
            case COLUMN_ISCSICXNREMOTEADDR:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                        (u_char *)table_entry->iscsiCxnRemoteAddr,
                        (table_entry->iscsiCxnAddrType == INET_ADDR_TYPE_IPV4)?
                        INET_ADDR_TYPE_IPV4_LEN:
                        sizeof(table_entry->iscsiCxnRemoteAddr));
                break;
            case COLUMN_ISCSICXNREMOTEPORT:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnRemotePort,
                          sizeof(table_entry->iscsiCxnRemotePort));
                break;
            case COLUMN_ISCSICXNMAXRECVDATASEGLENGTH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnMaxRecvDataSegLength,
                          sizeof(table_entry->iscsiCxnMaxRecvDataSegLength));
                break;
            case COLUMN_ISCSICXNMAXXMITDATASEGLENGTH:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnMaxXmitDataSegLength,
                          sizeof(table_entry->iscsiCxnMaxXmitDataSegLength));
                break;
            case COLUMN_ISCSICXNHEADERINTEGRITY:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiCxnHeaderIntegrity,
                          sizeof(table_entry->iscsiCxnHeaderIntegrity));
                break;
            case COLUMN_ISCSICXNDATAINTEGRITY:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiCxnDataIntegrity,
                          sizeof(table_entry->iscsiCxnDataIntegrity));
                break;
            case COLUMN_ISCSICXNRECVMARKER:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiCxnRecvMarker,
                          sizeof(table_entry->iscsiCxnRecvMarker));
                break;
            case COLUMN_ISCSICXNSENDMARKER:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->iscsiCxnSendMarker,
                          sizeof(table_entry->iscsiCxnSendMarker));
                break;
            case COLUMN_ISCSICXNVERSIONACTIVE:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->iscsiCxnVersionActive,
                          sizeof(table_entry->iscsiCxnVersionActive));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_CXN_ATTR "/proc/iscsi_target/mib/conn_attr"
#define ISCSI_CXN_ATTR_LINE "%lu %lu %lu %lu %lu %s %s %08X %s %lu %08X %lu %lu %lu %s %s %s %s %lu"

int 
iscsiCxnAttributes_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    char cxnState[8];
    char addrType[12];
    char proto[8];
    char hdrDgst[16];
    char dataDgst[16];
    char rcvMarker[4];
    char sendMarker[4];
    uint32_t addr;
    struct iscsiCxnAttributes_entry tmp, *entry;

    if (iscsiCxnAttributes_head)
        iscsiCxnAttributes_free(NULL, NULL);

    if (!(fp = fopen(PROC_CXN_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_CXN_ATTR);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_CXN_ATTR_LINE, &tmp.iscsiInstIndex,
                   &tmp.iscsiSsnNodeIndex, &tmp.iscsiSsnIndex,
                   &tmp.iscsiCxnIndex, &tmp.iscsiCxnCid, cxnState, addrType,
                   (u_int *)tmp.iscsiCxnLocalAddr, proto,
                   &tmp.iscsiCxnLocalPort, (u_int *)tmp.iscsiCxnRemoteAddr,
                   &tmp.iscsiCxnRemotePort, &tmp.iscsiCxnMaxRecvDataSegLength,
                   &tmp.iscsiCxnMaxXmitDataSegLength, hdrDgst, dataDgst,
                   rcvMarker, sendMarker, &tmp.iscsiCxnVersionActive) != 19)
            continue;

        if (!strcmp(cxnState, "login"))
            tmp.iscsiCxnState = CXN_STATE_LOGIN;
        else if (!strcmp(cxnState, "full"))
            tmp.iscsiCxnState = CXN_STATE_FULL;
        else if (!strcmp(cxnState, "logout"))
            tmp.iscsiCxnState = CXN_STATE_LOGOUT;

        if (!strcmp(addrType, "ipv4")) {
            tmp.iscsiCxnAddrType = INET_ADDR_TYPE_IPV4;

            addr = htonl(*(uint32_t *)tmp.iscsiCxnLocalAddr);
            *(uint32_t *)tmp.iscsiCxnLocalAddr = addr;

            addr = htonl(*(uint32_t *)tmp.iscsiCxnRemoteAddr);
            *(uint32_t *)tmp.iscsiCxnRemoteAddr = addr;
        }

        if (!strcmp(proto, "TCP"))
            tmp.iscsiCxnProtocol = TRANSPORT_PROTO_TCP;
        else if (!strcmp(proto, "SCTP"))
            tmp.iscsiCxnProtocol = TRANSPORT_PROTO_SCTP;

        if (!strcmp(hdrDgst, "CRC32C"))
            tmp.iscsiCxnHeaderIntegrity = ISCSI_DIGEST_CRC32C;
        else if (!strcmp(hdrDgst, "None"))
            tmp.iscsiCxnHeaderIntegrity = ISCSI_DIGEST_NODIGEST;
        else
            tmp.iscsiCxnHeaderIntegrity = ISCSI_DIGEST_OTHER;

        if (!strcmp(dataDgst, "CRC32C"))
            tmp.iscsiCxnDataIntegrity = ISCSI_DIGEST_CRC32C;
        else if (!strcmp(dataDgst, "None"))
            tmp.iscsiCxnDataIntegrity = ISCSI_DIGEST_NODIGEST;
        else
            tmp.iscsiCxnDataIntegrity = ISCSI_DIGEST_OTHER;

        if (!strcmp(rcvMarker, "Yes"))
            tmp.iscsiCxnRecvMarker = TV_TRUE;
        else
            tmp.iscsiCxnRecvMarker = TV_FALSE;

        if (!strcmp(sendMarker, "Yes"))
            tmp.iscsiCxnSendMarker = TV_TRUE;
        else
            tmp.iscsiCxnSendMarker = TV_FALSE;

        entry = SNMP_MALLOC_TYPEDEF(struct iscsiCxnAttributes_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = iscsiCxnAttributes_head;
        iscsiCxnAttributes_head = entry;
    }
    fclose(fp);
    return 0;
}

void
iscsiCxnAttributes_free(netsnmp_cache *cache, void *vmagic)
{
    struct iscsiCxnAttributes_entry *entry;

    while (iscsiCxnAttributes_head) {
        entry = iscsiCxnAttributes_head;
        iscsiCxnAttributes_head = iscsiCxnAttributes_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Session Failure Notification
 */

/* Use 3 sec poll recommended by the draft */
#define ISCSI_SSN_FAIL_POLL_INTERVAL 3

void iscsiInstSessionFailure_load(unsigned int clientreg, void *clientarg);

/* Initializes the iscsiInstSessionFailure module */
void
initialize_iscsiInstSessionFailure(void)
{
    /* Setup callback for polling for login failure */
    snmp_alarm_register(ISCSI_SSN_FAIL_POLL_INTERVAL, SA_REPEAT,
                        iscsiInstSessionFailure_load, NULL);
    /* Initial load */
    iscsiInstSessionFailure_load(0, NULL);
}

int
send_iscsiInstSessionFailure_trap(struct iscsiInstSessionFailure_entry *entry)
{
    netsnmp_variable_list  *var_list = NULL;
    oid iscsiInstSessionFailure_oid[] = {OID_LIO_ISCSI_MIB,0,3};
    oid iscsiInstSsnFailures_oid[] = {OID_LIO_ISCSI_MIB,1,1,1,1,10,
                                      entry->iscsiInstIndex};
    oid iscsiInstLastSsnFailureType_oid[] = {OID_LIO_ISCSI_MIB,1,1,1,1,11,
                                             entry->iscsiInstIndex};
    oid iscsiInstLastSsnRmtNodeName_oid[] = {OID_LIO_ISCSI_MIB,1,1,1,1,12,
                                             entry->iscsiInstIndex};

    /*
     * Set the snmpTrapOid.0 value
     */
    snmp_varlist_add_variable(&var_list, snmptrap_oid, OID_LENGTH(snmptrap_oid),
                              ASN_OBJECT_ID,
                              (u_char *)iscsiInstSessionFailure_oid,
                              sizeof(iscsiInstSessionFailure_oid));
    /*
     * Add any objects from the trap definition
     */
    snmp_varlist_add_variable(&var_list, iscsiInstSsnFailures_oid,
                              OID_LENGTH(iscsiInstSsnFailures_oid), ASN_COUNTER,
                              (u_char *)&entry->iscsiInstSsnFailures,
                              sizeof(entry->iscsiInstSsnFailures));
    snmp_varlist_add_variable(&var_list, iscsiInstLastSsnFailureType_oid,
                              OID_LENGTH(iscsiInstLastSsnFailureType_oid),
                              ASN_OBJECT_ID, 
                              (u_char *)&entry->iscsiInstLastSsnFailureType,
                              entry->iscsiInstLastSsnFailureType_len * 
                              sizeof(oid));
    snmp_varlist_add_variable(&var_list, iscsiInstLastSsnRmtNodeName_oid,
                              OID_LENGTH(iscsiInstLastSsnRmtNodeName_oid),
                              ASN_OCTET_STR, 
                              (u_char *)entry->iscsiInstLastSsnRmtNodeName,
                              strlen(entry->iscsiInstLastSsnRmtNodeName));
    /*
     * Send the trap to the list of configured destinations and clean up
     */
    send_v2trap(var_list);
    snmp_free_varbind(var_list);

    return SNMP_ERR_NOERROR;
}

static struct iscsiInstSessionFailure_entry ssnFailureData;

void
iscsiInstSessionFailure_load(unsigned int clientreg, void *clientarg)
{
    FILE *fp;
    char line[512];
    struct iscsiInstSessionFailure_entry tmp;
    u_long iscsiInstVersionMin;
    u_long iscsiInstVersionMax;
    u_long iscsiInstPortalNumber;
    u_long iscsiInstNodeNumber;
    u_long iscsiInstSessionNumber;
    u_long iscsiInstDiscontinuityTime;
    uint32_t failType;

    /* Use iSCSI Instance Attributes file */
    if (!(fp = fopen(PROC_INST_ATTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_INST_ATTR);
        return;
    }

    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, ISCSI_INST_ATTR_LINE, &tmp.iscsiInstIndex,
                   &iscsiInstVersionMin, &iscsiInstVersionMax,
                   &iscsiInstPortalNumber, &iscsiInstNodeNumber,
                   &iscsiInstSessionNumber, &tmp.iscsiInstSsnFailures,
                   &failType, tmp.iscsiInstLastSsnRmtNodeName, 
                   &iscsiInstDiscontinuityTime) != 10)
            continue;

#if 0
        /* Test code: simulates a session failure */
        static int count = 0;
        if (++count == 3) {
            tmp.iscsiInstSsnFailures++;
            failType = 2;
            strcpy(tmp.iscsiInstLastSsnRmtNodeName, "Trap-Test-Initiator-123");
        }
#endif

        if (tmp.iscsiInstSsnFailures != ssnFailureData.iscsiInstSsnFailures) {
            int oidLen = OID_LENGTH(iscsiInstSsnErrStats_oid);
            memcpy(tmp.iscsiInstLastSsnFailureType, iscsiInstSsnErrStats_oid,
                   sizeof(iscsiInstSsnErrStats_oid)); 
            tmp.iscsiInstLastSsnFailureType[oidLen] = failType;
            tmp.iscsiInstLastSsnFailureType_len = oidLen + 1;
            if (clientreg && tmp.iscsiInstSsnFailures)
                send_iscsiInstSessionFailure_trap(&tmp);
            memcpy(&ssnFailureData, &tmp, sizeof(tmp));
        }
        /* Only one instance exists now */
        break;
    }
    fclose(fp);
}
