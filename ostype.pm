sub ostype
{

    my $root = shift @_;
    
    my $keyfile = "$root/etc/issue";
    my $txt=`cat $keyfile`;
    my $rval;
    

    $rval->{ARCH}="$ENV{'ARCH'}";
    $rval->{RELEASE}="$ENV{'RELEASE'}";
    if (($root ne "") && ($root ne "/")) {
	my $atxt = $txt;
	$atxt =~ s/\n/ /g;
	$rval->{ARCH} = $1 if (($rval->{ARCH} eq "") && (lc ($atxt) =~ /arch (\w+)/));
	$rval->{RELEASE} = $1 if (($rval->{RELEASE} eq "") && (lc ($atxt) =~ /release ([\w.]+)/));
    }
    if ($rval->{RELEASE} eq "")
    {
	$rval->{RELEASE} = `uname -r`;
	$rval->{RELEASE} =~ s/\n+//g;
    }
    
    foreach my $key (glob("$root/lib/modules/*/kernel/arch/*"))
    {
	$key =~ s/^$root\/lib\/modules\///;
	
	my($release,$kernel,$archword,$arch) = split (/\//, $key);

	push @{$rval->{RELEASES}}, $release;
    }

    if ($rval->{ARCH} eq "")
    {
	my $kname = `uname -m`;
	my $uname = `file $root/bin/ls`;
	$uname =~ s/\n+//g;

	$rval->{ARCH}="x86_64" if ($uname =~ /64.*(AMD|Intel|x86-64)/);
	$rval->{ARCH}="i386" if ($uname =~ /32.*(AMD|Intel)/);
	$rval->{ARCH}="ppc" if ($uname =~ /32.*(PowerPC)/ &&
				!$kname =~ /ppc64/);
	$rval->{ARCH}="powerpc" if ($uname =~ /64.*(PowerPC)/ ||
				 $kname =~ /ppc64/);
	$rval->{ARCH}="alpha" if ($uname =~ /64.*(Alpha)/);
    }
    if ($rval->{ARCH} eq "")
    {
	die "Unknown architecture: could not continue --- $uname";
    }

    $rval->{LIBL}="ia32" if ($rval->{ARCH} eq "i386");
    $rval->{LIBL}="x86_64" if ($rval->{ARCH} eq "x86_64");
    

    $rval->{KERNEL} = "24" if ($rval->{RELEASE} =~ /2\.4/);
    $rval->{KERNEL} = "26" if ($rval->{RELEASE} =~ /2\.6/);
    
    if (lc($txt) =~/red.*hat.*release\s+(\w+)\s+\(\w+\s+update\s+(\w+)/ ||
	lc($txt) =~/red.*hat.*release\s+(\w+)/)
    {
	$rval->{DISTRO}="REDHAT";
	$rval->{SYSTEM}="RedHat-R$1";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_SOURCE_DIR}="$rval->{KERNEL_DIR}";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_DIR}/include";
	$rval->{OSTYPE}="LINUX";
	
	if ("$2" eq "")
	{
	    $rval->{SYSTEM}.="-Gold";
	}
	else
	{
	    $rval->{SYSTEM}.="-Update-\u$2";
	}
	$rval->{RPM_DIR}="/usr/src/redhat";
    }
    elsif (lc($txt) =~/suse.*enterprise.*server\s+(\w+) / ||
	   lc($txt) =~/suse/)
    {
	my $release = $1;
	my ($kernel) = glob("$root/lib/modules/*-{default,smp,desktop}");

	$kernel = basename($kernel);
	$kernel =~ s/-(default|smp|desktop)$//;

	unless ($ENV{'KERNEL'} eq "")
	{
	    $kernel = $ENV{'KERNEL'};
	}
	
	if (lc($txt) =~/opensuse/) {
		$rval->{SYSTEM}="OPENSUSE$release-$kernel";	
	} else {
		$rval->{SYSTEM}="SLES$release-$kernel";
	}
	$rval->{RPM_DIR}="/usr/src/packages";
	$rval->{DISTRO}="SUSE";
	$rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
        $rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
	
    }
    elsif (lc($txt) =~/centos.*release\s+(\d+)\.(\d+)\s+\((\w+)/)
    {
	$rval->{SYSTEM}="CentOS-R$1.$2-\u$3";
	$rval->{RPM_DIR}="/usr/src/redhat";
	$rval->{DISTRO}="CENTOS";
	$rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
        $rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/source";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
	
    }
    elsif (lc($txt) =~/centos.*release\s+(\d+)\s+\((\w+)/)
    {
	$rval->{SYSTEM}="CentOS-R$1-$2";
	$rval->{RPM_DIR}="/usr/src/redhat";
	$rval->{DISTRO}="CENTOS";
	$rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/source";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
    }
    elsif (lc($txt) =~/fedora.*(?:core)?.*release\s+(\w+)\s+\((\w+)/)
    {
	$rval->{SYSTEM}="FedoraCore-R$1-\u$2";
	$rval->{RPM_DIR}="/usr/src/redhat";
	$rval->{DISTRO}="FEDORA";
        $rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
        $rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/source";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
	
    }
    elsif ( -e "$root/etc/make.profile")
    {
	$rval->{DISTRO}="GENTOO";
	$rval->{RPM_DIR}="/usr/src/redhat";
	$rval->{OSTYPE}="LINUX";
	
	my $link = readlink("$root/etc/make.profile");
	
	if ($link =~ /.*?([\w\.]+)$/)
	{
	    $rval->{SYSTEM} = "Gentoo-$1";
	}
	$rval->{KERNEL_DIR}="$root/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_SOURCE_DIR}="$rval->{KERNEL_DIR}";
        $rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_DIR}/include";
    }
    elsif (lc($txt) =~/debian/)
    {
    	$rval->{DISTRO}="DEBIAN";
	$rval->{RPM_DIR}="/usr/src/redhat";
	$rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
    }
    elsif (lc($txt) =~ /ubuntu/)
    {
	$rval->{DISTRO}="UBUNTU";
	$rval->{RPM_DIR}="/usr/src/redhat";
	$rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
    }
    elsif (lc($txt) =~ /mandrake|pelco/)
    {
	$rval->{SYSTEM}="Mandrake-R10.0";
	$rval->{RPM_DIR}="/usr/src/RPM";
	$rval->{DISTRO}="MANDRAKE";
        $rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
        $rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/source";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
    }
    elsif (lc($txt) =~/elinos release (.*)/)
    {
	$rval->{SYSTEM}="ELinos-V$1";
    	$rval->{DISTRO}="ELINOS";
	$rval->{RPM_DIR}="/usr/src/redhat";
	$rval->{OSTYPE}="LINUX";
	$rval->{KERNEL_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_SOURCE_DIR}="/lib/modules/$rval->{RELEASE}/build";
	$rval->{KERNEL_INCLUDE_DIR}="$rval->{KERNEL_SOURCE_DIR}/include";
    	$rval->{NO_RPM}=1;
    }
    else
    {
	die "No distribution found in $txt\n";
    }
	 
    $rval->{KERNEL_VERSION_INFO}=$rval->{OSTYPE} . "_KERNEL_" . $rval->{KERNEL};
    $rval->{BASENAME}="$rval->{SYSTEM}.$rval->{ARCH}";
    
    return $rval;
}

sub report_time
{
    my $prompt = shift @_;
    my $start_time = shift @_;

    my $duration = int(time()) - int($start_time);
    my $seconds = $duration % 60;
    
    $duration /= 60;
    
    my $minutes = $duration % 60;

    $duration /= 60;

    my $hours = $duration % 24;

    $duration /= 24;

    my $days = $duration;

    print $prompt;
    
    print_time ($days, "day") if (int($days) > 0);
    print_time ($hours, "hour") if (int($hours) > 0);
    print_time ($minutes, "minute") if (int($minutes) > 0);
    print_time ($seconds, "second");
    print "\n";
}


sub print_time
{
    my ($amt, $msg) = @_;

    if ($amt == 1) {
	print "$amt $msg ";
    } else {
	print "$amt $msg" ."s ";
    }
}
    


1;
