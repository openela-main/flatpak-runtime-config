Name:           flatpak-runtime-config
Version:        34
Release:        4%{?dist}
Summary:        Configuration files that live inside the flatpak runtime
Source1:        50-flatpak.conf
Source2:        usercustomize.py
Source3:        com.redhat.Platform.appdata.xml
Source4:        com.redhat.Sdk.appdata.xml
Source5:        defaults.json.in
Source6:        05-flatpak-fontpath.conf

License:        MIT

BuildRequires:  python2
BuildRequires:  python2-rpm-macros
BuildRequires:  python3
BuildRequires:  python3-rpm-macros

Requires:       fontpackages-filesystem

%description
This package includes configuration files that are installed into the flatpak
runtime filesystem during the runtime creation process; it is also installed
into the build root when building RPMs. It contains all configuration
files that need to be different when executing a flatpak.

%prep

%build

%install
export RHEL_ALLOW_PYTHON2_FOR_BUILD=1

rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_prefix}/cache/fontconfig
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/fonts/conf.d
install -t $RPM_BUILD_ROOT%{_sysconfdir}/fonts/conf.d -p -m 0644 %{SOURCE1}
install -t $RPM_BUILD_ROOT%{_sysconfdir}/fonts/conf.d -p -m 0644 %{SOURCE6}

# usercustomize.py to set up Python paths
for d in %{python2_sitelib} %{python3_sitelib} ; do
    mkdir -p $RPM_BUILD_ROOT/$d
    install -t $RPM_BUILD_ROOT/$d -m 0644 %{SOURCE2}
done

# Install appdata for both the Platform and the Sdk
mkdir -p $RPM_BUILD_ROOT%{_datadir}/metainfo
install -t $RPM_BUILD_ROOT%{_datadir}/metainfo -p -m 0644 %{SOURCE3}
install -t $RPM_BUILD_ROOT%{_datadir}/metainfo -p -m 0644 %{SOURCE4}

# Install flatpak-builder config file
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/flatpak-builder
sed -e 's|%%{_libdir}|%{_libdir}|' \
    -e 's|%%{_lib}|%{_lib}|' \
    -e 's|%%{build_cflags}|%{build_cflags}|' \
    -e 's|%%{build_cxxflags}|%{build_cxxflags}|' \
    -e 's|%%{build_ldflags}|%{build_ldflags}|' \
    %{SOURCE5} > $RPM_BUILD_ROOT%{_sysconfdir}/flatpak-builder/defaults.json

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

%files
%dir %{_prefix}/cache
%dir %{_prefix}/cache/fontconfig
%{python2_sitelib}
%{python3_sitelib}
%{_datadir}/metainfo/*.appdata.xml
%{_sysconfdir}/flatpak-builder/
%{_sysconfdir}/fonts/conf.d/*
%{_sysconfdir}/ld.so.conf.d/app.conf

%changelog
* Wed Oct 15 2025 Tomas Popela <tpopela@redhat.com> - 34-4
- Re-enable the python2 support and fix various things that broke when I've
  by mistake used RHEL 9 SRPM when importing into RHEL 8
- Resolves: RHEL-121407

* Fri Mar 24 2023 Tomas Popela <tpopela@redhat.com> - 34-3
- Sync with Fedora
- Add a seed for <dir prefix="xdg">fonts</dir> (by tagoh)

* Fri Mar 17 2023 Tomas Popela <tpopela@redhat.com> - 34-2
- Sync with Fedora
- Correctly substitute /app/lib in flatpak-builder defaults.json ldflags (by klember)
- Include fonts-dirs.xml in fontconfig flatpak configuration (by tagoh)
- Add 05-flatpak-fontpath.conf that forces a different MD5 for fontconfig cache to avoid
  conflict between caches on host and flatpak (by tagoh)

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
