
ISCSI_NAME           = iscsi-name
ISCSI_NAME_SRCS      = iscsi_name.c md5.c
ISCSI_NAME_OBJS      = $(ISCSI_NAME_SRCS:.c=.o)

all:: $(ISCSI_NAME) 

$(ISCSI_NAME): $(ISCSI_NAME_OBJS)
	$(CC) -o $@ $(CFLAGS) $(ISCSI_NAME_OBJS) 

clean:
	rm -f $(ISCSI_NAME_OBJS) $(ISCSI_NAME) 

install:
	install -m 0755 $(ISCSI_NAME)     $(DESTDIR)/usr/sbin/iscsi-name
