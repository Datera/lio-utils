/*
 * Copyright (c) 2006 SBE, Inc.
 * Copyright (c) 2009 Linux-iSCSI.org
 */
#include <net-snmp/net-snmp-config.h>
#include <net-snmp/net-snmp-includes.h>
#include <net-snmp/agent/net-snmp-agent-includes.h>
#include "common.h"
#include "scsiMib.h"

/* Initializes the scsiMib module */
void
init_scsiMib(void)
{
    /* Initialize all tables */
    initialize_table_scsiInstanceTable();
    initialize_table_scsiDeviceTable();
    initialize_table_scsiPortTable();
    initialize_table_scsiTransportTable();
    initialize_table_scsiTgtPortTable();
    initialize_table_scsiAuthorizedIntrTable();
    initialize_table_scsiAttIntrPortTable();
    initialize_table_scsiLuTable();
    initialize_scsiTgtDevTable();
}

/*
 * Instance Table
 */

#define SCSI_INST_CACHE_TIMEOUT 10

/*
 * Initialize the scsiInstanceTable table
 */
void
initialize_table_scsiInstanceTable(void)
{
    static oid scsiInstanceTable_oid[] = {OID_LIO_SCSI_MIB,2,1,1};
    size_t scsiInstanceTable_oid_len = OID_LENGTH(scsiInstanceTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiInstanceTable",
                                              scsiInstanceTable_handler,
                                              scsiInstanceTable_oid,
                                              scsiInstanceTable_oid_len,
                                              HANDLER_CAN_RWRITE);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiInstanceTable_get_first_data_point;
    iinfo->get_next_data_point = scsiInstanceTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(SCSI_INST_CACHE_TIMEOUT,
                                             scsiInstanceTable_load, 
                                             scsiInstanceTable_free,
                                             scsiInstanceTable_oid, 
                                             scsiInstanceTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiInstanceTable_cache_update(void)
{
    static marker_t scsiInstanceTable_cache_marker = NULL;

    if (scsiInstanceTable_cache_marker &&
        (!atime_ready(scsiInstanceTable_cache_marker,
                      SCSI_INST_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiInstanceTable_cache_marker)
        atime_setMarker(scsiInstanceTable_cache_marker);
    else
        scsiInstanceTable_cache_marker = atime_newMarker();

    scsiInstanceTable_load(NULL, NULL);
}
#endif

struct scsiInstanceTable_entry *scsiInstanceTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiInstanceTable_get_first_data_point(void **my_loop_context,
                                       void **my_data_context,
                                       netsnmp_variable_list *put_index_data,
                                       netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiInstanceTable_cache_update();
#endif
    *my_loop_context = scsiInstanceTable_head;
    return scsiInstanceTable_get_next_data_point(my_loop_context,
                                                 my_data_context,
                                                 put_index_data, mydata);
}

netsnmp_variable_list *
scsiInstanceTable_get_next_data_point(void **my_loop_context,
                                      void **my_data_context,
                                      netsnmp_variable_list *put_index_data,
                                      netsnmp_iterator_info *mydata)
{
    struct scsiInstanceTable_entry *entry =
                             (struct scsiInstanceTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiInstanceTable table
 */
int
scsiInstanceTable_handler(netsnmp_mib_handler *handler,
                          netsnmp_handler_registration *reginfo,
                          netsnmp_agent_request_info *reqinfo,
                          netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiInstanceTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiInstanceTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSIINSTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiInstIndex,
                          sizeof(table_entry->scsiInstIndex));
                break;
            case COLUMN_SCSIINSTALIAS:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)&table_entry->scsiInstAlias,
                          strlen(table_entry->scsiInstAlias));
                break;
            case COLUMN_SCSIINSTSOFTWAREINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->scsiInstSoftwareIndex,
                          sizeof(table_entry->scsiInstSoftwareIndex));
                break;
            case COLUMN_SCSIINSTVENDORVERSION:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)&table_entry->scsiInstVendorVersion,
                          strlen(table_entry->scsiInstVendorVersion));
                break;
            case COLUMN_SCSIINSTSCSINOTIFICATIONSENABLE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                        (u_char *)&table_entry->scsiInstScsiNotificationsEnable,
                        sizeof(table_entry->scsiInstScsiNotificationsEnable));
                break;
            case COLUMN_SCSIINSTSTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->scsiInstStorageType,
                          sizeof(table_entry->scsiInstStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_INST "/proc/iscsi_target/mib/scsi_inst"
#define SCSI_INST_LINE "%lu %lu"

int 
scsiInstanceTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp, *alias_fp;
    char line[256];
    struct scsiInstanceTable_entry tmp, *entry;

    if (scsiInstanceTable_head)
        scsiInstanceTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_INST, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_INST);
        return -1;
    }

    alias_fp = fopen("/etc/iscsi.alias", "r");
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, SCSI_INST_LINE, &tmp.scsiInstIndex,
                   &tmp.scsiInstSoftwareIndex) != 2)
            continue;

        /* Change this if write is supported */
        tmp.scsiInstScsiNotificationsEnable = TV_TRUE;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "version: %s", tmp.scsiInstVendorVersion) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.scsiInstVendorVersion, line + strlen("version: "));
        }
        else
            break;

        tmp.scsiInstStorageType = ST_READONLY;

        if (alias_fp && (line == fgets(line, sizeof(line), alias_fp)))
            sscanf(line, "%s", tmp.scsiInstAlias);

        entry = SNMP_MALLOC_TYPEDEF(struct scsiInstanceTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiInstanceTable_head;
        scsiInstanceTable_head = entry;
    }
    fclose(fp);
    if (alias_fp)
        fclose(alias_fp);
    return 0;
}

