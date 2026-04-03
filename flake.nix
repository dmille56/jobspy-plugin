{
  description = "jobspy job search openclaw plugin";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        myPython = pkgs.python3.withPackages (python-pkgs: [
          python-pkgs.jobspy
          python-pkgs.python-lsp-server
          python-pkgs.ruff
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [ myPython ];
          shellHook = ''
            export PYTHONPATH="src:."
          '';
        };

        packages.default = myPython;

        apps.default = flake-utils.lib.mkApp {
          drv = self.packages.${system}.default;
        };
      }
    ) // {
      openclawPlugin = system: {
        name = "jobspy";
        skills = [ ./skills/jobspy ];
        packages = [ self.packages.${system}.default ];
        needs = {
          stateDirs = [ ];
          requiredEnv = [ ];
        };
      };
    };
}
