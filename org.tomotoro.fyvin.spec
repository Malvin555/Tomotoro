Name:           tomotoro
Version:        1.0.0
Release:        1%{?dist}
Summary:        Pomodoro app built for GNOME

License:        GPLv3+
URL:            https://github.com/malvin55/MalDoro
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  meson >= 0.59.0
BuildRequires:  ninja-build
BuildRequires:  python3-devel
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(libadwaita-1)
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

Requires:       python3
Requires:       python3-gobject
Requires:       libadwaita
Requires:       gtk4

%description
Tomotoro is a Gtk4 and Libadwaita Pomodoro application written in Python.

%prep
%autosetup

%build
%meson
%meson_build

%install
%meson_install

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/org.tomotoro.fyvin.desktop

%files
%license COPYING LICENSE
%doc README.md
%{_bindir}/tomotoro
%{_datadir}/applications/org.tomotoro.fyvin.desktop
%{_datadir}/dbus-1/services/org.tomotoro.fyvin.service
%{_datadir}/glib-2.0/schemas/org.tomotoro.fyvin.gschema.xml
%{_datadir}/metainfo/org.tomotoro.fyvin.metainfo.xml
%{_datadir}/icons/hicolor/*/
%{_datadir}/tomotoro/


%changelog
* Thu Oct 22 2026 malvin55 <malvin@example.com> - 1.0.0-1
- Initial RPM release