void
scsiInstanceTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiInstanceTable_entry *entry;

    while (scsiInstanceTable_head) {
        entry = scsiInstanceTable_head;
        scsiInstanceTable_head = scsiInstanceTable_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Device Table
 */
#define SCSI_DEV_CACHE_TIMEOUT 10

/*
 * Initialize the scsiDeviceTable table
 */
void
initialize_table_scsiDeviceTable(void)
{
    static oid scsiDeviceTable_oid[] = {OID_LIO_SCSI_MIB,2,1,2};
    size_t scsiDeviceTable_oid_len = OID_LENGTH(scsiDeviceTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiDeviceTable",
                                              scsiDeviceTable_handler,
                                              scsiDeviceTable_oid,
                                              scsiDeviceTable_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     ASN_UNSIGNED,  /* scsiDeviceIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiDeviceTable_get_first_data_point;
    iinfo->get_next_data_point = scsiDeviceTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(SCSI_DEV_CACHE_TIMEOUT,
                                             scsiDeviceTable_load, 
                                             scsiDeviceTable_free,
                                             scsiDeviceTable_oid, 
                                             scsiDeviceTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiDeviceTable_cache_update(void)
{
    static marker_t scsiDeviceTable_cache_marker = NULL;

    if (scsiDeviceTable_cache_marker &&
        (!atime_ready(scsiDeviceTable_cache_marker,
                      SCSI_DEV_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiDeviceTable_cache_marker)
        atime_setMarker(scsiDeviceTable_cache_marker);
    else
        scsiDeviceTable_cache_marker = atime_newMarker();

    scsiDeviceTable_load(NULL, NULL);
}
#endif

struct scsiDeviceTable_entry *scsiDeviceTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiDeviceTable_get_first_data_point(void **my_loop_context,
                                     void **my_data_context,
                                     netsnmp_variable_list *put_index_data,
                                     netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiDeviceTable_cache_update();
#endif
    *my_loop_context = scsiDeviceTable_head;
    return scsiDeviceTable_get_next_data_point(my_loop_context,
                                               my_data_context,
                                               put_index_data, mydata);
}

netsnmp_variable_list *
scsiDeviceTable_get_next_data_point(void **my_loop_context,
                                    void **my_data_context,
                                    netsnmp_variable_list *put_index_data,
                                    netsnmp_iterator_info *mydata)
{
    struct scsiDeviceTable_entry *entry =
                               (struct scsiDeviceTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiDeviceTable table
 */
int
scsiDeviceTable_handler(netsnmp_mib_handler *handler,
                        netsnmp_handler_registration *reginfo,
                        netsnmp_agent_request_info *reqinfo,
                        netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiDeviceTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiDeviceTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSIDEVICEINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiDeviceIndex,
                          sizeof(table_entry->scsiDeviceIndex));
                break;
            case COLUMN_SCSIDEVICEALIAS:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiDeviceAlias,
                          strlen(table_entry->scsiDeviceAlias));
                break;
            case COLUMN_SCSIDEVICEROLE:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)&table_entry->scsiDeviceRole,
                          sizeof(table_entry->scsiDeviceRole));
                break;
            case COLUMN_SCSIDEVICEPORTNUMBER:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiDevicePortNumber,
                          sizeof(table_entry->scsiDevicePortNumber));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_DEV "/proc/iscsi_target/mib/scsi_dev"
#define SCSI_DEV_LINE "%lu %lu %s %lu"

int 
scsiDeviceTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[128];
    struct scsiDeviceTable_entry tmp, *entry;
    char role[12];

    if (scsiDeviceTable_head)
        scsiDeviceTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_DEV, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_DEV);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, SCSI_DEV_LINE, &tmp.scsiInstIndex, 
                   &tmp.scsiDeviceIndex, role, &tmp.scsiDevicePortNumber) != 4)
            continue;

        tmp.scsiDeviceRole = SCSI_ROLE_TARGET;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "dev_alias: %s", tmp.scsiDeviceAlias) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.scsiDeviceAlias, line + strlen("dev_alias: "));
        }
        else
            break;

        entry = SNMP_MALLOC_TYPEDEF(struct scsiDeviceTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiDeviceTable_head;
        scsiDeviceTable_head = entry;
    }
    fclose(fp);
    return 0;
}

void
scsiDeviceTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiDeviceTable_entry *entry;

    while (scsiDeviceTable_head) {
        entry = scsiDeviceTable_head;
        scsiDeviceTable_head = scsiDeviceTable_head->next;
        SNMP_FREE(entry);
    }
}

/* 
 * Port Table
 */
#define SCSI_PORT_CACHE_TIMEOUT 10

/*
 * Initialize the scsiPortTable table
 */
void
initialize_table_scsiPortTable(void)
{
    static oid scsiPortTable_oid[] = {OID_LIO_SCSI_MIB,2,1,3};
    size_t scsiPortTable_oid_len = OID_LENGTH(scsiPortTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiPortTable",
                                              scsiPortTable_handler,
                                              scsiPortTable_oid,
                                              scsiPortTable_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     ASN_UNSIGNED,  /* scsiDeviceIndex */
                                     ASN_UNSIGNED,  /* scsiPortIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiPortTable_get_first_data_point;
    iinfo->get_next_data_point = scsiPortTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(SCSI_PORT_CACHE_TIMEOUT,
                                             scsiPortTable_load, 
                                             scsiPortTable_free,
                                             scsiPortTable_oid, 
                                             scsiPortTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiPortTable_cache_update(void)
{
    static marker_t scsiPortTable_cache_marker = NULL;

    if (scsiPortTable_cache_marker &&
        (!atime_ready(scsiPortTable_cache_marker,
                      SCSI_PORT_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiPortTable_cache_marker)
        atime_setMarker(scsiPortTable_cache_marker);
    else
        scsiPortTable_cache_marker = atime_newMarker();

    scsiPortTable_load(NULL, NULL);
}
#endif

struct scsiPortTable_entry *scsiPortTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiPortTable_get_first_data_point(void **my_loop_context,
                                   void **my_data_context,
                                   netsnmp_variable_list *put_index_data,
                                   netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiPortTable_cache_update();
#endif
    *my_loop_context = scsiPortTable_head;
    return scsiPortTable_get_next_data_point(my_loop_context,
                                             my_data_context,
                                             put_index_data, mydata);
}

netsnmp_variable_list *
scsiPortTable_get_next_data_point(void **my_loop_context,
                                  void **my_data_context,
                                  netsnmp_variable_list *put_index_data,
                                  netsnmp_iterator_info *mydata)
{
    struct scsiPortTable_entry *entry =
                                (struct scsiPortTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiPortIndex,
                           sizeof(entry->scsiPortIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiPortTable table
 */
int
scsiPortTable_handler(netsnmp_mib_handler *handler,
                      netsnmp_handler_registration *reginfo,
                      netsnmp_agent_request_info *reqinfo,
                      netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiPortTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiPortTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSIPORTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiPortIndex,
                          sizeof(table_entry->scsiPortIndex));
                break;
            case COLUMN_SCSIPORTROLE:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          &table_entry->scsiPortRole,
                          sizeof(table_entry->scsiPortRole));
                break;
            case COLUMN_SCSIPORTTRANSPORTPTR:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                          (u_char *)&table_entry->scsiPortTransportPtr,
                          table_entry->scsiPortTransportPtr_len * sizeof(oid));
                break;
            case COLUMN_SCSIPORTBUSYSTATUSES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiPortBusyStatuses,
                          sizeof(table_entry->scsiPortBusyStatuses));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_PORT "/proc/iscsi_target/mib/scsi_port"
#define SCSI_PORT_LINE "%lu %lu %lu %s %lu"
/*
 * scsiTransportTable.scsiTransportEntry.scsiTransportType
 */
static oid scsiTransportEntry_oid[] = {OID_LIO_SCSI_MIB,2,1,5,1,2};

