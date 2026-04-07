{
  description = "lg - LG TV remote control";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python312;
      pythonPkgs = pkgs.python312Packages;
    in
    {
      packages.${system}.default = python.pkgs.buildPythonApplication {
        pname = "lg";
        version = "0.1.0";
        src = ./.;
        format = "pyproject";

        nativeBuildInputs = [ pythonPkgs.poetry-core pkgs.gobject-introspection pkgs.wrapGAppsHook4 ];
        buildInputs = [ pkgs.gtk4 ];
        propagatedBuildInputs = [ pythonPkgs.aiowebostv pythonPkgs.pygobject3 ];

        postInstall = ''
          mv $out/bin/lg $out/bin/lg-remote
        '';
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          python
          pkgs.poetry
          pythonPkgs.aiowebostv
          pythonPkgs.pygobject3
          pkgs.gtk4
          pkgs.gobject-introspection
        ];

        shellHook = ''
          export GI_TYPELIB_PATH="${pkgs.gtk4}/lib/girepository-1.0:${pkgs.gdk-pixbuf}/lib/girepository-1.0:${pkgs.pango}/lib/girepository-1.0:${pkgs.graphene}/lib/girepository-1.0:''${GI_TYPELIB_PATH:-}"
        '';
      };
    };
}
