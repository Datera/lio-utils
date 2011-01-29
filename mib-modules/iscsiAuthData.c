/*
 * Copyright (c) 2006 SBE, Inc.
 * Copyright (c) 2009-2010 Linux-iSCSI.org
 *
 * Nicholas A. Bellinger <nab@kernel.org>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */
#include <sys/stat.h>
#include <net-snmp/net-snmp-config.h>
#include <net-snmp/net-snmp-includes.h>
#include "iscsiAuthData.h"

/*
 * Maintains authentication database with index values
 */

static uint32_t
get_authId_index(authId_entry_t *authId_list, char *authIdName)
{
    static uint32_t authIdIndex = 1;
    uint32_t index = 0;
    authId_entry_t *entry = authId_list;

    /* Use the index from the original list, if found */ 
    while (entry) {
        if (!strcmp(entry->authIdName, authIdName)) {
            index = entry->authIdIndex;
            break;
        }
        entry = entry->next;
    }

    if (!index)
        index = authIdIndex++;

    return index;
}

#define PROC_IPS_AUTH "/proc/iscsi_target/mib/ips_auth"
#define IPS_AUTH_LINE "%u %u"
static void
update_enforce_auth(authId_entry_t *authId_list)
{
    FILE *fp;
    char line[80];
    u_int tpgt, enforceAuth;
    authId_entry_t *authId_entry;
    authCred_entry_t *authCred_entry;

    if (authId_list == NULL)
        return;

    if (!(fp = fopen(PROC_IPS_AUTH, "r"))) {
        snmp_log(LOG_ERR, "snmpd: cannot open %s\n", PROC_IPS_AUTH);
        return;
    }
 
    while (line == fgets(line, sizeof(line), fp)) {
        if (sscanf(line, IPS_AUTH_LINE, &tpgt, &enforceAuth) != 2)
            continue;

        for (authId_entry = authId_list; authId_entry;
             authId_entry = authId_entry->next) {
            for (authCred_entry = authId_entry->authCred_list; authCred_entry;
                 authCred_entry = authCred_entry->next) {
                if ((authCred_entry->tpgt == tpgt) && 
                     (authCred_entry->enforceAuth != enforceAuth))
                    authCred_entry->enforceAuth = enforceAuth;
            }
        }
    }
    fclose(fp);
}

static void
free_auth_data(authId_entry_t *authId_list)
{
    authId_entry_t *authId_entry;
    authCred_entry_t *authCred_entry;

    while (authId_list) {
        authId_entry = authId_list;
        authId_list = authId_list->next;
        while (authId_entry->authCred_list) {
            authCred_entry = authId_entry->authCred_list;
            authId_entry->authCred_list = authCred_entry->next;
            SNMP_FREE(authCred_entry);
        }
        SNMP_FREE(authId_entry);
    }
}

#define AUTH_CONF_FILE "/etc/sysconfig/target_auth"
#define AUTH_CONF_LINE "%s %s %d %s"
static time_t auth_conf_mtime = 0;
static authId_entry_t *authId_list = NULL;