int 
scsiPortTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[128];
    struct scsiPortTable_entry tmp, *entry;
    char role[12];

    if (scsiPortTable_head)
        scsiPortTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_PORT, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_PORT);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
         if (sscanf(line, SCSI_PORT_LINE, &tmp.scsiInstIndex,
                    &tmp.scsiDeviceIndex, &tmp.scsiPortIndex, role,
                    &tmp.scsiPortBusyStatuses) != 5)
             continue;

        tmp.scsiPortRole = SCSI_ROLE_TARGET;

        memcpy(tmp.scsiPortTransportPtr, scsiTransportEntry_oid,
               sizeof(scsiTransportEntry_oid)); 
        tmp.scsiPortTransportPtr_len = OID_LENGTH(scsiTransportEntry_oid) + 3; 
        tmp.scsiPortTransportPtr[tmp.scsiPortTransportPtr_len - 3] = 
                                                          tmp.scsiInstIndex;
        tmp.scsiPortTransportPtr[tmp.scsiPortTransportPtr_len - 2] = 
                                                          tmp.scsiDeviceIndex;
        tmp.scsiPortTransportPtr[tmp.scsiPortTransportPtr_len - 1] = 
                                                          SCSI_TRANSPORT_INDEX;

        entry = SNMP_MALLOC_TYPEDEF(struct scsiPortTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiPortTable_head;
        scsiPortTable_head = entry;
    }
    fclose(fp);
    return 0;
}

void
scsiPortTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiPortTable_entry *entry;

    while (scsiPortTable_head) {
        entry = scsiPortTable_head;
        scsiPortTable_head = scsiPortTable_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Transport Table
 */
#define SCSI_TRANSPORT_CACHE_TIMEOUT 10

/*
 * Initialize the scsiTransportTable table
 */
void
initialize_table_scsiTransportTable(void)
{
    static oid scsiTransportTable_oid[] = {OID_LIO_SCSI_MIB,2,1,5};
    size_t scsiTransportTable_oid_len = OID_LENGTH(scsiTransportTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiTransportTable",
                                              scsiTransportTable_handler,
                                              scsiTransportTable_oid,
                                              scsiTransportTable_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     ASN_UNSIGNED,  /* scsiDeviceIndex */
                                     ASN_UNSIGNED,  /* scsiTransportIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiTransportTable_get_first_data_point;
    iinfo->get_next_data_point = scsiTransportTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(SCSI_TRANSPORT_CACHE_TIMEOUT,
                                             scsiTransportTable_load, 
                                             scsiTransportTable_free,
                                             scsiTransportTable_oid, 
                                             scsiTransportTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiTransportTable_cache_update(void)
{
    static marker_t scsiTransportTable_cache_marker = NULL;

    if (scsiTransportTable_cache_marker &&
        (!atime_ready(scsiTransportTable_cache_marker,
                      SCSI_TRANSPORT_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiTransportTable_cache_marker)
        atime_setMarker(scsiTransportTable_cache_marker);
    else
        scsiTransportTable_cache_marker = atime_newMarker();

    scsiTransportTable_load(NULL, NULL);
}
#endif

struct scsiTransportTable_entry *scsiTransportTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiTransportTable_get_first_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiTransportTable_cache_update();
#endif
    *my_loop_context = scsiTransportTable_head;
    return scsiTransportTable_get_next_data_point(my_loop_context,
                                                  my_data_context,
                                                  put_index_data, mydata);
}

netsnmp_variable_list *
scsiTransportTable_get_next_data_point(void **my_loop_context,
                                       void **my_data_context,
                                       netsnmp_variable_list *put_index_data,
                                       netsnmp_iterator_info *mydata)
{
    struct scsiTransportTable_entry *entry =
                            (struct scsiTransportTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiTransportIndex,
                           sizeof(entry->scsiTransportIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiTransportTable table
 */
int
scsiTransportTable_handler(netsnmp_mib_handler *handler,
                           netsnmp_handler_registration *reginfo,
                           netsnmp_agent_request_info *reqinfo,
                           netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiTransportTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiTransportTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSITRANSPORTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiTransportIndex,
                          sizeof(table_entry->scsiTransportIndex));
            case COLUMN_SCSITRANSPORTTYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                          (u_char *)&table_entry->scsiTransportType,
                          table_entry->scsiTransportType_len * sizeof(oid));
                break;
            case COLUMN_SCSITRANSPORTPOINTER:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                          (u_char *)&table_entry->scsiTransportPointer,
                          table_entry->scsiTransportPointer_len * sizeof(oid));
                break;
            case COLUMN_SCSITRANSPORTDEVNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiTransportDevName,
                          strlen(table_entry->scsiTransportDevName));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_TRANSPORT "/proc/iscsi_target/mib/scsi_transport"
#define SCSI_TRANSPORT_LINE "%lu %lu %lu %s"
static oid scsiTransportISCSI_oid[] = {OID_LIO_SCSI_MIB,1,1,5};
static oid iscsiInstAttributes_oid[] = {OID_LIO_ISCSI_MIB,1,1,1,1,2};

int 
scsiTransportTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    struct scsiTransportTable_entry tmp, *entry;

    if (scsiTransportTable_head)
        scsiTransportTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_TRANSPORT, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_TRANSPORT);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
         if (sscanf(line, SCSI_TRANSPORT_LINE, &tmp.scsiInstIndex,
                    &tmp.scsiDeviceIndex, &tmp.scsiTransportIndex,
                    tmp.scsiTransportDevName) != 4)
             continue;

        /* Transport type is always iSCSI */
        memcpy(tmp.scsiTransportType, scsiTransportISCSI_oid,
               sizeof(scsiTransportISCSI_oid)); 
        tmp.scsiTransportType_len = OID_LENGTH(scsiTransportISCSI_oid);

        /* Point to the iSCSI Instance (index 1) */
        memcpy(tmp.scsiTransportPointer, iscsiInstAttributes_oid,
               sizeof(iscsiInstAttributes_oid)); 
        tmp.scsiTransportPointer_len = OID_LENGTH(iscsiInstAttributes_oid) + 1; 
        tmp.scsiTransportPointer[tmp.scsiTransportPointer_len - 1] = 1;

        entry = SNMP_MALLOC_TYPEDEF(struct scsiTransportTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiTransportTable_head;
        scsiTransportTable_head = entry;
    }
    fclose(fp);
    return 0;
}

