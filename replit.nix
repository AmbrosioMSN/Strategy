{ pkgs }: {
  deps = [
    pkgs.python312Packages.gunicorn
    pkgs.python3
    pkgs.python3Packages.flask
  ];
}