int 
load_auth_data(authId_entry_t **authId_head)
{
    FILE *fp;
    struct stat sbuf;
    char line[1024];
    authId_entry_t *tmp_authId_list = NULL;
    authId_entry_t *authId_entry;
    authId_entry_t tmp_authId;
    authCred_entry_t tmp_authCred;
    authCred_entry_t *authCred_entry;
    char tmpstr[16];
    int tmp, found = 0;

    if (stat(AUTH_CONF_FILE, &sbuf)) {
	printf("File %s doesn't exist?\n", AUTH_CONF_FILE);
        free_auth_data(authId_list);
        *authId_head = NULL;
    }

#if 0
    /* Debug code */ 
    printf("mtime1: %s", ctime(&sbuf.st_mtime)); 
    printf("mtime2: %s\n", ctime(&auth_conf_mtime)); 
#endif

    if (sbuf.st_mtime == auth_conf_mtime) {
        /* No changes to the file since the last load */
        *authId_head = authId_list;
        update_enforce_auth(authId_list);
        return 0;
    }

    if (!(fp = fopen(AUTH_CONF_FILE, "r"))) {
        snmp_log(LOG_ERR, "snmpd: cannot open %s\n", AUTH_CONF_FILE);
        *authId_head = NULL;
        return -1;
    }

    auth_conf_mtime = sbuf.st_mtime;

    while (line == fgets(line, sizeof(line), fp)) {
        memset(&tmp_authId, 0, sizeof(tmp_authId));
        memset(&tmp_authCred, 0, sizeof(tmp_authCred));
        if (sscanf(line, AUTH_CONF_LINE, tmpstr, tmp_authId.authIdName, &tmp,
                   tmp_authCred.chapUserName) != 4)
            continue;               

        if (tmpstr[0] == '#')
            continue;

        if (tmp_authCred.chapUserName[0] == '"')
            tmp_authCred.chapUserName[0] = 0;

        tmp_authCred.tpgt = atoi(tmpstr + 6);

        /* If this authId entry doesn't exist in the list, add it */ 
        for (authId_entry = tmp_authId_list; authId_entry;
             authId_entry = authId_entry->next) {
            if (!strcmp(authId_entry->authIdName, tmp_authId.authIdName)) {
                found = 1;
                break;
            }
        }

        if (!found) {
            tmp_authId.authIdIndex = get_authId_index(authId_list,
                                                      tmp_authId.authIdName);
            authId_entry = SNMP_MALLOC_TYPEDEF(authId_entry_t);
            if (!authId_entry)
                break;
            memcpy(authId_entry, &tmp_authId, sizeof(tmp_authId));
            authId_entry->next = tmp_authId_list;
            tmp_authId_list = authId_entry;
        }

        /* If this authCred entry doesn't exist, add it */ 
        found = 0;
        for (authCred_entry = authId_entry->authCred_list; authCred_entry;
             authCred_entry = authCred_entry->next) {
            if ((authCred_entry->tpgt == tmp_authCred.tpgt) &&
                !strcmp(authCred_entry->chapUserName,
                        tmp_authCred.chapUserName)) {
                found = 1;
                break;
            }
        }
        if (!found) {
            authCred_entry = SNMP_MALLOC_TYPEDEF(authCred_entry_t);
            if (!authCred_entry)
                break;
            memcpy(authCred_entry, &tmp_authCred, sizeof(tmp_authCred));
            authCred_entry->next = authId_entry->authCred_list;
            authId_entry->authCred_list = authCred_entry;
        }
    }
    update_enforce_auth(tmp_authId_list);

#if 0
    /* Debug code */
    for (authId_entry = tmp_authId_list; authId_entry;
         authId_entry = authId_entry->next) {
            printf("index %d, authIdName %s\n", authId_entry->authIdIndex,
                   authId_entry->authIdName);
            for (authCred_entry = authId_entry->authCred_list; authCred_entry;
                 authCred_entry = authCred_entry->next) {
                printf("tpgt %d, chapUserName %s\n", authCred_entry->tpgt,
                       authCred_entry->chapUserName);
        }
    }
#endif
    
    /* Update list pointer */
    free_auth_data(authId_list);
    *authId_head = authId_list = tmp_authId_list;
    fclose(fp);
    return 0;
}

uint32_t
find_authId_index(char *intrName)
{
    authId_entry_t *authId_head, *authId_entry;
    uint32_t index = 0;

    load_auth_data(&authId_head);
    if (authId_head == NULL)
        return 0;

    for (authId_entry = authId_head; authId_entry;
         authId_entry = authId_entry->next) {
        if (!strcmp(authId_entry->authIdName, intrName)) {
            index = authId_entry->authIdIndex;
            break;
        }
    }
    return index;
}
