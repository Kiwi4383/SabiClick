{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = [
    (pkgs.python3.withPackages (ps: with ps; [ evdev pytest pyinstaller ]))
    pkgs.python3Packages.tkinter
  ];
  shellHook = ''
    echo "SabiClick env: python $(python3 --version) + tkinter + evdev + pytest"
  '';
}
