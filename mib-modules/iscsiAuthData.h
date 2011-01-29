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
#ifndef ISCSIAUTHDATA_H
#define ISCSIAUTHDATA_H

#define AUTH_MAX_NAME_LEN	224

/* 
 * Structures used for maintaining initiator authentication database 
 */
typedef struct authCred_entry_s {
    uint16_t	tpgt;
    uint16_t	enforceAuth;
    char	chapUserName[AUTH_MAX_NAME_LEN];
    struct authCred_entry_s *next;
} authCred_entry_t;

typedef struct authId_entry_s {
    uint32_t	authIdIndex;
    char	authIdName[AUTH_MAX_NAME_LEN];
    struct authCred_entry_s *authCred_list;
    struct authId_entry_s *next;
} authId_entry_t;

extern int load_auth_data(authId_entry_t **authId_head);
extern uint32_t find_authId_index(char *intrName);

#endif /* ISCSIAUTHDATA_H */
