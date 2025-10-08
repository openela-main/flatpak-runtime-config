# package notes require setting RPM-specific environment variables,
# incompatible with flatpak-builder
%undefine _package_note_flags

Name:           flatpak-runtime-config
Version:        40
Release:        4%{?dist}
Summary:        Configuration files that live inside the flatpak runtime
Source1:        50-flatpak.conf
Source2:        sitecustomize.py
Source3:        defaults.json.in
Source4:        com.redhat.Platform.appdata.xml
Source5:        com.redhat.Sdk.appdata.xml
Source6:        org.centos.stream.Platform.appdata.xml
Source7:        org.centos.stream.Sdk.appdata.xml
Source10:       05-flatpak-fontpath.conf

License:        MIT

BuildRequires:  python3
BuildRequires:  python3-rpm-macros

Requires:       findutils
Requires:       fontpackages-filesystem

%description
This package includes configuration files that are installed into the flatpak
runtime filesystem during the runtime creation process; it is also installed
into the build root when building RPMs. It contains all configuration
files that need to be different when executing a flatpak.

%prep

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_prefix}/cache/fontconfig
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/fonts/conf.d
install -t $RPM_BUILD_ROOT%{_sysconfdir}/fonts/conf.d -p -m 0644 %{SOURCE1}
install -t $RPM_BUILD_ROOT%{_sysconfdir}/fonts/conf.d -p -m 0644 %{SOURCE10}

# usercustomize.py to set up Python paths
for d in %{python3_sitelib} ; do
    mkdir -p $RPM_BUILD_ROOT/$d
    install -t $RPM_BUILD_ROOT/$d -m 0644 %{SOURCE2}
done

# Install appdata for both the Platform and the Sdk
mkdir -p $RPM_BUILD_ROOT%{_datadir}/metainfo
%if 0%{?rhel}
install -t $RPM_BUILD_ROOT%{_datadir}/metainfo -p -m 0644 %{SOURCE4}
install -t $RPM_BUILD_ROOT%{_datadir}/metainfo -p -m 0644 %{SOURCE5}
%endif
%if 0%{?centos}
install -t $RPM_BUILD_ROOT%{_datadir}/metainfo -p -m 0644 %{SOURCE6}
install -t $RPM_BUILD_ROOT%{_datadir}/metainfo -p -m 0644 %{SOURCE7}
%endif

# Install flatpak-builder config file
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/flatpak-builder
sed -e 's|%%{_libdir}|%{_libdir}|' \
    -e 's|%%{_lib}|%{_lib}|' \
    -e 's|%%{build_cflags}|%{build_cflags}|' \
    -e 's|%%{build_cxxflags}|%{build_cxxflags}|' \
    -e 's|%%{build_ldflags}|%{build_ldflags}|' \
    %{SOURCE3} > $RPM_BUILD_ROOT%{_sysconfdir}/flatpak-builder/defaults.json

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/ld.so.conf.d/
echo "/app/%{_lib}" > $RPM_BUILD_ROOT%{_sysconfdir}/ld.so.conf.d/app.conf

# We duplicate selected file triggers from packages in the runtime, to
# extend them to cover /app as well. Some other functions that RPM file
# triggers normally provide are handled by flatpak triggers - in particular
# calling update-desktop-database and gtk-update-icon-cache.

# The ldconfig scriplets have a limited function since symlinks are supposed
# to be packaged, and a ld.so.cache that handles both /app and /usr is
# maintained by flatpak. But occasionally a symlink is missed in packaging,
# and this will make sure it is created install time, as it would be
# system-wide.

%post -p /sbin/ldconfig

%transfiletriggerin -P 1999999 -- /app/lib /app/lib64
/sbin/ldconfig

%transfiletriggerin -- /app/share/glib-2.0/schemas
glib-compile-schemas /app/share/glib-2.0/schemas &> /dev/null || :

%transfiletriggerin -- /app/share/fonts
HOME=/root /usr/bin/fc-cache -s