void
scsiTransportTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiTransportTable_entry *entry;

    while (scsiTransportTable_head) {
        entry = scsiTransportTable_head;
        scsiTransportTable_head = scsiTransportTable_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Target Device Table support and Device status change Trap generator
 */
/* Use 3 sec poll recommended by the draft */
#define SCSI_TGT_DEV_STATUS_POLL_INTERVAL 3

/*
 * Initializes the iscsiTargetAttributes
 */
void
initialize_scsiTgtDevTable(void)
{
    /* Initialize the table */
    initialize_table_scsiTgtDevTable();

    /* Setup callback for polling */
    snmp_alarm_register(SCSI_TGT_DEV_STATUS_POLL_INTERVAL, SA_REPEAT,
                        scsiTgtDevTable_load, NULL);

    /* Initial load */
    scsiTgtDevTable_load(0, NULL);
}

/*
 * Initialize the scsiTgtDevTable table
 */
void
initialize_table_scsiTgtDevTable(void)
{
    static oid scsiTgtDevTable_oid[] = {OID_LIO_SCSI_MIB,2,3,1};
    size_t scsiTgtDevTable_oid_len = OID_LENGTH(scsiTgtDevTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiTgtDevTable",
                                              scsiTgtDevTable_handler,
                                              scsiTgtDevTable_oid,
                                              scsiTgtDevTable_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     ASN_UNSIGNED,  /* scsiDeviceIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiTgtDevTable_get_first_data_point;
    iinfo->get_next_data_point = scsiTgtDevTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);
}

struct scsiTgtDevTable_entry *scsiTgtDevTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiTgtDevTable_get_first_data_point(void **my_loop_context,
                                     void **my_data_context,
                                     netsnmp_variable_list *put_index_data,
                                     netsnmp_iterator_info *mydata)
{
    *my_loop_context = scsiTgtDevTable_head;
    return scsiTgtDevTable_get_next_data_point(my_loop_context, my_data_context,
                                               put_index_data, mydata);
}

netsnmp_variable_list *
scsiTgtDevTable_get_next_data_point(void **my_loop_context,
                                    void **my_data_context,
                                    netsnmp_variable_list *put_index_data,
                                    netsnmp_iterator_info *mydata)
{
    struct scsiTgtDevTable_entry *entry =
                               (struct scsiTgtDevTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiTgtDevTable table
 */
int
scsiTgtDevTable_handler(netsnmp_mib_handler *handler,
                        netsnmp_handler_registration *reginfo,
                        netsnmp_agent_request_info *reqinfo,
                        netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiTgtDevTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiTgtDevTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSITGTDEVNUMBEROFLUS:
                snmp_set_var_typed_value(request->requestvb, ASN_GAUGE,
                          (u_char *)&table_entry->scsiTgtDevNumberOfLUs,
                          sizeof(table_entry->scsiTgtDevNumberOfLUs));
                break;
            case COLUMN_SCSITGTDEVICESTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->scsiTgtDeviceStatus,
                          sizeof(table_entry->scsiTgtDeviceStatus));
                break;
            case COLUMN_SCSITGTDEVNONACCESSIBLELUS:
                snmp_set_var_typed_value(request->requestvb, ASN_GAUGE,
                          (u_char *)&table_entry->scsiTgtDevNonAccessibleLUs,
                          sizeof(table_entry->scsiTgtDevNonAccessibleLUs));
                break;
            case COLUMN_SCSITGTDEVRESETS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiTgtDevResets,
                          sizeof(table_entry->scsiTgtDevResets));
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
static oid snmptrap_oid[] = {1, 3, 6, 1, 6, 3, 1, 1, 4, 1, 0};

int
send_scsiTgtDeviceStatusChanged_trap(struct scsiTgtDevTable_entry *entry)
{
    netsnmp_variable_list  *var_list = NULL;
    oid scsiTgtDeviceStatusChanged_oid[] = {OID_LIO_SCSI_MIB,0,0,1};
    oid scsiTgtDeviceStatus_oid[] = {OID_LIO_SCSI_MIB,2,3,1,1,2,
                                     entry->scsiInstIndex,
                                     entry->scsiDeviceIndex};

    /*
     * Set the snmpTrapOid.0 value
     */
    snmp_varlist_add_variable(&var_list, snmptrap_oid, OID_LENGTH(snmptrap_oid),
                              ASN_OBJECT_ID, 
                              (u_char *)scsiTgtDeviceStatusChanged_oid,
                              sizeof(scsiTgtDeviceStatusChanged_oid));
    /*
     * Add objects from the trap definition
     */
    snmp_varlist_add_variable(&var_list, scsiTgtDeviceStatus_oid,
                              OID_LENGTH(scsiTgtDeviceStatus_oid), ASN_INTEGER,
                              (u_char *)&entry->scsiTgtDeviceStatus,
                              sizeof(entry->scsiTgtDeviceStatus));
    /*
     * Send the trap to the list of configured destinations and clean up
     */
    send_v2trap(var_list);
    snmp_free_varbind(var_list);

    return SNMP_ERR_NOERROR;
}

void
scsiTgtDevTable_free(struct scsiTgtDevTable_entry **table_head_ptr)
{
    struct scsiTgtDevTable_entry *entry;

    while (*table_head_ptr) {
        entry = *table_head_ptr;
        *table_head_ptr = (*table_head_ptr)->next;
        SNMP_FREE(entry);
    }
}

#define PROC_SCSI_TGT_DEV "/proc/iscsi_target/mib/scsi_tgt_dev"
#define SCSI_TGT_DEV_LINE "%lu %lu %lu %s %lu %lu"

void 
scsiTgtDevTable_load(unsigned int clientreg, void *clientarg)
{
    FILE *fp;
    char line[128];
    struct scsiTgtDevTable_entry tmp, *entry;
    struct scsiTgtDevTable_entry *old_table, *old_entry;
    char status[16];


    if (!(fp = fopen(PROC_SCSI_TGT_DEV, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_TGT_DEV);
        if (scsiTgtDevTable_head)
            scsiTgtDevTable_free(&scsiTgtDevTable_head);
        return;
    }
 
    old_table = scsiTgtDevTable_head;
    scsiTgtDevTable_head = NULL; 

    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, SCSI_TGT_DEV_LINE, &tmp.scsiInstIndex, 
                   &tmp.scsiDeviceIndex, &tmp.scsiTgtDevNumberOfLUs,
                   status, &tmp.scsiTgtDevNonAccessibleLUs,
                   &tmp.scsiTgtDevResets) != 6)
            continue;

        if (!strcmp(status, "activated"))
            tmp.scsiTgtDeviceStatus = SCSI_DEV_STATUS_AVAILABLE;
        else if (!strncmp(status, "unknown", 7))
            tmp.scsiTgtDeviceStatus = SCSI_DEV_STATUS_UNKNOWN;
        else
            tmp.scsiTgtDeviceStatus = SCSI_DEV_STATUS_ABNORMAL;

#if 0
        /* Test code. Simulate status changes */
        static int count = 0;
        if (!(++count % 20))
            tmp.scsiTgtDeviceStatus = SCSI_DEV_STATUS_ABNORMAL;
#endif

        /* Get the previous status */  
        for (old_entry = old_table; old_entry; old_entry = old_entry->next) {
            if ((old_entry->scsiInstIndex == tmp.scsiInstIndex) &&
                (old_entry->scsiDeviceIndex == tmp.scsiDeviceIndex)) {
                if (old_entry->scsiTgtDeviceStatus != tmp.scsiTgtDeviceStatus) {
                    /* Status changed. Send a trap */
                    send_scsiTgtDeviceStatusChanged_trap(&tmp);
                }
                break;
            }
        }

        entry = SNMP_MALLOC_TYPEDEF(struct scsiTgtDevTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiTgtDevTable_head;
        scsiTgtDevTable_head = entry;
    }
    fclose(fp);

    if (old_table)
        scsiTgtDevTable_free(&old_table);

    return;
}

/*
 * Target Port Table
 */
#define SCSI_TGT_PORT_CACHE_TIMEOUT 5

/*
 * Initialize the scsiTgtPortTable table
 */
void
initialize_table_scsiTgtPortTable(void)
{
    static oid scsiTgtPortTable_oid[] = {OID_LIO_SCSI_MIB,2,3,2};
    size_t scsiTgtPortTable_oid_len = OID_LENGTH(scsiTgtPortTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiTgtPortTable",
                                              scsiTgtPortTable_handler,
                                              scsiTgtPortTable_oid,
                                              scsiTgtPortTable_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     ASN_UNSIGNED,  /* scsiDeviceIndex */
                                     ASN_UNSIGNED,  /* scsiPortIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 9;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiTgtPortTable_get_first_data_point;
    iinfo->get_next_data_point = scsiTgtPortTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(SCSI_TGT_PORT_CACHE_TIMEOUT,
                                             scsiTgtPortTable_load, 
                                             scsiTgtPortTable_free,
                                             scsiTgtPortTable_oid, 
                                             scsiTgtPortTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiTgtPortTable_cache_update(void)
{
    static marker_t scsiTgtPortTable_cache_marker = NULL;

    if (scsiTgtPortTable_cache_marker &&
        (!atime_ready(scsiTgtPortTable_cache_marker,
                      SCSI_TGT_PORT_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiTgtPortTable_cache_marker)
        atime_setMarker(scsiTgtPortTable_cache_marker);
    else
        scsiTgtPortTable_cache_marker = atime_newMarker();

    scsiTgtPortTable_load(NULL, NULL);
}
#endif

struct scsiTgtPortTable_entry *scsiTgtPortTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiTgtPortTable_get_first_data_point(void **my_loop_context,
                                      void **my_data_context,
                                      netsnmp_variable_list *put_index_data,
                                      netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiTgtPortTable_cache_update();
#endif
    *my_loop_context = scsiTgtPortTable_head;
    return scsiTgtPortTable_get_next_data_point(my_loop_context,
                                                my_data_context,
                                                put_index_data, mydata);
}

netsnmp_variable_list *
scsiTgtPortTable_get_next_data_point(void **my_loop_context,
                                     void **my_data_context,
                                     netsnmp_variable_list *put_index_data,
                                     netsnmp_iterator_info *mydata)
{
    struct scsiTgtPortTable_entry *entry =
                              (struct scsiTgtPortTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiPortIndex,
                           sizeof(entry->scsiPortIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiTgtPortTable table
 */
int
scsiTgtPortTable_handler(netsnmp_mib_handler *handler,
                         netsnmp_handler_registration *reginfo,
                         netsnmp_agent_request_info *reqinfo,
                         netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiTgtPortTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiTgtPortTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSITGTPORTNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiTgtPortName,
                          strlen(table_entry->scsiTgtPortName));
                break;
            case COLUMN_SCSITGTPORTIDENTIFIER:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiTgtPortIdentifier,
                          strlen(table_entry->scsiTgtPortIdentifier));
                break;
            case COLUMN_SCSITGTPORTINCOMMANDS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiTgtPortInCommands,
                          sizeof(table_entry->scsiTgtPortInCommands));
                break;
            case COLUMN_SCSITGTPORTWRITTENMEGABYTES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiTgtPortWrittenMegaBytes,
                          sizeof(table_entry->scsiTgtPortWrittenMegaBytes));
                break;
            case COLUMN_SCSITGTPORTREADMEGABYTES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiTgtPortReadMegaBytes,
                          sizeof(table_entry->scsiTgtPortReadMegaBytes));
                break;
            case COLUMN_SCSITGTPORTHSINCOMMANDS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER64,
                          (u_char *)&table_entry->scsiTgtPortHSInCommands,
                          sizeof(table_entry->scsiTgtPortHSInCommands));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_TGT_PORT "/proc/iscsi_target/mib/scsi_tgt_port"
