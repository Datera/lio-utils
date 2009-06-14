/*
 * Copyright (c) 2006 SBE, Inc.
 */
#ifndef SCSIMIB_H
#define SCSIMIB_H

#define SCSI_MAX_NAME_LEN	262

#define SCSI_ROLE_TARGET	(1 << 7)
#define SCSI_ROLE_INITIATOR	(1 << 6)

#define SCSI_TRANSPORT_INDEX		1

/* Device status */
#define SCSI_DEV_STATUS_UNKNOWN			1
#define SCSI_DEV_STATUS_AVAILABLE		2
#define SCSI_DEV_STATUS_BROKEN			3
#define SCSI_DEV_STATUS_READYING		4
#define SCSI_DEV_STATUS_ABNORMAL		5
#define SCSI_DEV_STATUS_NONADDRFAILURE		6
#define SCSI_DEV_STATUS_NONADDRFAILREADYING	7
#define SCSI_DEV_STATUS_NONADDRFAILABNORMAL	8

/* LU status */
#define SCSI_LU_STATUS_UNKNOWN		1
#define SCSI_LU_STATUS_AVAILABLE	2
#define SCSI_LU_STATUS_NOTAVAILABLE	3
#define SCSI_LU_STATUS_BROKEN		4
#define SCSI_LU_STATUS_READYING		5
#define SCSI_LU_STATUS_ABNORMAL		6

/* LU state bit  */
#define SCSI_LU_STATE_DATALOST			0
#define SCSI_LU_STATE_DYNAMICREGONFIG		1
#define SCSI_LU_STATE_EXPOSED			2
#define SCSI_LU_STATE_FRACTIONALLYEXPOSED	3
#define SCSI_LU_STATE_PARTIALLYEXPOSED		4
#define SCSI_LU_STATE_PROTECTEDREBUILD		5
#define SCSI_LU_STATE_PROTECTIONDISABLED	6
#define SCSI_LU_STATE_REBUILD			7
#define SCSI_LU_STATE_RECALCULATE		8
#define SCSI_LU_STATE_SPARCEINUSE		9
#define SCSI_LU_STATE_VERIFYINPROGRESS		10

/*
 * Instance Table
 */
void initialize_table_scsiInstanceTable(void);
Netsnmp_Node_Handler scsiInstanceTable_handler;
Netsnmp_First_Data_Point scsiInstanceTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiInstanceTable_get_next_data_point;
int scsiInstanceTable_load(netsnmp_cache *cache, void *vmagic);
void scsiInstanceTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiInstanceTable */
#define COLUMN_SCSIINSTINDEX			1
#define COLUMN_SCSIINSTALIAS			2
#define COLUMN_SCSIINSTSOFTWAREINDEX		3
#define COLUMN_SCSIINSTVENDORVERSION		4
#define COLUMN_SCSIINSTSCSINOTIFICATIONSENABLE	5
#define COLUMN_SCSIINSTSTORAGETYPE		6

/* Data structure for row entry */
struct scsiInstanceTable_entry {
    u_long	scsiInstIndex;
    char	scsiInstAlias[80];
    char	old_scsiInstAlias[80];
    long	scsiInstSoftwareIndex;
    char	scsiInstVendorVersion[80];
    long	scsiInstScsiNotificationsEnable;
    long	scsiInstStorageType;
    struct scsiInstanceTable_entry *next;
};

/*
 * Device Table
 */
void initialize_table_scsiDeviceTable(void);
Netsnmp_Node_Handler scsiDeviceTable_handler;
Netsnmp_First_Data_Point scsiDeviceTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiDeviceTable_get_next_data_point;
int scsiDeviceTable_load(netsnmp_cache *cache, void *vmagic);
void scsiDeviceTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiDeviceTable */
#define COLUMN_SCSIDEVICEINDEX		1
#define COLUMN_SCSIDEVICEALIAS		2
#define COLUMN_SCSIDEVICEROLE		3
#define COLUMN_SCSIDEVICEPORTNUMBER	4

/* Data structure for row entry */
struct scsiDeviceTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    char	scsiDeviceAlias[80];
    char	scsiDeviceRole;
    u_long	scsiDevicePortNumber;
    struct scsiDeviceTable_entry *next;
};

/* 
 * Port Table
 */
void initialize_table_scsiPortTable(void);
Netsnmp_Node_Handler scsiPortTable_handler;
Netsnmp_First_Data_Point scsiPortTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiPortTable_get_next_data_point;
int scsiPortTable_load(netsnmp_cache *cache, void *vmagic);
void scsiPortTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiPortTable */
#define COLUMN_SCSIPORTINDEX		1
#define COLUMN_SCSIPORTROLE		2
#define COLUMN_SCSIPORTTRANSPORTPTR	3
#define COLUMN_SCSIPORTBUSYSTATUSES	4

