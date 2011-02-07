/*
 * Copyright (c) 2006 SBE, Inc.
 * Copyright (c) 2009-2011 Linux-iSCSI.org
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */
#ifndef ISCSIMIB_H
#define ISCSIMIB_H

#define ISCSI_NUM_INSTANCES	1
#define ISCSI_NUM_NODES		1

#define ISCSI_MAX_NAME_LEN	224
#define ISCSI_MAX_ALIAS_LEN	256

#define NODE_ROLE_TARGET	(1 << 7)

#define INET_ADDR_TYPE_IPV4	1
#define INET_ADDR_TYPE_IPV6	2

#define INET_ADDR_TYPE_IPV4_LEN 4

#define TRANSPORT_PROTO_TCP	6
#define TRANSPORT_PROTO_SCTP	132 

#define ISCSI_DIGEST_NONE	1     
#define ISCSI_DIGEST_OTHER	2     
#define ISCSI_DIGEST_NODIGEST	3     
#define ISCSI_DIGEST_CRC32C	4     

#define SSN_DIR_INBOUND		1
#define SSN_DIR_OUTBOUND	2

#define SSN_TYPE_NORMAL		1
#define SSN_TYPE_DISCOVERY	2

#define CXN_STATE_LOGIN		1
#define CXN_STATE_FULL		2
#define CXN_STATE_LOGOUT	3

/* iSCSI login failure types (sub oids) */
#define ISCSI_LOGIN_FAIL_OTHER		2
#define ISCSI_LOGIN_FAIL_REDIRECT	3
#define ISCSI_LOGIN_FAIL_AUTHORIZE	4
#define ISCSI_LOGIN_FAIL_AUTHENTICATE	5
#define ISCSI_LOGIN_FAIL_NEGOTIATE	6

/*
 * Instance Attributes Table
 */
void initialize_table_iscsiInstAttributes(void);
Netsnmp_Node_Handler iscsiInstAttributes_handler;
Netsnmp_First_Data_Point iscsiInstAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiInstAttributes_get_next_data_point;
int iscsiInstAttributes_load(netsnmp_cache *cache, void *vmagic);
void iscsiInstAttributes_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSIINSTINDEX			1
#define COLUMN_ISCSIINSTDESCR			2
#define COLUMN_ISCSIINSTVERSIONMIN		3
#define COLUMN_ISCSIINSTVERSIONMAX		4
#define COLUMN_ISCSIINSTVENDORID		5
#define COLUMN_ISCSIINSTVENDORVERSION		6
#define COLUMN_ISCSIINSTPORTALNUMBER		7
#define COLUMN_ISCSIINSTNODENUMBER		8
#define COLUMN_ISCSIINSTSESSIONNUMBER		9
#define COLUMN_ISCSIINSTSSNFAILURES		10
#define COLUMN_ISCSIINSTLASTSSNFAILURETYPE	11
#define COLUMN_ISCSIINSTLASTSSNRMTNODENAME	12
#define COLUMN_ISCSIINSTDISCONTINUITYTIME	13

/* Data structure for row entry */
struct iscsiInstAttributes_entry {
    u_long	iscsiInstIndex;
    char	iscsiInstDescr[64];
    u_long	iscsiInstVersionMin;
    u_long	iscsiInstVersionMax;
    char	iscsiInstVendorID[64];
    char	iscsiInstVendorVersion[64];
    u_long	iscsiInstPortalNumber;
    u_long	iscsiInstNodeNumber;
    u_long	iscsiInstSessionNumber;
    u_long	iscsiInstSsnFailures;
    oid		iscsiInstLastSsnFailureType[MAX_OID_LEN];
    int		iscsiInstLastSsnFailureType_len;
    char	iscsiInstLastSsnRmtNodeName[ISCSI_MAX_NAME_LEN];
    u_long	iscsiInstDiscontinuityTime;
    struct iscsiInstAttributes_entry *next;
};

/*
 * Instance Session Failure Stats Table
 */