#define SCSI_TGT_PORT_LINE_32 "%lu %lu %lu %s %s %llu %lu %lu"
#define SCSI_TGT_PORT_LINE_64 "%lu %lu %lu %s %s %lu %lu %lu"

int 
scsiTgtPortTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    struct scsiTgtPortTable_entry tmp, *entry;
    u_int64_t inCommands;

    if (scsiTgtPortTable_head)
        scsiTgtPortTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_TGT_PORT, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_TGT_PORT);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, (sizeof(long) == 8)? SCSI_TGT_PORT_LINE_64 :
                   SCSI_TGT_PORT_LINE_32, &tmp.scsiInstIndex, 
                   &tmp.scsiDeviceIndex, &tmp.scsiPortIndex,
                   tmp.scsiTgtPortName, tmp.scsiTgtPortIdentifier,
		   &inCommands,
                   &tmp.scsiTgtPortWrittenMegaBytes,
                   &tmp.scsiTgtPortReadMegaBytes) != 8)
            continue;

        tmp.scsiTgtPortHSInCommands.high = (inCommands >> 32) & 0xffffffff;
        tmp.scsiTgtPortHSInCommands.low = inCommands & 0xffffffff;

	tmp.scsiTgtPortInCommands = tmp.scsiTgtPortHSInCommands.low;

        entry = SNMP_MALLOC_TYPEDEF(struct scsiTgtPortTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiTgtPortTable_head;
        scsiTgtPortTable_head = entry;
    }
    fclose(fp);
    return 0;
}

