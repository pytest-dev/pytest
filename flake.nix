{
  description = "Development environment for Pytest";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs";
    systems.url = "github:nix-systems/default";
  };

  outputs = { self, nixpkgs, nixpkgs-unstable, systems }:
    let
      forAllSystems = nixpkgs.lib.genAttrs (import systems);
      mkPkgs = system: import nixpkgs {
        inherit system;
        overlays = [ self.overlays.newer-pre-commit ];
      };
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = mkPkgs system;
        in
        {
          fhs-test-env = pkgs.buildFHSEnv {
            name = "fhs-test-env";
            targetPkgs = fhspkgs:
              let
                python313-with-tox = pkgs.python313.withPackages (ps: with ps; [
                  tox
                ]);
              in
              [
                python313-with-tox

                # other Pythons
                fhspkgs.python310
                fhspkgs.python311
                fhspkgs.python312
                fhspkgs.python314

                fhspkgs.bashInteractive
                fhspkgs.pre-commit

              ];
            runScript = "bash";
          };
        });

      devShells = forAllSystems (system:
        let
          pkgs = mkPkgs system;
        in
        {
          default = pkgs.mkShell {
            packages = [ self.packages.${system}.fhs-test-env ];
            shellHook = "exec fhs-test-env";
          };
        });

      overlays = {
        newer-pre-commit = final: prev: {
          pre-commit =
            let
              pkgs = import nixpkgs-unstable { inherit (final.stdenv.hostPlatform) system; };
            in
            pkgs.pre-commit;
        };
      };
    };
}