/* Data structure for row entry */
struct scsiPortTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    u_long	scsiPortIndex;
    u_char	scsiPortRole;
    oid		scsiPortTransportPtr[MAX_OID_LEN];
    int		scsiPortTransportPtr_len;
    u_long	scsiPortBusyStatuses;
    struct scsiPortTable_entry *next;
};

/*
 * Transport Table
 */
void initialize_table_scsiTransportTable(void);
Netsnmp_Node_Handler scsiTransportTable_handler;
Netsnmp_First_Data_Point scsiTransportTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiTransportTable_get_next_data_point;
int scsiTransportTable_load(netsnmp_cache *cache, void *vmagic);
void scsiTransportTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiTransportTable */
#define COLUMN_SCSITRANSPORTINDEX	1
#define COLUMN_SCSITRANSPORTTYPE	2
#define COLUMN_SCSITRANSPORTPOINTER	3
#define COLUMN_SCSITRANSPORTDEVNAME	4

/* Data structure for row entry */
struct scsiTransportTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    u_long	scsiTransportIndex;
    oid		scsiTransportType[MAX_OID_LEN];
    int		scsiTransportType_len;
    oid		scsiTransportPointer[MAX_OID_LEN];
    int		scsiTransportPointer_len;
    char	scsiTransportDevName[SCSI_MAX_NAME_LEN];
    struct scsiTransportTable_entry *next;
};

/*
 * Target Device Table
 */
void initialize_scsiTgtDevTable(void);
void initialize_table_scsiTgtDevTable(void);
Netsnmp_Node_Handler scsiTgtDevTable_handler;
Netsnmp_First_Data_Point scsiTgtDevTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiTgtDevTable_get_next_data_point;
void scsiTgtDevTable_load(unsigned int clientreg, void *clientarg);

/* column number definitions for table scsiTgtDevTable */
#define COLUMN_SCSITGTDEVNUMBEROFLUS		1
#define COLUMN_SCSITGTDEVICESTATUS		2
#define COLUMN_SCSITGTDEVNONACCESSIBLELUS	3
#define COLUMN_SCSITGTDEVRESETS			4

/* Data structure for row entry */
struct scsiTgtDevTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    u_long	scsiTgtDevNumberOfLUs;
    long	scsiTgtDeviceStatus;
    u_long	scsiTgtDevNonAccessibleLUs;
    u_long	scsiTgtDevResets;
    struct scsiTgtDevTable_entry *next;
};

/*
 * Target Port Table
 */
void initialize_table_scsiTgtPortTable(void);
Netsnmp_Node_Handler scsiTgtPortTable_handler;
Netsnmp_First_Data_Point scsiTgtPortTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiTgtPortTable_get_next_data_point;
int scsiTgtPortTable_load(netsnmp_cache *cache, void *vmagic);
void scsiTgtPortTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiTgtPortTable */
#define COLUMN_SCSITGTPORTNAME			1
#define COLUMN_SCSITGTPORTIDENTIFIER		2
#define COLUMN_SCSITGTPORTINCOMMANDS		3
#define COLUMN_SCSITGTPORTWRITTENMEGABYTES	4
#define COLUMN_SCSITGTPORTREADMEGABYTES		5
#define COLUMN_SCSITGTPORTHSINCOMMANDS		6

/* Data structure for row entry */
struct scsiTgtPortTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    u_long	scsiPortIndex;
    char	scsiTgtPortName[SCSI_MAX_NAME_LEN];
    char	scsiTgtPortIdentifier[SCSI_MAX_NAME_LEN];
    u_long	scsiTgtPortInCommands;
    u_long	scsiTgtPortWrittenMegaBytes;
    u_long	scsiTgtPortReadMegaBytes;
    U64		scsiTgtPortHSInCommands;
    struct scsiTgtPortTable_entry *next;
};

/*
 * Authorized Initiator Table
 */
void initialize_table_scsiAuthorizedIntrTable(void);
Netsnmp_Node_Handler scsiAuthorizedIntrTable_handler;
Netsnmp_First_Data_Point scsiAuthorizedIntrTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiAuthorizedIntrTable_get_next_data_point;
int scsiAuthorizedIntrTable_load(netsnmp_cache *cache, void *vmagic);
void scsiAuthorizedIntrTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiAuthorizedIntrTable */
#define COLUMN_SCSIAUTHINTRTGTPORTINDEX		1
#define COLUMN_SCSIAUTHINTRINDEX		2
#define COLUMN_SCSIAUTHINTRDEVORPORT		3
#define COLUMN_SCSIAUTHINTRNAME			4
#define COLUMN_SCSIAUTHINTRLUNMAPINDEX		5
#define COLUMN_SCSIAUTHINTRATTACHEDTIMES	6
#define COLUMN_SCSIAUTHINTROUTCOMMANDS		7
#define COLUMN_SCSIAUTHINTRREADMEGABYTES	8
#define COLUMN_SCSIAUTHINTRWRITTENMEGABYTES	9
#define COLUMN_SCSIAUTHINTRHSOUTCOMMANDS	10
#define COLUMN_SCSIAUTHINTRLASTCREATION		11
#define COLUMN_SCSIAUTHINTRROWSTATUS		12

