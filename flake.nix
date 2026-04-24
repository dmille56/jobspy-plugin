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
        jobspy = pythonPackages.jobspy.overridePythonAttrs (old: rec {
          version = "1.1.82-fork-713a87a";
          src = pkgs.fetchFromGitHub {
            owner = "dmille56";
            repo = "JobSpy";
            rev = "ed205bf3566fae606968495c438baf6c711af32d";
            sha256 = "ha256-C+kV5VLUGINDFGXM1OS0jDKMo4ZfsKinO8O4xBdJ2B8=";
          };
        });
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
            jobspy
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
            jobspy
            pythonPackages.pandas
            pythonPackages.python-lsp-server
            pythonPackages.ruff
          ];
        };

        packages.jobspySkill = jobspySkill;

        packages.default = myApp;

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/jobspy";
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