void initialize_table_iscsiInstSsnErrStats(void);
Netsnmp_Node_Handler iscsiInstSsnErrStats_handler;
Netsnmp_First_Data_Point iscsiInstSsnErrStats_get_first_data_point;
Netsnmp_Next_Data_Point iscsiInstSsnErrStats_get_next_data_point;
int iscsiInstSsnErrStats_load(netsnmp_cache *cache, void *vmagic);
void iscsiInstSsnErrStats_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSIINSTSSNDIGESTERRORS		1
#define COLUMN_ISCSIINSTSSNCXNTIMEOUTERRORS	2
#define COLUMN_ISCSIINSTSSNFORMATERRORS		3

/* Data structure for row entry */
struct iscsiInstSsnErrStats_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiInstSsnDigestErrors;
    u_long	iscsiInstSsnCxnTimeoutErrors;
    u_long	iscsiInstSsnFormatErrors;
    struct iscsiInstSsnErrStats_entry *next;
};

/*
 * Portal Attributes Table
 */
void initialize_table_iscsiPortalAttributes(void);
Netsnmp_Node_Handler iscsiPortalAttributes_handler;
Netsnmp_First_Data_Point iscsiPortalAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiPortalAttributes_get_next_data_point;
int iscsiPortalAttributes_load(netsnmp_cache *cache, void *vmagic);
void iscsiPortalAttributes_free(netsnmp_cache *cache, void *vmagic);


/* column number definitions */
#define COLUMN_ISCSIPORTALINDEX			1
#define COLUMN_ISCSIPORTALROWSTATUS		2
#define COLUMN_ISCSIPORTALROLES			3
#define COLUMN_ISCSIPORTALADDRTYPE		4
#define COLUMN_ISCSIPORTALADDR			5
#define COLUMN_ISCSIPORTALPROTOCOL		6
#define COLUMN_ISCSIPORTALMAXRECVDATASEGLENGTH	7
#define COLUMN_ISCSIPORTALPRIMARYHDRDIGEST	8
#define COLUMN_ISCSIPORTALPRIMARYDATADIGEST	9
#define COLUMN_ISCSIPORTALSECONDARYHDRDIGEST	10
#define COLUMN_ISCSIPORTALSECONDARYDATADIGEST	11
#define COLUMN_ISCSIPORTALRECVMARKER		12
#define COLUMN_ISCSIPORTALSTORAGETYPE		13

/* Data structure for row entry */
struct iscsiPortalAttributes_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiPortalIndex;
    long	iscsiPortalRowStatus;
    char	iscsiPortalRoles;
    long	iscsiPortalAddrType;
    char	iscsiPortalAddr[16];
    u_long	iscsiPortalProtocol;
    u_long	iscsiPortalMaxRecvDataSegLength;
    long	iscsiPortalPrimaryHdrDigest;
    long	iscsiPortalPrimaryDataDigest;
    long	iscsiPortalSecondaryHdrDigest;
    long	iscsiPortalSecondaryDataDigest;
    long	iscsiPortalRecvMarker;
    long	iscsiPortalStorageType;
    struct iscsiPortalAttributes_entry *next;
};

/*
 * Target Portal Attributes Table
 */
void initialize_table_iscsiTgtPortalAttributes(void);
Netsnmp_Node_Handler iscsiTgtPortalAttributes_handler;
Netsnmp_First_Data_Point iscsiTgtPortalAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiTgtPortalAttributes_get_next_data_point;
int iscsiTgtPortalAttributes_load(netsnmp_cache *cache, void *vmagic);
void iscsiTgtPortalAttributes_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSITGTPORTALNODEINDEXORZERO	1
#define COLUMN_ISCSITGTPORTALPORT		2
#define COLUMN_ISCSITGTPORTALTAG		3

/* Data structure for row entry */
struct iscsiTgtPortalAttributes_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiPortalIndex;
    u_long	iscsiTgtPortalNodeIndexOrZero;
    u_long	iscsiTgtPortalPort;
    u_long	iscsiTgtPortalTag;
    struct iscsiTgtPortalAttributes_entry *next;
};

/*
 * Node Attributes Table
 */