%transfiletriggerin -- /app/share/java
for d in `find /app/share/java -type d`; do mkdir -p /usr${d#/app}; done
for f in `find /app/share/java ! -type d`; do ln -s $f /usr${f#/app}; done

%transfiletriggerin -P 1 -- /app
for l in `find /app -type l`; do \
  case `readlink $l` in /etc/alternatives/*) ln -fns `readlink -f $l` $l ;; esac \
done

%files
%dir %{_prefix}/cache
%dir %{_prefix}/cache/fontconfig
%{python3_sitelib}
%{_datadir}/metainfo/*.appdata.xml
%{_sysconfdir}/flatpak-builder/
%{_sysconfdir}/fonts/conf.d/*
%{_sysconfdir}/ld.so.conf.d/app.conf

%changelog
* Tue Oct 29 2024 Troy Dawson <tdawson@redhat.com> - 40-4
- Bump release for October 2024 mass rebuild:
  Resolves: RHEL-64018

* Sat Jun 08 2024 Owen Taylor <otaylor@redhat.com> - 40-3
- Adapt to centos-stream and RHEL for el10

* Mon Jun 24 2024 Troy Dawson <tdawson@redhat.com> - 40-2
- Bump release for June 2024 mass rebuild

* Wed Apr 03 2024 Yaakov Selkowitz <yselkowi@redhat.com> - 40-1
- Bump version

* Fri Mar 01 2024 Yaakov Selkowitz <yselkowi@redhat.com> - 39-6
- Add Java symlink trigger
- Add /app-built X11 font directories to fontconfig path
- Add alternatives symlink trigger

* Fri Dec 15 2023 Yaakov Selkowitz <yselkowi@redhat.com> - 39-5
- Add graphviz install trigger

* Thu Oct 05 2023 Kalev Lember <klember@redhat.com> - 39-4
- appdata: Add F39 versions

* Mon Sep 04 2023 Yaakov Selkowitz <yselkowi@redhat.com> - 39-3
- Provide sitecustomize instead of usercustomize

* Tue Aug 22 2023 Owen Taylor <otaylor@redhat.com> - 39-2
- Bump for rebuild

* Mon Aug 7 2023 Owen Taylor <otaylor@redhat.com> - 39-1
- Bump version

* Sat Mar 18 2023 Kalev Lember <klember@redhat.com> - 38-1
- appdata: Add F38 versions
- Revert "Provide systemd packages"

* Tue Feb 21 2023 Yaakov Selkowitz <yselkowi@redhat.com> - 37-4
- Add metainfo for KDE runtimes

* Tue Feb 21 2023 Yaakov Selkowitz <yselkowi@redhat.com> - 37-3
- Remove package notes from flatpak-builder compile flags

* Tue Sep 06 2022 Kalev Lember <klember@redhat.com> - 37-2
- Correctly substitute /app/lib in flatpak-builder defaults.json ldflags
- Revert "Fix search paths for /app-installed python modules" (#2026979)

* Wed Aug 17 2022 Kalev Lember <klember@redhat.com> - 37-1
- appdata: Add F37 versions

* Thu Aug 04 2022 Kalev Lember <klember@redhat.com> - 36-2
- Fix search paths for /app-installed python modules (#2112499)

* Mon May 02 2022 Tomas Popela <tpopela@redhat.com> - 36-1
- appdata: Add F36 versions

* Thu Sep 30 2021 Kalev Lember <klember@redhat.com> - 35-1
- appdata: Add F35 versions

* Tue Feb 02 2021 Kalev Lember <klember@redhat.com> - 34-1
- Install flatpak-builder defaults.json config file

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 33-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Wed Jul 29 2020 Kalev Lember <klember@redhat.com> - 33-1
- Install appdata for both the Platform and the Sdk

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 32-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Mar 06 2020 Kalev Lember <klember@redhat.com> - 32-1
- Remove Python 2 support (#1801932)

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 30-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Aug  8 2019 fedora-toolbox <otaylor@redhat.com> - 30-2
- Fix comment location in fontconfig config file

* Fri Jul 26 2019 Mark Otaris <mark@net-c.com> - 30-1
- Update font config to match freedesktop-sdk, allowing user-installed fonts to work

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 29-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 29-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Fri Sep 28 2018 Owen Taylor <otaylor@redhat.com> - 29-4
- Add a usercustomize.py to set up Python paths

* Sat Sep  8 2018 Owen Taylor <otaylor@redhat.com> - 29-3
- Fix path to gsettings schemas in trigger

* Sat Sep  8 2018 Owen Taylor <otaylor@redhat.com> - 29-2
- Avoid comments leaking into scriplets

* Sat Sep  8 2018 Owen Taylor <otaylor@redhat.com> - 29-1
- Add file triggers from glibc, glib2, and fontconfig

- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 27-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 27-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 27-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jun 29 2017 Owen Taylor <otaylor@redhat.com> - 27-3
- Make not noarch - the contents of /etc/ld.so.conf.d/app.conf
  depend on 64-bit vs. 32-bit
- Rename fontconfig conf file from 'xdg-app' to 'flatpak'

* Tue Jun 13 2017 Owen Taylor <otaylor@redhat.com> - 27-2
See https://bugzilla.redhat.com/show_bug.cgi?id=1460081
- Switch license to MIT
- Preserve timestamps on file installation
- Own /usr/cache since it's not a standard directory
- Require fontpackages-filesystem for /etc/fonts/conf.d

* Wed Jun  7 2017 Owen Taylor <otaylor@redhat.com> - 27-1
- Strip down to just config files

* Wed Jun  3 2015 Alexander Larsson <alexl@redhat.com>
- Initial version