void
scsiTgtPortTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiTgtPortTable_entry *entry;

    while (scsiTgtPortTable_head) {
        entry = scsiTgtPortTable_head;
        scsiTgtPortTable_head = scsiTgtPortTable_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Authorized Initiator Table
 */
#define SCSI_AUTH_INTR_CACHE_TIMEOUT 5

/*
 * Initialize the scsiAuthorizedIntrTable table
 */
void
initialize_table_scsiAuthorizedIntrTable(void)
{
    static oid scsiAuthorizedIntrTable_oid[] = {OID_LIO_SCSI_MIB,2,3,3,1};
    size_t scsiAuthorizedIntrTable_oid_len = 
                                       OID_LENGTH(scsiAuthorizedIntrTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiAuthorizedIntrTable",
                                              scsiAuthorizedIntrTable_handler,
                                              scsiAuthorizedIntrTable_oid,
                                              scsiAuthorizedIntrTable_oid_len,
                                              HANDLER_CAN_RWRITE);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED, /* scsiInstIndex */
                                     ASN_UNSIGNED, /* scsiDeviceIndex */
                                     ASN_UNSIGNED, /* scsiAuthIntrTgtPortIndex*/
                                     ASN_UNSIGNED, /* scsiAuthIntrIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 14;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiAuthorizedIntrTable_get_first_data_point;
    iinfo->get_next_data_point = scsiAuthorizedIntrTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(SCSI_AUTH_INTR_CACHE_TIMEOUT,
                                             scsiAuthorizedIntrTable_load, 
                                             scsiAuthorizedIntrTable_free,
                                             scsiAuthorizedIntrTable_oid, 
                                             scsiAuthorizedIntrTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiAuthorizedIntrTable_cache_update(void)
{
    static marker_t scsiAuthorizedIntrTable_cache_marker = NULL;

    if (scsiAuthorizedIntrTable_cache_marker &&
        (!atime_ready(scsiAuthorizedIntrTable_cache_marker,
                      SCSI_AUTH_INTR_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiAuthorizedIntrTable_cache_marker)
        atime_setMarker(scsiAuthorizedIntrTable_cache_marker);
    else
        scsiAuthorizedIntrTable_cache_marker = atime_newMarker();

    scsiAuthorizedIntrTable_load(NULL, NULL);
}
#endif

struct scsiAuthorizedIntrTable_entry *scsiAuthorizedIntrTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiAuthorizedIntrTable_get_first_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiAuthorizedIntrTable_cache_update();
#endif
    *my_loop_context = scsiAuthorizedIntrTable_head;
    return scsiAuthorizedIntrTable_get_next_data_point(my_loop_context,
                                                       my_data_context,
                                                       put_index_data, mydata);
}

netsnmp_variable_list *
scsiAuthorizedIntrTable_get_next_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
    struct scsiAuthorizedIntrTable_entry *entry =
                       (struct scsiAuthorizedIntrTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiAuthIntrTgtPortIndex,
                           sizeof(entry->scsiAuthIntrTgtPortIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiAuthIntrIndex,
                           sizeof(entry->scsiAuthIntrIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiAuthorizedIntrTable table
 */
int
scsiAuthorizedIntrTable_handler(netsnmp_mib_handler *handler,
                                netsnmp_handler_registration *reginfo,
                                netsnmp_agent_request_info *reqinfo,
                                netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiAuthorizedIntrTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiAuthorizedIntrTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSIAUTHINTRTGTPORTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiAuthIntrTgtPortIndex,
                          sizeof(table_entry->scsiAuthIntrTgtPortIndex));
                break;
            case COLUMN_SCSIAUTHINTRINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiAuthIntrIndex,
                          sizeof(table_entry->scsiAuthIntrIndex));
                break;
            case COLUMN_SCSIAUTHINTRDEVORPORT:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->scsiAuthIntrDevOrPort,
                          sizeof(table_entry->scsiAuthIntrDevOrPort));
                break;
            case COLUMN_SCSIAUTHINTRNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiAuthIntrName,
                          strlen(table_entry->scsiAuthIntrName));
                break;
            case COLUMN_SCSIAUTHINTRLUNMAPINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiAuthIntrLunMapIndex,
                          sizeof(table_entry->scsiAuthIntrLunMapIndex));
                break;
            case COLUMN_SCSIAUTHINTRATTACHEDTIMES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiAuthIntrAttachedTimes,
                          sizeof(table_entry->scsiAuthIntrAttachedTimes));
                break;
            case COLUMN_SCSIAUTHINTROUTCOMMANDS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiAuthIntrOutCommands,
                          sizeof(table_entry->scsiAuthIntrOutCommands));
                break;
            case COLUMN_SCSIAUTHINTRREADMEGABYTES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiAuthIntrReadMegaBytes,
                          sizeof(table_entry->scsiAuthIntrReadMegaBytes));
                break;
            case COLUMN_SCSIAUTHINTRWRITTENMEGABYTES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiAuthIntrWrittenMegaBytes,
                          sizeof(table_entry->scsiAuthIntrWrittenMegaBytes));
                break;
            case COLUMN_SCSIAUTHINTRHSOUTCOMMANDS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER64,
                          (u_char *)&table_entry->scsiAuthIntrHSOutCommands,
                          sizeof(table_entry->scsiAuthIntrHSOutCommands));
                break;
            case COLUMN_SCSIAUTHINTRLASTCREATION:
                snmp_set_var_typed_value(request->requestvb, ASN_TIMETICKS,
                          (u_char *)&table_entry->scsiAuthIntrLastCreation,
                          sizeof(table_entry->scsiAuthIntrLastCreation));
                break;
            case COLUMN_SCSIAUTHINTRROWSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->scsiAuthIntrRowStatus,
                          sizeof(table_entry->scsiAuthIntrRowStatus));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_AUTH_INTR "/proc/iscsi_target/mib/scsi_auth_intr"
#define SCSI_AUTH_INTR_LINE "%lu %lu %lu %lu %lu %s %lu %lu %lu %lu %lu %lu"

int 
scsiAuthorizedIntrTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    struct scsiAuthorizedIntrTable_entry tmp, *entry;

    if (scsiAuthorizedIntrTable_head)
        scsiAuthorizedIntrTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_AUTH_INTR, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_AUTH_INTR);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, SCSI_AUTH_INTR_LINE, &tmp.scsiInstIndex, 
                   &tmp.scsiDeviceIndex, &tmp.scsiAuthIntrTgtPortIndex,
                   &tmp.scsiAuthIntrIndex, &tmp.scsiAuthIntrDevOrPort,
                   tmp.scsiAuthIntrName, &tmp.scsiAuthIntrLunMapIndex,
                   &tmp.scsiAuthIntrAttachedTimes, &tmp.scsiAuthIntrOutCommands,
                   &tmp.scsiAuthIntrReadMegaBytes,
                   &tmp.scsiAuthIntrWrittenMegaBytes,
                   &tmp.scsiAuthIntrLastCreation) != 12)
            continue;

        tmp.scsiAuthIntrHSOutCommands.low = tmp.scsiAuthIntrOutCommands;

        tmp.scsiAuthIntrRowStatus = RS_ACTIVE;

        entry = SNMP_MALLOC_TYPEDEF(struct scsiAuthorizedIntrTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiAuthorizedIntrTable_head;
        scsiAuthorizedIntrTable_head = entry;
    }
    fclose(fp);
    return 0;
}