void initialize_table_iscsiNodeAttributes(void);
Netsnmp_Node_Handler iscsiNodeAttributes_handler;
Netsnmp_First_Data_Point iscsiNodeAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiNodeAttributes_get_next_data_point;
int iscsiNodeAttributes_load(netsnmp_cache *cache, void *vmagic);
void iscsiNodeAttributes_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSINODEINDEX			1
#define COLUMN_ISCSINODENAME			2
#define COLUMN_ISCSINODEALIAS			3
#define COLUMN_ISCSINODEROLES			4
#define COLUMN_ISCSINODETRANSPORTTYPE		5
#define COLUMN_ISCSINODEINITIALR2T		6
#define COLUMN_ISCSINODEIMMEDIATEDATA		7
#define COLUMN_ISCSINODEMAXOUTSTANDINGR2T	8
#define COLUMN_ISCSINODEFIRSTBURSTLENGTH	9
#define COLUMN_ISCSINODEMAXBURSTLENGTH		10
#define COLUMN_ISCSINODEMAXCONNECTIONS		11
#define COLUMN_ISCSINODEDATASEQUENCEINORDER	12
#define COLUMN_ISCSINODEDATAPDUINORDER		13
#define COLUMN_ISCSINODEDEFAULTTIME2WAIT	14
#define COLUMN_ISCSINODEDEFAULTTIME2RETAIN	15
#define COLUMN_ISCSINODEERRORRECOVERYLEVEL	16
#define COLUMN_ISCSINODEDISCONTINUITYTIME	17
#define COLUMN_ISCSINODESTORAGETYPE		18

/* Data structure for row entry */
struct iscsiNodeAttributes_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiNodeIndex;
    char	iscsiNodeName[ISCSI_MAX_NAME_LEN];
    char	iscsiNodeAlias[ISCSI_MAX_ALIAS_LEN];
    char	iscsiNodeRoles;
    oid		iscsiNodeTransportType[MAX_OID_LEN];
    int		iscsiNodeTransportType_len;
    long	iscsiNodeInitialR2T;
    long	iscsiNodeImmediateData;
    u_long	iscsiNodeMaxOutstandingR2T;
    u_long	iscsiNodeFirstBurstLength;
    u_long	iscsiNodeMaxBurstLength;
    u_long	iscsiNodeMaxConnections;
    long	iscsiNodeDataSequenceInOrder;
    long	iscsiNodeDataPDUInOrder;
    u_long	iscsiNodeDefaultTime2Wait;
    u_long	iscsiNodeDefaultTime2Retain;
    u_long	iscsiNodeErrorRecoveryLevel;
    u_long	iscsiNodeDiscontinuityTime;
    long	iscsiNodeStorageType;
    struct iscsiNodeAttributes_entry *next;
};

/*
 * Target Attributes Table and Target Login Failure Notification
 */
void initialize_iscsiTargetAttributes(void);
void initialize_table_iscsiTargetAttributes(void);
Netsnmp_Node_Handler iscsiTargetAttributes_handler;
Netsnmp_First_Data_Point iscsiTargetAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiTargetAttributes_get_next_data_point;
void iscsiTargetAttributes_load(unsigned int clientreg, void *clientarg);
void iscsiTargetAttributes_free(void);

/* column number definitions */
#define COLUMN_ISCSITGTLOGINFAILURES		1
#define COLUMN_ISCSITGTLASTFAILURETIME		2
#define COLUMN_ISCSITGTLASTFAILURETYPE		3
#define COLUMN_ISCSITGTLASTINTRFAILURENAME	4
#define COLUMN_ISCSITGTLASTINTRFAILUREADDRTYPE	5
#define COLUMN_ISCSITGTLASTINTRFAILUREADDR	6

/* Data structure for row entry */
struct iscsiTargetAttributes_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiNodeIndex;
    u_long	iscsiTgtLoginFailures;
    u_long	iscsiTgtLastFailureTime;
    oid		iscsiTgtLastFailureType[MAX_OID_LEN];
    int		iscsiTgtLastFailureType_len;
    char	iscsiTgtLastIntrFailureName[ISCSI_MAX_NAME_LEN];
    long	iscsiTgtLastIntrFailureAddrType;
    char	iscsiTgtLastIntrFailureAddr[16];
    struct iscsiTargetAttributes_entry *next;
};

