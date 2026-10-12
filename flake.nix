{
  description = "SabiClick — Wayland auto-clicker (Tkinter + evdev)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAll = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in
    {
      devShells = forAll (pkgs: {
        default = pkgs.mkShell {
          buildInputs = [
            (pkgs.python3.withPackages (ps: with ps; [ evdev pytest pyinstaller ]))
            pkgs.python3Packages.tkinter
          ];
        };
      });

      apps = forAll (pkgs:
        let
          py = pkgs.python3.withPackages (ps: with ps; [ evdev ]);
          tk = pkgs.python3Packages.tkinter;
        in
        {
          default = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "sabiclick" ''
              export PYTHONPATH="${tk}/${pkgs.python3.sitePackages}:$PYTHONPATH"
              exec ${py}/bin/python ${self}/main.py "$@"
            ''}/bin/sabiclick";
          };
        });
    };
}