void
scsiAuthorizedIntrTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiAuthorizedIntrTable_entry *entry;

    while (scsiAuthorizedIntrTable_head) {
        entry = scsiAuthorizedIntrTable_head;
        scsiAuthorizedIntrTable_head = scsiAuthorizedIntrTable_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Attached Initiator Port Table
 */
#define SCSI_ATT_INTR_PORT_CACHE_TIMEOUT 10

/*
 * Initialize the scsiAttIntrPortTable table
 */
void
initialize_table_scsiAttIntrPortTable(void)
{
    static oid scsiAttIntrPortTable_oid[] = {OID_LIO_SCSI_MIB,2,3,3,2};
    size_t scsiAttIntrPortTable_oid_len = OID_LENGTH(scsiAttIntrPortTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiAttIntrPortTable",
                                              scsiAttIntrPortTable_handler,
                                              scsiAttIntrPortTable_oid,
                                              scsiAttIntrPortTable_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     ASN_UNSIGNED,  /* scsiDeviceIndex */
                                     ASN_UNSIGNED,  /* scsiPortIndex */
                                     ASN_UNSIGNED,  /* scsiAttIntrPortIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 7;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiAttIntrPortTable_get_first_data_point;
    iinfo->get_next_data_point = scsiAttIntrPortTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(SCSI_ATT_INTR_PORT_CACHE_TIMEOUT,
                                             scsiAttIntrPortTable_load, 
                                             scsiAttIntrPortTable_free,
                                             scsiAttIntrPortTable_oid, 
                                             scsiAttIntrPortTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiAttIntrPortTable_cache_update(void)
{
    static marker_t scsiAttIntrPortTable_cache_marker = NULL;

    if (scsiAttIntrPortTable_cache_marker &&
        (!atime_ready(scsiAttIntrPortTable_cache_marker,
                      SCSI_ATT_INTR_PORT_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiAttIntrPortTable_cache_marker)
        atime_setMarker(scsiAttIntrPortTable_cache_marker);
    else
        scsiAttIntrPortTable_cache_marker = atime_newMarker();

    scsiAttIntrPortTable_load(NULL, NULL);
}
#endif

struct scsiAttIntrPortTable_entry *scsiAttIntrPortTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiAttIntrPortTable_get_first_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiAttIntrPortTable_cache_update();
#endif
    *my_loop_context = scsiAttIntrPortTable_head;
    return scsiAttIntrPortTable_get_next_data_point(my_loop_context,
                                                    my_data_context,
                                                    put_index_data, mydata);
}

netsnmp_variable_list *
scsiAttIntrPortTable_get_next_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
    struct scsiAttIntrPortTable_entry *entry =
                          (struct scsiAttIntrPortTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiPortIndex,
                           sizeof(entry->scsiPortIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiAttIntrPortIndex,
                           sizeof(entry->scsiAttIntrPortIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiAttIntrPortTable table
 */
int
scsiAttIntrPortTable_handler(netsnmp_mib_handler *handler,
                             netsnmp_handler_registration *reginfo,
                             netsnmp_agent_request_info *reqinfo,
                             netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiAttIntrPortTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiAttIntrPortTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSIATTINTRPORTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiAttIntrPortIndex,
                          sizeof(table_entry->scsiAttIntrPortIndex));
                break;
            case COLUMN_SCSIATTINTRPORTAUTHINTRIDX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiAttIntrPortAuthIntrIdx,
                          sizeof(table_entry->scsiAttIntrPortAuthIntrIdx));
                break;
            case COLUMN_SCSIATTINTRPORTNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiAttIntrPortName,
                          strlen(table_entry->scsiAttIntrPortName));
                break;
            case COLUMN_SCSIATTINTRPORTIDENTIFIER:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiAttIntrPortIdentifier,
                          strlen(table_entry->scsiAttIntrPortIdentifier));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_ATT_INTR_PORT "/proc/iscsi_target/mib/scsi_att_intr_port"
#define SCSI_ATT_INTR_PORT_LINE "%lu %lu %lu %lu %lu %s"

int 
scsiAttIntrPortTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    struct scsiAttIntrPortTable_entry tmp, *entry;

    if (scsiAttIntrPortTable_head)
        scsiAttIntrPortTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_ATT_INTR_PORT, "r"))) {
        //snmp_log(LOG_DEBUG,"snmpd: cannot open %s\n",PROC_SCSI_ATT_INTR_PORT);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, SCSI_ATT_INTR_PORT_LINE, &tmp.scsiInstIndex, 
                   &tmp.scsiDeviceIndex, &tmp.scsiPortIndex,
                   &tmp.scsiAttIntrPortIndex, &tmp.scsiAttIntrPortAuthIntrIdx,
                   tmp.scsiAttIntrPortName) != 6)
            continue;

        strcpy(tmp.scsiAttIntrPortIdentifier, tmp.scsiAttIntrPortName);

        entry = SNMP_MALLOC_TYPEDEF(struct scsiAttIntrPortTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiAttIntrPortTable_head;
        scsiAttIntrPortTable_head = entry;
    }
    fclose(fp);
    return 0;
}

void
scsiAttIntrPortTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiAttIntrPortTable_entry *entry;

    while (scsiAttIntrPortTable_head) {
        entry = scsiAttIntrPortTable_head;
        scsiAttIntrPortTable_head = scsiAttIntrPortTable_head->next;
        SNMP_FREE(entry);
    }
}

/*
 * Logical Unit Table
 */
#define SCSI_LU_CACHE_TIMEOUT 5

/*
 * Initialize the scsiLuTable table
 */