/*
 * Target Login Stats Table
 */
void initialize_table_iscsiTgtLoginStats(void);
Netsnmp_Node_Handler iscsiTgtLoginStats_handler;
Netsnmp_First_Data_Point iscsiTgtLoginStats_get_first_data_point;
Netsnmp_Next_Data_Point iscsiTgtLoginStats_get_next_data_point;
int iscsiTgtLoginStats_load(netsnmp_cache *cache, void *vmagic);
void iscsiTgtLoginStats_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSITGTLOGINACCEPTS		1
#define COLUMN_ISCSITGTLOGINOTHERFAILS		2
#define COLUMN_ISCSITGTLOGINREDIRECTS		3
#define COLUMN_ISCSITGTLOGINAUTHORIZEFAILS	4
#define COLUMN_ISCSITGTLOGINAUTHENTICATEFAILS	5
#define COLUMN_ISCSITGTLOGINNEGOTIATEFAILS	6

/* Data structure for row entry */
struct iscsiTgtLoginStats_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiNodeIndex;
    u_long	iscsiTgtLoginAccepts;
    u_long	iscsiTgtLoginOtherFails;
    u_long	iscsiTgtLoginRedirects;
    u_long	iscsiTgtLoginAuthorizeFails;
    u_long	iscsiTgtLoginAuthenticateFails;
    u_long	iscsiTgtLoginNegotiateFails;
    struct iscsiTgtLoginStats_entry *next;
};

/*
 * Target Logout Stats Table
 */
void initialize_table_iscsiTgtLogoutStats(void);
Netsnmp_Node_Handler iscsiTgtLogoutStats_handler;
Netsnmp_First_Data_Point iscsiTgtLogoutStats_get_first_data_point;
Netsnmp_Next_Data_Point iscsiTgtLogoutStats_get_next_data_point;
int iscsiTgtLogoutStats_load(netsnmp_cache *cache, void *vmagic);
void iscsiTgtLogoutStats_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSITGTLOGOUTNORMALS		1
#define COLUMN_ISCSITGTLOGOUTOTHERS		2

/* Data structure for row entry */
struct iscsiTgtLogoutStats_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiNodeIndex;
    u_long	iscsiTgtLogoutNormals;
    u_long	iscsiTgtLogoutOthers;
    struct iscsiTgtLogoutStats_entry *next;
};

/*
 * Target Authorization Attributes Table
 */
void initialize_table_iscsiTgtAuthAttributes(void);
Netsnmp_Node_Handler iscsiTgtAuthAttributes_handler;
Netsnmp_First_Data_Point iscsiTgtAuthAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiTgtAuthAttributes_get_next_data_point;
int iscsiTgtAuthAttributes_load(netsnmp_cache *cache, void *vmagic);
void iscsiTgtAuthAttributes_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSITGTAUTHINDEX	1
#define COLUMN_ISCSITGTAUTHROWSTATUS	2
#define COLUMN_ISCSITGTAUTHIDENTITY	3
#define COLUMN_ISCSITGTAUTHSTORAGETYPE	4

/* Data structure for row entry */
struct iscsiTgtAuthAttributes_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiNodeIndex;
    u_long	iscsiTgtAuthIndex;
    long	iscsiTgtAuthRowStatus;
    oid		iscsiTgtAuthIdentity[MAX_OID_LEN];
    int		iscsiTgtAuthIdentity_len;
    long	iscsiTgtAuthStorageType;
    struct iscsiTgtAuthAttributes_entry *next;
};

/*
 * Session Attributes Table
 */
