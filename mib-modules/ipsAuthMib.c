/*
 * Copyright (c) 2006 SBE, Inc.
 * Copyright (c) 2009 Linux-iSCSI.org
 */

#include <sys/stat.h>
#include <net-snmp/net-snmp-config.h>
#include <net-snmp/net-snmp-includes.h>
#include <net-snmp/agent/net-snmp-agent-includes.h>
#include "common.h"
#include "iscsiAuthData.h"
#include "ipsAuthMib.h"

#define IPS_AUTH_MIB_CACHE_TIMEOUT 10

/* 
 * Initializes the ipsAuthMib module 
 */
void
init_ipsAuthMib(void)
{
    /* Initialize all tables */
    initialize_table_ipsAuthInstAttr();
    initialize_table_ipsAuthIdentAttr();
    initialize_table_ipsAuthIdentNameAttr();
    initialize_table_ipsAuthCredAttr();
    initialize_table_ipsAuthCredChapAttr();
}

/*
 * Instance Attributes Table
 */

/* 
 * Initialize the ipsAuthInstAttr table
 */
void
initialize_table_ipsAuthInstAttr(void)
{
    static oid ipsAuthInstAttr_oid[] = {OID_LIO_IPS_AUTH_MIB,1,2,2};
    size_t ipsAuthInstAttr_oid_len = OID_LENGTH(ipsAuthInstAttr_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("ipsAuthInstAttr",
                                              ipsAuthInstAttr_handler,
                                              ipsAuthInstAttr_oid,
                                              ipsAuthInstAttr_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* ipsAuthInstIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 3;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = ipsAuthInstAttr_get_first_data_point;
    iinfo->get_next_data_point = ipsAuthInstAttr_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(IPS_AUTH_MIB_CACHE_TIMEOUT,
                                             ipsAuthInstAttr_load, 
                                             ipsDummy_free,
                                             ipsAuthInstAttr_oid, 
                                             ipsAuthInstAttr_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
ipsAuthInstAttr_cache_update(void)
{
    static marker_t ipsAuthInstAttr_cache_marker = NULL;

    if (ipsAuthInstAttr_cache_marker &&
        (!atime_ready(ipsAuthInstAttr_cache_marker,
                      IPS_AUTH_MIB_CACHE_TIMEOUT * 1000)))
        return;

    if (ipsAuthInstAttr_cache_marker)
        atime_setMarker(ipsAuthInstAttr_cache_marker);
    else
        ipsAuthInstAttr_cache_marker = atime_newMarker();

    ipsAuthInstAttr_load(NULL, NULL);
}
#endif

struct ipsAuthInstAttr_entry *ipsAuthInstAttr_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
ipsAuthInstAttr_get_first_data_point(void **my_loop_context,
                                     void **my_data_context,
                                     netsnmp_variable_list *put_index_data,
                                     netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    ipsAuthInstAttr_cache_update();
#endif
    *my_loop_context = ipsAuthInstAttr_head;
    return ipsAuthInstAttr_get_next_data_point(my_loop_context, my_data_context,
                                               put_index_data, mydata);
}

netsnmp_variable_list *
ipsAuthInstAttr_get_next_data_point(void **my_loop_context,
                                    void **my_data_context,
                                    netsnmp_variable_list *put_index_data,
                                    netsnmp_iterator_info *mydata)
{
    struct ipsAuthInstAttr_entry *entry =
                               (struct ipsAuthInstAttr_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthInstIndex,
                           sizeof(entry->ipsAuthInstIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the ipsAuthInstAttr table
 */
int
ipsAuthInstAttr_handler(netsnmp_mib_handler *handler,
                        netsnmp_handler_registration *reginfo,
                        netsnmp_agent_request_info *reqinfo,
                        netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct ipsAuthInstAttr_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct ipsAuthInstAttr_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_IPSAUTHINSTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->ipsAuthInstIndex,
                          sizeof(table_entry->ipsAuthInstIndex));
                break;
            case COLUMN_IPSAUTHINSTDESCR:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->ipsAuthInstDescr,
                          strlen(table_entry->ipsAuthInstDescr));
                break;
            case COLUMN_IPSAUTHINSTSTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthInstStorageType,
                          sizeof(table_entry->ipsAuthInstStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

int 
ipsAuthInstAttr_load(netsnmp_cache *cache, void *vmagic)
{
    struct ipsAuthInstAttr_entry *entry;

    if (ipsAuthInstAttr_head)
        return 0;

    entry = SNMP_MALLOC_TYPEDEF(struct ipsAuthInstAttr_entry);
    if (!entry)
        return -1;

    entry->ipsAuthInstIndex = AUTH_INST_INDEX;
    strcpy(entry->ipsAuthInstDescr, "iSCSI Target");
    entry->ipsAuthInstStorageType = ST_READONLY;
    ipsAuthInstAttr_head = entry;

     return 0;
}

/*
 * User Identity Attributes Table
 */

/*
 * Initialize the ipsAuthIdentAttr table
 */
void
initialize_table_ipsAuthIdentAttr(void)
{
    static oid ipsAuthIdentAttr_oid[] = {OID_LIO_IPS_AUTH_MIB,1,3,1};
    size_t ipsAuthIdentAttr_oid_len = OID_LENGTH(ipsAuthIdentAttr_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("ipsAuthIdentAttr",
                                              ipsAuthIdentAttr_handler,
                                              ipsAuthIdentAttr_oid,
                                              ipsAuthIdentAttr_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* ipsAuthInstIndex */
                                     ASN_UNSIGNED,  /* ipsAuthIdentIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 5;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = ipsAuthIdentAttr_get_first_data_point;
    iinfo->get_next_data_point = ipsAuthIdentAttr_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(IPS_AUTH_MIB_CACHE_TIMEOUT,
                                             ipsAuthIdentAttr_load, 
                                             ipsDummy_free,
                                             ipsAuthIdentAttr_oid, 
                                             ipsAuthIdentAttr_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
ipsAuthIdentAttr_cache_update(void)
{
    static marker_t ipsAuthIdentAttr_cache_marker = NULL;

    if (ipsAuthIdentAttr_cache_marker &&
        (!atime_ready(ipsAuthIdentAttr_cache_marker,
                      IPS_AUTH_MIB_CACHE_TIMEOUT * 1000)))
        return;

    if (ipsAuthIdentAttr_cache_marker)
        atime_setMarker(ipsAuthIdentAttr_cache_marker);
    else
        ipsAuthIdentAttr_cache_marker = atime_newMarker();

    ipsAuthIdentAttr_load(NULL, NULL);
}
#endif

struct ipsAuthIdentAttr_entry *ipsAuthIdentAttr_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
ipsAuthIdentAttr_get_first_data_point(void **my_loop_context,
                                      void **my_data_context,
                                      netsnmp_variable_list *put_index_data,
                                      netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    ipsAuthIdentAttr_cache_update();
#endif
    *my_loop_context = ipsAuthIdentAttr_head;
    return ipsAuthIdentAttr_get_next_data_point(my_loop_context,
                                                my_data_context,
                                                put_index_data, mydata);
}

netsnmp_variable_list *
ipsAuthIdentAttr_get_next_data_point(void **my_loop_context,
                                     void **my_data_context,
                                     netsnmp_variable_list *put_index_data,
                                     netsnmp_iterator_info *mydata)
{
    struct ipsAuthIdentAttr_entry *entry =
                             (struct ipsAuthIdentAttr_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthInstIndex,
                           sizeof(entry->ipsAuthInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthIdentIndex,
                           sizeof(entry->ipsAuthIdentIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the ipsAuthIdentAttr table
 */
int
ipsAuthIdentAttr_handler(netsnmp_mib_handler *handler,
                         netsnmp_handler_registration *reginfo,
                         netsnmp_agent_request_info *reqinfo,
                         netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct ipsAuthIdentAttr_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct ipsAuthIdentAttr_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_IPSAUTHIDENTINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->ipsAuthIdentIndex,
                          sizeof(table_entry->ipsAuthIdentIndex));
                break;
            case COLUMN_IPSAUTHIDENTDESCRIPTION:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->ipsAuthIdentDescription,
                          strlen(table_entry->ipsAuthIdentDescription));
                break;
            case COLUMN_IPSAUTHIDENTROWSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthIdentRowStatus,
                          sizeof(table_entry->ipsAuthIdentRowStatus));
                break;
            case COLUMN_IPSAUTHIDENTSTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthIdentStorageType,
                          sizeof(table_entry->ipsAuthIdentStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

void
ipsAuthIdentAttr_free(void)
{
    struct ipsAuthIdentAttr_entry *entry;

    while (ipsAuthIdentAttr_head) {
        entry = ipsAuthIdentAttr_head;
        ipsAuthIdentAttr_head = ipsAuthIdentAttr_head->next;
        SNMP_FREE(entry);
    }
}

int 
ipsAuthIdentAttr_load(netsnmp_cache *cache, void *vmagic)
{
    struct ipsAuthIdentAttr_entry *entry;
    static authId_entry_t *prev_authId_head = NULL;
    authId_entry_t *authId_head, *authId_entry;

    load_auth_data(&authId_head);
    if (authId_head == prev_authId_head) {
        /* No change to the cache */
        return 0;
    }

    if (ipsAuthIdentAttr_head)
        ipsAuthIdentAttr_free();

    prev_authId_head = authId_head;

    if (authId_head == NULL) {
        return 0;
    }

    for (authId_entry = authId_head; authId_entry;
         authId_entry = authId_entry->next) {
        entry = SNMP_MALLOC_TYPEDEF(struct ipsAuthIdentAttr_entry);
        if (!entry)
            break;
        entry->ipsAuthInstIndex = AUTH_INST_INDEX;
        entry->ipsAuthIdentIndex = authId_entry->authIdIndex;
        strcpy(entry->ipsAuthIdentDescription, authId_entry->authIdName);
        entry->ipsAuthIdentRowStatus = RS_ACTIVE;
        entry->ipsAuthIdentStorageType = ST_READONLY;
        entry->next = ipsAuthIdentAttr_head;
        ipsAuthIdentAttr_head = entry;
    }
    return 0;
}

/*
 * User Identity Attributes Table
 */

/*
 * Initialize the ipsAuthIdentNameAttr table
 */
void
initialize_table_ipsAuthIdentNameAttr(void)
{
    static oid ipsAuthIdentNameAttr_oid[] = {OID_LIO_IPS_AUTH_MIB,1,4,1};
    size_t ipsAuthIdentNameAttr_oid_len = OID_LENGTH(ipsAuthIdentNameAttr_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("ipsAuthIdentNameAttr",
                                              ipsAuthIdentNameAttr_handler,
                                              ipsAuthIdentNameAttr_oid,
                                              ipsAuthIdentNameAttr_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* ipsAuthInstIndex */
                                     ASN_UNSIGNED,  /* ipsAuthIdentIndex */
                                     ASN_UNSIGNED,  /* ipsAuthIdentNameIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = ipsAuthIdentNameAttr_get_first_data_point;
    iinfo->get_next_data_point = ipsAuthIdentNameAttr_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(IPS_AUTH_MIB_CACHE_TIMEOUT,
                                             ipsAuthIdentNameAttr_load, 
                                             ipsDummy_free,
                                             ipsAuthIdentNameAttr_oid, 
                                             ipsAuthIdentNameAttr_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
ipsAuthIdentNameAttr_cache_update(void)
{
    static marker_t ipsAuthIdentNameAttr_cache_marker = NULL;

    if (ipsAuthIdentNameAttr_cache_marker &&
        (!atime_ready(ipsAuthIdentNameAttr_cache_marker,
                      IPS_AUTH_MIB_CACHE_TIMEOUT * 1000)))
        return;

    if (ipsAuthIdentNameAttr_cache_marker)
        atime_setMarker(ipsAuthIdentNameAttr_cache_marker);
    else
        ipsAuthIdentNameAttr_cache_marker = atime_newMarker();

    ipsAuthIdentNameAttr_load(NULL, NULL);
}
#endif

struct ipsAuthIdentNameAttr_entry *ipsAuthIdentNameAttr_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
ipsAuthIdentNameAttr_get_first_data_point(void **my_loop_context,
                                          void **my_data_context,
                                          netsnmp_variable_list *put_index_data,
                                          netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    ipsAuthIdentNameAttr_cache_update();
#endif
    *my_loop_context = ipsAuthIdentNameAttr_head;
    return ipsAuthIdentNameAttr_get_next_data_point(my_loop_context,
                                                    my_data_context,
                                                    put_index_data, mydata);
}

netsnmp_variable_list *
ipsAuthIdentNameAttr_get_next_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
    struct ipsAuthIdentNameAttr_entry *entry =
                         (struct ipsAuthIdentNameAttr_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthInstIndex,
                           sizeof(entry->ipsAuthInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthIdentIndex,
                           sizeof(entry->ipsAuthIdentIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthIdentNameIndex,
                           sizeof(entry->ipsAuthIdentNameIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the ipsAuthIdentNameAttr table
 */
int
ipsAuthIdentNameAttr_handler(netsnmp_mib_handler *handler,
                             netsnmp_handler_registration *reginfo,
                             netsnmp_agent_request_info *reqinfo,
                             netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct ipsAuthIdentNameAttr_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct ipsAuthIdentNameAttr_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_IPSAUTHIDENTNAMEINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->ipsAuthIdentNameIndex,
                          sizeof(table_entry->ipsAuthIdentNameIndex));
                break;
            case COLUMN_IPSAUTHIDENTNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->ipsAuthIdentName,
                          strlen(table_entry->ipsAuthIdentName));
                break;
            case COLUMN_IPSAUTHIDENTNAMEROWSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthIdentNameRowStatus,
                          sizeof(table_entry->ipsAuthIdentNameRowStatus));
                break;
            case COLUMN_IPSAUTHIDENTNAMESTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthIdentNameStorageType,
                          sizeof(table_entry->ipsAuthIdentNameStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

void
ipsAuthIdentNameAttr_free(void)
{
    struct ipsAuthIdentNameAttr_entry *entry;

    while (ipsAuthIdentNameAttr_head) {
        entry = ipsAuthIdentNameAttr_head;
        ipsAuthIdentNameAttr_head = ipsAuthIdentNameAttr_head->next;
        SNMP_FREE(entry);
    }
}

int 
ipsAuthIdentNameAttr_load(netsnmp_cache *cache, void *vmagic)
{
    struct ipsAuthIdentNameAttr_entry *entry;
    static authId_entry_t *prev_authId_head = NULL;
    authId_entry_t *authId_head, *authId_entry;

    load_auth_data(&authId_head);
    if (authId_head == prev_authId_head) {
        /* No change to the cache */
        return 0;
    }

    if (ipsAuthIdentNameAttr_head)
        ipsAuthIdentNameAttr_free();

    prev_authId_head = authId_head;

    if (authId_head == NULL) {
        return 0;
    }

    for (authId_entry = authId_head; authId_entry;
         authId_entry = authId_entry->next) {

        entry = SNMP_MALLOC_TYPEDEF(struct ipsAuthIdentNameAttr_entry);
        if (!entry)
            break;
        entry->ipsAuthInstIndex = AUTH_INST_INDEX;
        entry->ipsAuthIdentIndex = authId_entry->authIdIndex;
        entry->ipsAuthIdentNameIndex = AUTH_ID_NAME_INDEX;
        strcpy(entry->ipsAuthIdentName, authId_entry->authIdName);
        entry->ipsAuthIdentNameRowStatus = RS_ACTIVE;
        entry->ipsAuthIdentNameStorageType = ST_READONLY;
        entry->next = ipsAuthIdentNameAttr_head;
        ipsAuthIdentNameAttr_head = entry;
    }
    return 0;
}

/*
 * Credential Attributes Table
 */

/*
 * Initialize the ipsAuthCredAttr table
 */
void
initialize_table_ipsAuthCredAttr(void)
{
    static oid ipsAuthCredAttr_oid[] = {OID_LIO_IPS_AUTH_MIB,1,6,1};
    size_t ipsAuthCredAttr_oid_len = OID_LENGTH(ipsAuthCredAttr_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("ipsAuthCredAttr",
                                              ipsAuthCredAttr_handler,
                                              ipsAuthCredAttr_oid,
                                              ipsAuthCredAttr_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* ipsAuthInstIndex */
                                     ASN_UNSIGNED,  /* ipsAuthIdentIndex */
                                     ASN_UNSIGNED,  /* ipsAuthCredIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = ipsAuthCredAttr_get_first_data_point;
    iinfo->get_next_data_point = ipsAuthCredAttr_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(IPS_AUTH_MIB_CACHE_TIMEOUT,
                                             ipsAuthCredAttr_load, 
                                             ipsAuthCredAttr_free,
                                             ipsAuthCredAttr_oid, 
                                             ipsAuthCredAttr_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
ipsAuthCredAttr_cache_update(void)
{
    static marker_t ipsAuthCredAttr_cache_marker = NULL;

    if (ipsAuthCredAttr_cache_marker &&
        (!atime_ready(ipsAuthCredAttr_cache_marker,
                      IPS_AUTH_MIB_CACHE_TIMEOUT * 1000)))
        return;

    if (ipsAuthCredAttr_cache_marker)
        atime_setMarker(ipsAuthCredAttr_cache_marker);
    else
        ipsAuthCredAttr_cache_marker = atime_newMarker();

    ipsAuthCredAttr_load(NULL, NULL);
}
#endif

struct ipsAuthCredAttr_entry *ipsAuthCredAttr_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
ipsAuthCredAttr_get_first_data_point(void **my_loop_context,
                                     void **my_data_context,
                                     netsnmp_variable_list *put_index_data,
                                     netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    ipsAuthCredAttr_cache_update();
#endif
    *my_loop_context = ipsAuthCredAttr_head;
    return ipsAuthCredAttr_get_next_data_point(my_loop_context,
                                               my_data_context,
                                               put_index_data, mydata);
}

netsnmp_variable_list *
ipsAuthCredAttr_get_next_data_point(void **my_loop_context,
                                    void **my_data_context,
                                    netsnmp_variable_list *put_index_data,
                                    netsnmp_iterator_info *mydata)
{
    struct ipsAuthCredAttr_entry *entry =
                             (struct ipsAuthCredAttr_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthInstIndex,
                           sizeof(entry->ipsAuthInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthIdentIndex,
                           sizeof(entry->ipsAuthIdentIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthCredIndex,
                           sizeof(entry->ipsAuthCredIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the ipsAuthCredAttr table
 */
int
ipsAuthCredAttr_handler(netsnmp_mib_handler *handler,
                        netsnmp_handler_registration *reginfo,
                        netsnmp_agent_request_info *reqinfo,
                        netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct ipsAuthCredAttr_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct ipsAuthCredAttr_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_IPSAUTHCREDINDEX:
                snmp_set_var_typed_value(request->requestvb, ASN_UNSIGNED,
                          (u_char *)&table_entry->ipsAuthCredIndex,
                          sizeof(table_entry->ipsAuthCredIndex));
                break;
            case COLUMN_IPSAUTHCREDAUTHMETHOD:
                snmp_set_var_typed_value(request->requestvb, ASN_OBJECT_ID,
                          (u_char *)&table_entry->ipsAuthCredAuthMethod,
                          table_entry->ipsAuthCredAuthMethod_len * sizeof(oid));
                break;
            case COLUMN_IPSAUTHCREDROWSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthCredRowStatus,
                          sizeof(table_entry->ipsAuthCredRowStatus));
                break;
            case COLUMN_IPSAUTHCREDSTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthCredStorageType,
                          sizeof(table_entry->ipsAuthCredStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

void
ipsAuthCredAttr_free(netsnmp_cache *cache, void *vmagic)
{
    struct ipsAuthCredAttr_entry *entry;

    while (ipsAuthCredAttr_head) {
        entry = ipsAuthCredAttr_head;
        ipsAuthCredAttr_head = ipsAuthCredAttr_head->next;
        SNMP_FREE(entry);
    }
}

static oid ipsAuthMethodNone_oid[] = {OID_LIO_IPS_AUTH_MIB,1,1,1,1};
static oid ipsAuthMethodChap_oid[] = {OID_LIO_IPS_AUTH_MIB,1,1,1,3};
int 
ipsAuthCredAttr_load(netsnmp_cache *cache, void *vmagic)
{
    struct ipsAuthCredAttr_entry *entry;
    authId_entry_t *authId_head, *authId_entry;
    authCred_entry_t *authCred_entry;

    if (ipsAuthCredAttr_head)
        ipsAuthCredAttr_free(NULL, NULL);

    load_auth_data(&authId_head);

    if (authId_head == NULL) {
        return 0;
    }

    for (authId_entry = authId_head; authId_entry;
         authId_entry = authId_entry->next) {
        for (authCred_entry = authId_entry->authCred_list; authCred_entry;
             authCred_entry = authCred_entry->next) {
            entry = SNMP_MALLOC_TYPEDEF(struct ipsAuthCredAttr_entry);
            if (!entry)
                break;
            entry->ipsAuthInstIndex = AUTH_INST_INDEX;
            entry->ipsAuthIdentIndex = authId_entry->authIdIndex;
            entry->ipsAuthCredIndex = authCred_entry->tpgt + 1;

            if (authCred_entry->enforceAuth)
                memcpy(entry->ipsAuthCredAuthMethod, ipsAuthMethodChap_oid,
                       sizeof(ipsAuthMethodChap_oid)); 
            else
                memcpy(entry->ipsAuthCredAuthMethod, ipsAuthMethodNone_oid,
                       sizeof(ipsAuthMethodNone_oid)); 
            entry->ipsAuthCredAuthMethod_len =
                                            OID_LENGTH(ipsAuthMethodNone_oid);
            entry->ipsAuthCredRowStatus = RS_ACTIVE;
            entry->ipsAuthCredStorageType = ST_READONLY;
            entry->next = ipsAuthCredAttr_head;
            ipsAuthCredAttr_head = entry;
        }
    }
    return 0;
}

/*
 * Credential Chap-Specific Attributes Table
 */

/*
 * Initialize the ipsAuthCredChapAttr table
 */
void
initialize_table_ipsAuthCredChapAttr(void)
{
    static oid ipsAuthCredChapAttr_oid[] = {OID_LIO_IPS_AUTH_MIB,1,7,1};
    size_t ipsAuthCredChapAttr_oid_len = OID_LENGTH(ipsAuthCredChapAttr_oid);
    netsnmp_handler_registration    *reg;
    netsnmp_iterator_info           *iinfo;
    netsnmp_table_registration_info *table_info;

    reg = netsnmp_create_handler_registration("ipsAuthCredChapAttr",
                                              ipsAuthCredChapAttr_handler,
                                              ipsAuthCredChapAttr_oid,
                                              ipsAuthCredChapAttr_oid_len,
                                              HANDLER_CAN_RONLY);

    table_info = SNMP_MALLOC_TYPEDEF(netsnmp_table_registration_info);
    netsnmp_table_helper_add_indexes(table_info,
                                     ASN_UNSIGNED,  /* ipsAuthInstIndex */
                                     ASN_UNSIGNED,  /* ipsAuthIdentIndex */
                                     ASN_UNSIGNED,  /* ipsAuthCredIndex */
                                     0);
    table_info->min_column = 1;
    table_info->max_column = 6;
    
    iinfo = SNMP_MALLOC_TYPEDEF(netsnmp_iterator_info);
    iinfo->get_first_data_point = ipsAuthCredChapAttr_get_first_data_point;
    iinfo->get_next_data_point = ipsAuthCredChapAttr_get_next_data_point;
    iinfo->table_reginfo = table_info;
    
    netsnmp_register_table_iterator(reg, iinfo);

#if HAVE_CACHE_HANDLER
    /* Initialize the contents of the table */
    netsnmp_inject_handler(reg, 
                   netsnmp_get_cache_handler(IPS_AUTH_MIB_CACHE_TIMEOUT,
                                             ipsAuthCredChapAttr_load, 
                                             ipsAuthCredChapAttr_free,
                                             ipsAuthCredChapAttr_oid, 
                                             ipsAuthCredChapAttr_oid_len));
#endif
}

#if !HAVE_CACHE_HANDLER
void
ipsAuthCredChapAttr_cache_update(void)
{
    static marker_t ipsAuthCredChapAttr_cache_marker = NULL;

    if (ipsAuthCredChapAttr_cache_marker &&
        (!atime_ready(ipsAuthCredChapAttr_cache_marker,
                      IPS_AUTH_MIB_CACHE_TIMEOUT * 1000)))
        return;

    if (ipsAuthCredChapAttr_cache_marker)
        atime_setMarker(ipsAuthCredChapAttr_cache_marker);
    else
        ipsAuthCredChapAttr_cache_marker = atime_newMarker();

    ipsAuthCredChapAttr_load(NULL, NULL);
}
#endif

struct ipsAuthCredChapAttr_entry *ipsAuthCredChapAttr_head = NULL;

/*
 * Iterator hook routines
 */
netsnmp_variable_list *
ipsAuthCredChapAttr_get_first_data_point(void **my_loop_context,
                                         void **my_data_context,
                                         netsnmp_variable_list *put_index_data,
                                         netsnmp_iterator_info *mydata)
{
#if !HAVE_CACHE_HANDLER
    ipsAuthCredChapAttr_cache_update();
#endif
    *my_loop_context = ipsAuthCredChapAttr_head;
    return ipsAuthCredChapAttr_get_next_data_point(my_loop_context,
                                                   my_data_context,
                                                   put_index_data, mydata);
}

netsnmp_variable_list *
ipsAuthCredChapAttr_get_next_data_point(void **my_loop_context,
                                        void **my_data_context,
                                        netsnmp_variable_list *put_index_data,
                                        netsnmp_iterator_info *mydata)
{
    struct ipsAuthCredChapAttr_entry *entry =
                         (struct ipsAuthCredChapAttr_entry *)*my_loop_context;
    netsnmp_variable_list *idx = put_index_data;

    if (entry) {
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthInstIndex,
                           sizeof(entry->ipsAuthInstIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthIdentIndex,
                           sizeof(entry->ipsAuthIdentIndex));
        idx = idx->next_variable;
        snmp_set_var_value(idx, (u_char *)&entry->ipsAuthCredIndex,
                           sizeof(entry->ipsAuthCredIndex));
        idx = idx->next_variable;
        *my_data_context = (void *)entry;
        *my_loop_context = (void *)entry->next;
        return put_index_data;
    } else {
        return NULL;
    }
}

/*
 * Handles requests for the ipsAuthCredChapAttr table
 */
int
ipsAuthCredChapAttr_handler(netsnmp_mib_handler *handler,
                            netsnmp_handler_registration *reginfo,
                            netsnmp_agent_request_info *reqinfo,
                            netsnmp_request_info *requests) 
{

    netsnmp_request_info *request;
    netsnmp_table_request_info *table_info;
    struct ipsAuthCredChapAttr_entry *table_entry;

    switch (reqinfo->mode) {
        /*
         * Read-support (also covers GetNext requests)
         */
    case MODE_GET:
        for (request = requests; request; request = request->next) {
            table_entry = (struct ipsAuthCredChapAttr_entry *)
                              netsnmp_extract_iterator_context(request);
            table_info = netsnmp_extract_table_info(request);

            if (!table_entry || !table_info)
                continue;
    
            switch (table_info->colnum) {
            case COLUMN_IPSAUTHCREDCHAPUSERNAME:
                snmp_set_var_typed_value(request->requestvb, ASN_OCTET_STR,
                          (u_char *)table_entry->ipsAuthCredChapUserName,
                          strlen(table_entry->ipsAuthCredChapUserName));
                break;
            case COLUMN_IPSAUTHCREDCHAPROWSTATUS:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthCredChapRowStatus,
                          sizeof(table_entry->ipsAuthCredChapRowStatus));
                break;
            case COLUMN_IPSAUTHCREDCHAPSTORAGETYPE:
                snmp_set_var_typed_value(request->requestvb, ASN_INTEGER,
                          (u_char *)&table_entry->ipsAuthCredChapStorageType,
                          sizeof(table_entry->ipsAuthCredChapStorageType));
                break;
            }
        }
        break;
    }
    return SNMP_ERR_NOERROR;
}

void
ipsAuthCredChapAttr_free(netsnmp_cache *cache, void *vmagic)
{
    struct ipsAuthCredChapAttr_entry *entry;

    while (ipsAuthCredChapAttr_head) {
        entry = ipsAuthCredChapAttr_head;
        ipsAuthCredChapAttr_head = ipsAuthCredChapAttr_head->next;
        SNMP_FREE(entry);
    }
}

int 
ipsAuthCredChapAttr_load(netsnmp_cache *cache, void *vmagic)
{
    struct ipsAuthCredChapAttr_entry *entry;
    authId_entry_t *authId_head, *authId_entry;
    authCred_entry_t *authCred_entry;

    if (ipsAuthCredChapAttr_head)
        ipsAuthCredChapAttr_free(NULL, NULL);

    load_auth_data(&authId_head);

    if (authId_head == NULL) {
        return 0;
    }

    for (authId_entry = authId_head; authId_entry;
         authId_entry = authId_entry->next) {
        for (authCred_entry = authId_entry->authCred_list; authCred_entry;
             authCred_entry = authCred_entry->next) {
            if (!authCred_entry->enforceAuth)
                continue;

            entry = SNMP_MALLOC_TYPEDEF(struct ipsAuthCredChapAttr_entry);
            if (!entry)
                break;

            entry->ipsAuthInstIndex = AUTH_INST_INDEX;
            entry->ipsAuthIdentIndex = authId_entry->authIdIndex;
            entry->ipsAuthCredIndex = authCred_entry->tpgt + 1;
            strcpy(entry->ipsAuthCredChapUserName,
                   authCred_entry->chapUserName);
            entry->ipsAuthCredChapRowStatus = RS_ACTIVE;
            entry->ipsAuthCredChapStorageType = ST_READONLY;
            entry->next = ipsAuthCredChapAttr_head;
            ipsAuthCredChapAttr_head = entry;
        }
    }
    return 0;
}

/* Prevent older versions of net-snmp from crashing */
void
ipsDummy_free(netsnmp_cache *cache, void *vmagic)
{
}