void
initialize_table_scsiLuTable(void)
{
    static oid scsiLuTable_oid[] = {OID_LIO_SCSI_MIB,2,4,1};
    size_t scsiLuTable_oid_len = OID_LENGTH(scsiLuTable_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("scsiLuTable",
                                              scsiLuTable_handler,
                                              scsiLuTable_oid,
                                              scsiLuTable_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* scsiInstIndex */
                                     ASN_UNSIGNED,  /* scsiDeviceIndex */
                                     ASN_UNSIGNED,  /* scsiLuIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 18;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = scsiLuTable_get_first_data_point;
    iinfo->get_next_data_point = scsiLuTable_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                           netsnmp_get_cache_handler(SCSI_LU_CACHE_TIMEOUT,
                                                     scsiLuTable_load, 
                                                     scsiLuTable_free,
                                                     scsiLuTable_oid, 
                                                     scsiLuTable_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
scsiLuTable_cache_update(void)
{
    static marker_t scsiLuTable_cache_marker = NULL;

    if (scsiLuTable_cache_marker &&
        (!atime_ready(scsiLuTable_cache_marker, SCSI_LU_CACHE_TIMEOUT * 1000)))
        return;

    if (scsiLuTable_cache_marker)
        atime_setMarker(scsiLuTable_cache_marker);
    else
        scsiLuTable_cache_marker = atime_newMarker();

    scsiLuTable_load(NULL, NULL);
}
#endif

struct scsiLuTable_entry *scsiLuTable_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
scsiLuTable_get_first_data_point(void **my_loop_context, void **my_data_context,
                                 netsnmp_variable_list *put_index_data,
                                 netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    scsiLuTable_cache_update();
#endif
    *my_loop_context = scsiLuTable_head;
    return scsiLuTable_get_next_data_point(my_loop_context, my_data_context,
                                           put_index_data, mydata);
}

netsnmp_variable_list *
scsiLuTable_get_next_data_point(void **my_loop_context, void **my_data_context,
                                netsnmp_variable_list *put_index_data,
                                netsnmp_iterator_info *mydata)
{
    struct scsiLuTable_entry *entry =
                                  (struct scsiLuTable_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->scsiInstIndex,
                           sizeof(entry->scsiInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiDeviceIndex,
                           sizeof(entry->scsiDeviceIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->scsiLuIndex,
                           sizeof(entry->scsiLuIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the scsiLuTable table
 */
int
scsiLuTable_handler(netsnmp_mib_handler *handler,
                    netsnmp_handler_registration *reginfo,
                    netsnmp_agent_request_info *reqinfo,
                    netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct scsiLuTable_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct scsiLuTable_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_SCSILUINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiLuIndex,
                          sizeof(table_entry->scsiLuIndex));
                break;
            case COLUMN_SCSILUDEFAULTLUN:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          table_entry->scsiLuDefaultLun,
                          sizeof(table_entry->scsiLuDefaultLun));
                break;
            case COLUMN_SCSILUWWNNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiLuWwnName,
                          strlen(table_entry->scsiLuWwnName));
                break;
            case COLUMN_SCSILUVENDORID:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiLuVendorId,
                          strlen(table_entry->scsiLuVendorId));
                break;
            case COLUMN_SCSILUPRODUCTID:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiLuProductId,
                          strlen(table_entry->scsiLuProductId));
                break;
            case COLUMN_SCSILUREVISIONID:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiLuRevisionId,
                          strlen(table_entry->scsiLuRevisionId));
                break;
            case COLUMN_SCSILUPERIPHERALTYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->scsiLuPeripheralType,
                          sizeof(table_entry->scsiLuPeripheralType));
                break;
            case COLUMN_SCSILUSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->scsiLuStatus,
                          sizeof(table_entry->scsiLuStatus));
                break;
            case COLUMN_SCSILUSTATE:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->scsiLuState,
                          sizeof(table_entry->scsiLuState));
                break;
            case COLUMN_SCSILUINCOMMANDS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiLuInCommands,
                          sizeof(table_entry->scsiLuInCommands));
                break;
            case COLUMN_SCSILUREADMEGABYTES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiLuReadMegaBytes,
                          sizeof(table_entry->scsiLuReadMegaBytes));
                break;
            case COLUMN_SCSILUWRITTENMEGABYTES:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiLuWrittenMegaBytes,
                          sizeof(table_entry->scsiLuWrittenMegaBytes));
                break;
            case COLUMN_SCSILUINRESETS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiLuInResets,
                          sizeof(table_entry->scsiLuInResets));
                break;
            case COLUMN_SCSILUOUTTASKSETFULLSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER,
                          (u_char *)&table_entry->scsiLuOutTaskSetFullStatus,
                          sizeof(table_entry->scsiLuOutTaskSetFullStatus));
                break;
            case COLUMN_SCSILUHSINCOMMANDS:
                snmp_set_var_typed_value(request->requestvb, ASN_COUNTER64,
                          (u_char *)&table_entry->scsiLuHSInCommands,
                          sizeof(table_entry->scsiLuHSInCommands));
                break;
            case COLUMN_SCSILULASTCREATION:
                snmp_set_var_typed_value(request->requestvb, ASN_TIMETICKS,
                          (u_char *)&table_entry->scsiLuLastCreation,
                          sizeof(table_entry->scsiLuLastCreation));
                break;
            }
        }
        break;

    }
    return SNMP_ERR_NOERROR;
}

#define PROC_SCSI_LU "/proc/iscsi_target/mib/scsi_lu"
#define SCSI_LU_LINE_32 "%lu %lu %lu %llu %s %lu %s %s %llu %lu %lu %lu"
#define SCSI_LU_LINE_64 "%lu %lu %lu %lu %s %lu %s %s %lu %lu %lu %lu"

int 
scsiLuTable_load(netsnmp_cache *cache, void *vmagic)
{
    FILE *fp;
    char line[512];
    struct scsiLuTable_entry tmp, *entry;
    char status[16];
    char state[36];
    char luName[12];
    u_int64_t inCommands;

    if (scsiLuTable_head)
        scsiLuTable_free(NULL, NULL);

    if (!(fp = fopen(PROC_SCSI_LU, "r"))) {
        //snmp_log(LOG_DEBUG, "snmpd: cannot open %s\n", PROC_SCSI_LU);
        return -1;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp, 0, sizeof(tmp));
        if (sscanf(line, (sizeof(long) == 8)? SCSI_LU_LINE_64 : SCSI_LU_LINE_32,
                   &tmp.scsiInstIndex, &tmp.scsiDeviceIndex,
                   &tmp.scsiLuIndex, (u_int64_t *)tmp.scsiLuDefaultLun,
                   luName, &tmp.scsiLuPeripheralType, status, state,
                   &inCommands, &tmp.scsiLuReadMegaBytes,
                   &tmp.scsiLuWrittenMegaBytes, &tmp.scsiLuLastCreation) != 12)
            continue;

        if (strcmp(luName, "None"))
            strcpy(tmp.scsiLuWwnName, luName);

        if (!strcmp(status, "available"))
            tmp.scsiLuStatus = SCSI_LU_STATUS_AVAILABLE;
        else if (!strcmp(status, "notavailable"))
            tmp.scsiLuStatus = SCSI_LU_STATUS_NOTAVAILABLE;
        else
            tmp.scsiLuStatus = SCSI_LU_STATUS_UNKNOWN;

        tmp.scsiLuHSInCommands.high = (inCommands >> 32) & 0xffffffff;
        tmp.scsiLuHSInCommands.low = inCommands & 0xffffffff;

//TODO: Check this and tmp.scsiLuDefaultLun
        tmp.scsiLuInCommands = tmp.scsiLuHSInCommands.low;

        /* Use state "exposed (bit 2)" for now */
        tmp.scsiLuState[0] = (1 << 5);

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "vendor: %s", tmp.scsiLuVendorId) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.scsiLuVendorId, line + strlen("vendor: "));
        }
        else
            break;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "model: %s", tmp.scsiLuProductId) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.scsiLuProductId, line + strlen("model: "));
        }
        else
            break;

        if (line != fgets(line, sizeof(line), fp))
            break;
        if (sscanf(line, "revision: %s", tmp.scsiLuRevisionId) == 1) {
            *(line + strlen(line) - 1) = 0;
            strcpy(tmp.scsiLuRevisionId, line + strlen("revision: "));
        }
        else
            break;

        entry = SNMP_MALLOC_TYPEDEF(struct scsiLuTable_entry);
        if (!entry)
            break;
        memcpy(entry, &tmp, sizeof(tmp));
        entry->next = scsiLuTable_head;
        scsiLuTable_head = entry;
    }
    fclose(fp);
    return 0;
}

void
scsiLuTable_free(netsnmp_cache *cache, void *vmagic)
{
    struct scsiLuTable_entry *entry;

    while (scsiLuTable_head) {
        entry = scsiLuTable_head;
        scsiLuTable_head = scsiLuTable_head->next;
        SNMP_FREE(entry);
    }
}

