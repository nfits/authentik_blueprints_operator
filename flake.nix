{
  description = "Description for the project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      self,
      flake-parts,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];

      imports = [
        inputs.treefmt-nix.flakeModule
      ];

      perSystem =
        { config, pkgs, ... }:
        {
          devShells.default = pkgs.mkShell {
            packages = with pkgs; [
              config.treefmt.package
              uv
              kubectl
              postgresql.pg_config
              heimdal
              gcc13
              pkg-config
            ];
          };

          packages = rec {
            authentik_blueprints_operator =
              let
                overlay = workspace.mkPyprojectOverlay {
                  sourcePreference = "wheel";
                };
                pythonSets =
                  (pkgs.callPackage pyproject-nix.build.packages {
                    python = pkgs.python3;
                  }).overrideScope
                    (
                      pkgs.lib.composeManyExtensions [
                        pyproject-build-systems.overlays.default
                        pyproject-build-systems.overlays.wheel
                        overlay

                        (final: prev: {
                          ak-guardian = prev.ak-guardian.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [
                              final.hatchling
                              final.pathspec
                              final.pluggy
                              final.packaging
                              final.trove-classifiers

                            ];
                          });
                          authentik = prev.authentik.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [
                              final.hatchling
                              final.pathspec
                              final.pluggy
                              final.packaging
                              final.trove-classifiers

                            ];
                          });
                          django-channels-postgres = prev.django-channels-postgres.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [
                              final.hatchling
                              final.pathspec
                              final.pluggy
                              final.packaging
                              final.trove-classifiers
                            ];
                          });
                          django-dramatiq-postgres = prev.django-dramatiq-postgres.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [
                              final.hatchling
                              final.pathspec
                              final.pluggy
                              final.packaging
                              final.trove-classifiers

                            ];
                          });
                          django-postgres-cache = prev.django-postgres-cache.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [
                              final.hatchling
                              final.pathspec
                              final.pluggy
                              final.packaging
                              final.trove-classifiers

                            ];
                          });
                          gssapi = prev.gssapi.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [
                              final.setuptools
                              final.cython
                              pkgs.heimdal
                              pkgs.pkg-config
                              pkgs.gcc13
                            ];
                          });
                          opencontainers = prev.opencontainers.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [ final.setuptools ];
                          });
                          psycopg-c = prev.psycopg-c.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [
                              final.setuptools
                              pkgs.postgresql.pg_config
                            ];
                          });
                          djangorestframework = prev.djangorestframework.overrideAttrs (old: {
                            nativeBuildInputs = old.nativeBuildInputs ++ [ final.setuptools ];
                          });
                        })
                      ]
                    );

                workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = self; };
              in
              pythonSets.mkVirtualEnv "authentik_blueprints_operator-env" workspace.deps.default;
            authentik_blueprints_operator_image = pkgs.dockerTools.buildLayeredImage {
              name = "authentik_blueprints_operator";
              tag = "latest";
              created = "now";

              contents = with pkgs; [
                dockerTools.usrBinEnv
                dockerTools.binSh
                dockerTools.caCertificates
                busybox
                authentik_blueprints_operator
              ];

              fakeRootCommands = ''
                #!${pkgs.runtimeShell}

                mkdir -p ./etc

                cat ${pkgs.fakeNss}/etc/passwd > ./etc/passwd
                cat ${pkgs.fakeNss}/etc/group > ./etc/group

                if [ -f ${pkgs.fakeNss}/etc/shadow ]; then
                  cat ${pkgs.fakeNss}/etc/shadow > ./etc/shadow
                fi
                if [ -f ${pkgs.fakeNss}/etc/nsswitch.conf ]; then
                  cat ${pkgs.fakeNss}/etc/nsswitch.conf > ./etc/nsswitch.conf
                fi
              '';

              config = {
                Cmd = [ "authentik_blueprints_operator" ];
              };
            };
            authentik_blueprints_operator_crd = pkgs.runCommand "crd.yaml" { } ''
              export TMP=$(${pkgs.lib.getExe pkgs.mktemp} -d)

              ${pkgs.lib.getExe' authentik_blueprints_operator "kubesdk"} generate crd \
                --from-dir ${self}/authentik_blueprints_operator/models/ \
                --output $TMP

              ${pkgs.lib.getExe pkgs.gawk} 'FNR==1 && NR!=1  {print "---"} {print}' $TMP/*.yaml > $out
            '';
          };

          treefmt = {
            programs = {
              nixf-diagnose.enable = true;
              nixfmt.enable = true;
              black.enable = true;
            };
          };
        };
    };
}
