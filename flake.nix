{
  description = "job search openclaw plugin";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {

      perSystem = { self', pkgs, system, ... }:
      let
        myPython = (pkgs.python3.withPackages (python-pkgs: [
          python-pkgs.jobspy
          python-pkgs.python-lsp-server
          python-pkgs.ruff
        ]));
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            myPython
          ];

          shellHook = ''
            # so running the python module runs correctly
            export PYTHONPATH="src:."
          '';
        };
        
        packages.default = pkgs.hello;

        openclawPlugin = {
          name = "jobspy";
          skills = [ ./skills/jobspy ];
          packages = [ myPython ];
          needs = {
            stateDirs = [ ];
            requiredEnv = [ ];
          };
        };
      };

      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin" ];
    };
}
