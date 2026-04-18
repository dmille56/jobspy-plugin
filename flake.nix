{
  description = "jobspy job search openclaw plugin";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
        pythonPackages = pkgs.python3Packages;
        myApp = pythonPackages.buildPythonApplication {
          pname = "jobspy-plugin";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";

          nativeBuildInputs = [
            pythonPackages.setuptools
            pythonPackages.wheel
          ];

          propagatedBuildInputs = [
            pythonPackages.jobspy
            pythonPackages.pandas
          ];

          meta = with pkgs.lib; {
            mainProgram = "jobspy";
          };
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            pythonPackages.jobspy
            pythonPackages.pandas
            pythonPackages.python-lsp-server
            pythonPackages.ruff
          ];
        };

        packages.default = myApp;

        apps.default = flake-utils.lib.mkApp {
          drv = self.packages.${system}.default;
        };
      }
    )
    // {
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
