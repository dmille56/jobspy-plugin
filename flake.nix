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
            rev = "713a87a0962b2d3481443f7b1466b5bf7ce27369";
            sha256 = "sha256-aekq0RgYH9pgJ1lMKaRQaq7vrbQH9zHPyv0tnuS/x98=";
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
