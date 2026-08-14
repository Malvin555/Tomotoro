pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'maldoro'
gnome = import('gnome')

# gnome.compile_resources('maldoro',
#   'maldoro.gresource.xml',
#   gresource_bundle: true,
#   install: true,
#   install_dir: pkgdatadir,
# )

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'maldoro.in',
  output: 'maldoro',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

install_data(
  [
    '__init__.py',
    'main.py',
  ],
  install_dir: moduledir,
)

install_subdir('services', install_dir: moduledir)
install_subdir('utils', install_dir: moduledir)
install_subdir('view', install_dir: moduledir)
