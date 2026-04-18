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
        jobspySkill = pkgs.runCommand "jobspy-skill" { } ''
          mkdir -p "$out"
          cp ${./skills/jobspy/SKILL.md} "$out/SKILL.md"
        '';
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

        packages.jobspySkill = jobspySkill;

        packages.default = myApp;

        apps.default = flake-utils.lib.mkApp {
          drv = self.packages.${system}.default;
        };
      }
    )
    // {
      overlays.default = final: prev: {
        jobspy = self.packages.${final.stdenv.hostPlatform.system}.default;
        "jobspy-plugin" = self.packages.${final.stdenv.hostPlatform.system}.default;
        jobspySkill = self.packages.${final.stdenv.hostPlatform.system}.jobspySkill;
        "jobspy-skill" = self.packages.${final.stdenv.hostPlatform.system}.jobspySkill;
      };

      homeManagerModules.jobspy =
        { pkgs, ... }:
        {
          home.file.".agents/skills/jobspy/SKILL.md".source = "${pkgs.jobspySkill}/SKILL.md";
        };

      openclawPlugin = system: {
        name = "jobspy";
        skills = [ ./skills/jobspy ];
        packages = [
          self.packages.${system}.default
          self.packages.${system}.jobspySkill
        ];
        needs = {
          stateDirs = [ ];
          requiredEnv = [ ];
        };
      };
    };
}
