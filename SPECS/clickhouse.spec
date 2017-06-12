%define clickhouse_user clickhouse
%define clickhouse_group clickhouse

%global commit             96485e41c5b1d65fa2fbf016523f5e1fb37d3ffd
%global shortcommit        %(c=%{commit}; echo ${c:0:7})

Name:           clickhouse
Version:        1.1.54236
Release:        1%{?dist}
Summary:        A free analytic DBMS for big data
Group:          Applications/Databases
License:        Apache-2.0
URL:            https://clickhouse.yandex/
Source0:        https://github.com/yandex/ClickHouse/archive/%{commit}.tar.gz#/ClickHouse-%{commit}.tar.gz

%if 0%{?rhel}  == 7
Source1:        clickhouse.service
Source2:        clickhouse.tmpfilesd
Source3:        logrotate

BuildRequires:  cmake
BuildRequires:  devtoolset-6-gcc-c++
BuildRequires:  libicu-devel
BuildRequires:  libtool-ltdl-devel
BuildRequires:  unixODBC-devel
BuildRequires:  openssl-devel
BuildRequires:  readline-devel
BuildRequires:  mariadb-devel
BuildRequires:  libzstd-devel
BuildRequires:  expat-devel
BuildRequires:  re2-devel
BuildRequires:  zlib-devel
%endif

%description
ClickHouse is an open source column-oriented database management system capable
of real time generation of analytical data reports using SQL queries.

%package     common
Summary:     clickhouse common files
Requires:    %{name} = %{version}-%{release}

%description common
%{summary}.

%package     server
Summary:     clickhouse server files
Requires:    %{name} = %{version}-%{release}
%if 0%{?rhel}  == 7
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif

%description server
%{summary}.

%package     client
Summary:     clickhouse client files
Requires:    %{name} = %{version}-%{release}

%description client
%{summary}.

%prep
%setup -q -n ClickHouse-%{commit}

%build
%if 0%{?rhel}  == 7
%{__cat} <<EOF | scl enable devtoolset-6 -
%{__mkdir} build
cd build
cmake .. \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DUSE_STATIC_LIBRARIES=0 \
  -DENABLE_JEMALLOC=1 \
  -DUSE_INTERNAL_POCO_LIBRARY=0 \
  -DUSE_INTERNAL_RE2_LIBRARY=0 \
  -DUSE_INTERNAL_ZSTD_LIBRARY=0 \
  -DUSE_INTERNAL_ZLIB_LIBRARY=0 \
  -DENABLE_TESTS=0
%{__make} %{?_smp_mflags}
EOF
%endif

%install
%{__rm} -rf %{buildroot}
cd build
%{__make} DESTDIR=%{buildroot} install
# NOTE: We don't need this file since poco library are static linked to clickhouse,
# so we delete it to avoid file collision with other rpm packages.
%{__rm} -rf %{buildroot}/usr/lib/cmake/Poco/PocoConfig.cmake

%if 0%{?rhel}  == 7
%{__mkdir} -p %{buildroot}%{_localstatedir}/log/clickhouse-server
%{__mkdir} -p %{buildroot}%{_localstatedir}/lib/clickhouse-server/tmp
%{__mkdir} -p %{buildroot}%{_localstatedir}/run/clickhouse-server
%{__install} -D -m 0644 -p %{SOURCE1} \
   %{buildroot}%{_unitdir}/clickhouse.service
%{__install} -D -m 0644 -p %{SOURCE2} \
   %{buildroot}%{_sysconfdir}/tmpfiles.d/clickhouse.conf
%{__mkdir} -p %{buildroot}%{_sysconfdir}/logrotate.d
%{__install} -m 644 -p %{SOURCE3} \
    %{buildroot}%{_sysconfdir}/logrotate.d/clickhouse-server
%endif

%clean
%{__rm} -rf %{buildroot}

%pre
# Add the "clickhouse" user
getent group %{clickhouse_group} >/dev/null || groupadd -r %{clickhouse_group}
getent passwd %{clickhouse_user} >/dev/null || \
    useradd -r -g %{clickhouse_group} -s /sbin/nologin \
    --no-create-home -c "clickhouse user"  %{clickhouse_user}
exit 0

%post
%if 0%{?rhel}  == 7
%systemd_post clickhouse.service
%endif

%preun
%if 0%{?rhel}  == 7
%systemd_preun clickhouse.service
%endif

%postun
%if 0%{?rhel}  == 7
%systemd_postun_with_restart clickhouse.service
%endif


%files common
%defattr(-,root,root,-)
%{_bindir}/clickhouse
%{_bindir}/config-processor
%{_libdir}/libclickhouse.so*

%files server
%defattr(-,root,root,-)
%{_bindir}/clickhouse-benchmark
%{_bindir}/clickhouse-compressor
%{_bindir}/clickhouse-local
%{_bindir}/clickhouse-server
%{_bindir}/clickhouse-zookeeper-cli
%{_bindir}/corrector_utf8
%if 0%{?rhel}  == 7
%config(noreplace) %{_sysconfdir}/%{name}-server/config.xml
%config(noreplace) %{_sysconfdir}/%{name}-server/users.xml
%{_unitdir}/clickhouse.service
%{_sysconfdir}/tmpfiles.d/clickhouse.conf
%attr(0755, %{clickhouse_user}, %{clickhouse_group}) %dir %{_localstatedir}/lib/%{name}-server
%attr(0755, %{clickhouse_user}, %{clickhouse_group}) %dir %{_localstatedir}/lib/%{name}-server/tmp
%attr(0755, %{clickhouse_user}, %{clickhouse_group}) %dir %{_localstatedir}/log/%{name}-server
%attr(0755, %{clickhouse_user}, %{clickhouse_group}) %dir %{_localstatedir}/run/%{name}-server
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-server
%endif

%files client
%defattr(-,root,root,-)
%{_bindir}/clickhouse-client
%config(noreplace) %{_sysconfdir}/%{name}-client/config.xml


%changelog
* Mon Jun 12 2017 Hiroaki Nakamura <hnakamur@gmail.com> - 1.1.54236-1
- Initial packaging