/* Data structure for row entry */
struct scsiAuthorizedIntrTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    u_long	scsiAuthIntrTgtPortIndex;
    u_long	scsiAuthIntrIndex;
    long	scsiAuthIntrDevOrPort;
    char	scsiAuthIntrName[SCSI_MAX_NAME_LEN];
    u_long	scsiAuthIntrLunMapIndex;
    u_long	scsiAuthIntrAttachedTimes;
    u_long	scsiAuthIntrOutCommands;
    u_long	scsiAuthIntrReadMegaBytes;
    u_long	scsiAuthIntrWrittenMegaBytes;
    U64		scsiAuthIntrHSOutCommands;
    u_long	scsiAuthIntrLastCreation;
    long	scsiAuthIntrRowStatus;
    struct scsiAuthorizedIntrTable_entry *next;
};

/*
 * Attached Initiator Port Table
 */
void initialize_table_scsiAttIntrPortTable(void);
Netsnmp_Node_Handler scsiAttIntrPortTable_handler;
Netsnmp_First_Data_Point scsiAttIntrPortTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiAttIntrPortTable_get_next_data_point;
int scsiAttIntrPortTable_load(netsnmp_cache *cache, void *vmagic);
void scsiAttIntrPortTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiAttIntrPortTable */
#define COLUMN_SCSIATTINTRPORTINDEX		1
#define COLUMN_SCSIATTINTRPORTAUTHINTRIDX	2
#define COLUMN_SCSIATTINTRPORTNAME		3
#define COLUMN_SCSIATTINTRPORTIDENTIFIER	4

/* Data structure for row entry */
struct scsiAttIntrPortTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    u_long	scsiPortIndex;
    u_long	scsiAttIntrPortIndex;
    u_long	scsiAttIntrPortAuthIntrIdx;
    char	scsiAttIntrPortName[SCSI_MAX_NAME_LEN];
    char	scsiAttIntrPortIdentifier[SCSI_MAX_NAME_LEN];
    struct scsiAttIntrPortTable_entry *next;
};

/*
 * Logical Unit Table
 */
void initialize_table_scsiLuTable(void);
Netsnmp_Node_Handler scsiLuTable_handler;
Netsnmp_First_Data_Point scsiLuTable_get_first_data_point;
Netsnmp_Next_Data_Point scsiLuTable_get_next_data_point;
int scsiLuTable_load(netsnmp_cache *cache, void *vmagic);
void scsiLuTable_free(netsnmp_cache *cache, void *vmagic);

/* column number definitions for table scsiLuTable */
#define COLUMN_SCSILUINDEX			1
#define COLUMN_SCSILUDEFAULTLUN			2
#define COLUMN_SCSILUWWNNAME			3
#define COLUMN_SCSILUVENDORID			4
#define COLUMN_SCSILUPRODUCTID			5
#define COLUMN_SCSILUREVISIONID			6
#define COLUMN_SCSILUPERIPHERALTYPE		7
#define COLUMN_SCSILUSTATUS			8
#define COLUMN_SCSILUSTATE			9
#define COLUMN_SCSILUINCOMMANDS			10
#define COLUMN_SCSILUREADMEGABYTES		11
#define COLUMN_SCSILUWRITTENMEGABYTES		12
#define COLUMN_SCSILUINRESETS			13
#define COLUMN_SCSILUOUTTASKSETFULLSTATUS	14
#define COLUMN_SCSILUHSINCOMMANDS		15
#define COLUMN_SCSILULASTCREATION		16

/* Data structure for row entry */
struct scsiLuTable_entry {
    u_long	scsiInstIndex;
    u_long	scsiDeviceIndex;
    u_long	scsiLuIndex;
    u_char	scsiLuDefaultLun[8];
    char	scsiLuWwnName[12];
    char	scsiLuVendorId[32];
    char	scsiLuProductId[32];
    char	scsiLuRevisionId[16];
    u_long	scsiLuPeripheralType;
    long	scsiLuStatus;
    char	scsiLuState[2];
    u_long	scsiLuInCommands;
    u_long	scsiLuReadMegaBytes;
    u_long	scsiLuWrittenMegaBytes;
    u_long	scsiLuInResets;
    u_long	scsiLuOutTaskSetFullStatus;
    U64		scsiLuHSInCommands;
    u_long	scsiLuLastCreation;
    struct scsiLuTable_entry *next;
};

#endif /* SCSIMIB_H */