void initialize_table_iscsiSessionAttributes(void);
Netsnmp_Node_Handler iscsiSessionAttributes_handler;
Netsnmp_First_Data_Point iscsiSessionAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiSessionAttributes_get_next_data_point;
int iscsiSessionAttributes_load(netsnmp_cache *cache, void *vmagic);
void iscsiSessionAttributes_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSISSNNODEINDEX		1
#define COLUMN_ISCSISSNINDEX			2
#define COLUMN_ISCSISSNDIRECTION		3
#define COLUMN_ISCSISSNINITIATORNAME		4
#define COLUMN_ISCSISSNTARGETNAME		5
#define COLUMN_ISCSISSNTSIH			6
#define COLUMN_ISCSISSNISID			7
#define COLUMN_ISCSISSNINITIATORALIAS		8
#define COLUMN_ISCSISSNTARGETALIAS		9
#define COLUMN_ISCSISSNINITIALR2T		10
#define COLUMN_ISCSISSNIMMEDIATEDATA		11
#define COLUMN_ISCSISSNTYPE			12
#define COLUMN_ISCSISSNMAXOUTSTANDINGR2T	13
#define COLUMN_ISCSISSNFIRSTBURSTLENGTH		14
#define COLUMN_ISCSISSNMAXBURSTLENGTH		15
#define COLUMN_ISCSISSNCONNECTIONNUMBER		16
#define COLUMN_ISCSISSNAUTHIDENTITY		17
#define COLUMN_ISCSISSNDATASEQUENCEINORDER	18
#define COLUMN_ISCSISSNDATAPDUINORDER		19
#define COLUMN_ISCSISSNERRORRECOVERYLEVEL	20
#define COLUMN_ISCSISSNDISCONTINUITYTIME	21

/* Data structure for row entry */
struct iscsiSessionAttributes_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiSsnNodeIndex;
    u_long	iscsiSsnIndex;
    long	iscsiSsnDirection;
    char	iscsiSsnInitiatorName[ISCSI_MAX_NAME_LEN];
    char	iscsiSsnTargetName[ISCSI_MAX_NAME_LEN];
    u_long	iscsiSsnTSIH;
    char	iscsiSsnISID[6];
    char	iscsiSsnInitiatorAlias[ISCSI_MAX_ALIAS_LEN];
    char	iscsiSsnTargetAlias[ISCSI_MAX_ALIAS_LEN];
    long	iscsiSsnInitialR2T;
    long	iscsiSsnImmediateData;
    long	iscsiSsnType;
    u_long	iscsiSsnMaxOutstandingR2T;
    u_long	iscsiSsnFirstBurstLength;
    u_long	iscsiSsnMaxBurstLength;
    u_long	iscsiSsnConnectionNumber;
    oid		iscsiSsnAuthIdentity[MAX_OID_LEN];
    int		iscsiSsnAuthIdentity_len;
    long	iscsiSsnDataSequenceInOrder;
    long	iscsiSsnDataPDUInOrder;
    u_long	iscsiSsnErrorRecoveryLevel;
    u_long	iscsiSsnDiscontinuityTime;
    struct iscsiSessionAttributes_entry *next;
};

/*
 * Session Stats Table
 */
void initialize_table_iscsiSessionStats(void);
Netsnmp_Node_Handler iscsiSessionStats_handler;
Netsnmp_First_Data_Point iscsiSessionStats_get_first_data_point;
Netsnmp_Next_Data_Point iscsiSessionStats_get_next_data_point;
int iscsiSessionStats_load(netsnmp_cache *cache, void *vmagic);
void iscsiSessionStats_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSISSNCMDPDUS		1
#define COLUMN_ISCSISSNRSPPDUS		2
#define COLUMN_ISCSISSNTXDATAOCTETS	3
#define COLUMN_ISCSISSNRXDATAOCTETS	4
#define COLUMN_ISCSISSNLCTXDATAOCTETS	5
#define COLUMN_ISCSISSNLCRXDATAOCTETS	6

/* Data structure for row entry */
struct iscsiSessionStats_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiSsnNodeIndex;
    u_long	iscsiSsnIndex;
    u_long	iscsiSsnCmdPDUs;
    u_long	iscsiSsnRspPDUs;
    U64		iscsiSsnTxDataOctets;
    U64		iscsiSsnRxDataOctets;
    u_long	iscsiSsnLCTxDataOctets;
    u_long	iscsiSsnLCRxDataOctets;
    struct iscsiSessionStats_entry *next;
};

