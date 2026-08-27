application_id = 'org.maldoro.fyvin'

foreach size : ['16x16', '32x32', '48x48', '64x64', '128x128']
  install_data(
    'hicolor' / size / 'apps' / ('@0@.png').format(application_id),
    install_dir: get_option('datadir') / 'icons' / 'hicolor' / size / 'apps',
  )
endforeach

install_data(
  'hicolor' / 'symbolic' / 'apps' / ('@0@-symbolic.png').format(application_id),
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'symbolic' / 'apps',
)

install_subdir(
  'hicolor' / 'symbolic' / 'actions',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'symbolic',
  strip_directory: false,
)