/*
 * Session Connection Error Stats Table
 */
void initialize_table_iscsiSsnCxnErrStats(void);
Netsnmp_Node_Handler iscsiSsnCxnErrStats_handler;
Netsnmp_First_Data_Point iscsiSsnCxnErrStats_get_first_data_point;
Netsnmp_Next_Data_Point iscsiSsnCxnErrStats_get_next_data_point;
int iscsiSsnCxnErrStats_load(netsnmp_cache *cache, void *vmagic);
void iscsiSsnCxnErrStats_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSISSNCXNDIGESTERRORS		1
#define COLUMN_ISCSISSNCXNTIMEOUTERRORS		2

/* Data structure for row entry */
struct iscsiSsnCxnErrStats_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiSsnNodeIndex;
    u_long	iscsiSsnIndex;
    u_long	iscsiSsnCxnDigestErrors;
    u_long	iscsiSsnCxnTimeoutErrors;
    struct iscsiSsnCxnErrStats_entry *next;
};

/*
 * Connection Attributes Table
 */
void initialize_table_iscsiCxnAttributes(void);
Netsnmp_Node_Handler iscsiCxnAttributes_handler;
Netsnmp_First_Data_Point iscsiCxnAttributes_get_first_data_point;
Netsnmp_Next_Data_Point iscsiCxnAttributes_get_next_data_point;
int iscsiCxnAttributes_load(netsnmp_cache *cache, void *vmagic);
void iscsiCxnAttributes_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions */
#define COLUMN_ISCSICXNINDEX			1
#define COLUMN_ISCSICXNCID			2
#define COLUMN_ISCSICXNSTATE			3
#define COLUMN_ISCSICXNADDRTYPE			4
#define COLUMN_ISCSICXNLOCALADDR		5
#define COLUMN_ISCSICXNPROTOCOL			6
#define COLUMN_ISCSICXNLOCALPORT		7
#define COLUMN_ISCSICXNREMOTEADDR		8
#define COLUMN_ISCSICXNREMOTEPORT		9
#define COLUMN_ISCSICXNMAXRECVDATASEGLENGTH	10
#define COLUMN_ISCSICXNMAXXMITDATASEGLENGTH	11
#define COLUMN_ISCSICXNHEADERINTEGRITY		12
#define COLUMN_ISCSICXNDATAINTEGRITY		13
#define COLUMN_ISCSICXNRECVMARKER		14
#define COLUMN_ISCSICXNSENDMARKER		15
#define COLUMN_ISCSICXNVERSIONACTIVE		16

/* Data structure for row entry */
struct iscsiCxnAttributes_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiSsnNodeIndex;
    u_long	iscsiSsnIndex;
    u_long	iscsiCxnIndex;
    u_long	iscsiCxnCid;
    long	iscsiCxnState;
    long	iscsiCxnAddrType;
    char	iscsiCxnLocalAddr[16];
    u_long	iscsiCxnProtocol;
    u_long	iscsiCxnLocalPort;
    char	iscsiCxnRemoteAddr[16];
    u_long	iscsiCxnRemotePort;
    u_long	iscsiCxnMaxRecvDataSegLength;
    u_long	iscsiCxnMaxXmitDataSegLength;
    long	iscsiCxnHeaderIntegrity;
    long	iscsiCxnDataIntegrity;
    long	iscsiCxnRecvMarker;
    long	iscsiCxnSendMarker;
    u_long	iscsiCxnVersionActive;
    struct iscsiCxnAttributes_entry *next;
};

/*
 * Session Failure Notification
 */
void initialize_iscsiInstSessionFailure(void);

struct iscsiInstSessionFailure_entry {
    u_long	iscsiInstIndex;
    u_long	iscsiInstSsnFailures;
    oid		iscsiInstLastSsnFailureType[MAX_OID_LEN];
    int		iscsiInstLastSsnFailureType_len;
    char	iscsiInstLastSsnRmtNodeName[ISCSI_MAX_NAME_LEN];
};

#endif /* ISCSIMIB_H */
