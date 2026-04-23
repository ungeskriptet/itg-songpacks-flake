{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs =
    { nixpkgs, ... }@inputs:
    let
      forAllSystems = nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
      ];
      treefmtEval = forAllSystems (
        system:
        inputs.treefmt-nix.lib.evalModule nixpkgs.legacyPackages.${system} (
          { ... }:
          {
            projectRootFile = "flake.nix";
            programs = {
              black.enable = true;
              keep-sorted.enable = true;
              nixf-diagnose.enable = true;
              nixfmt.enable = true;
              biome = {
                enable = true;
                settings = {
                  assist.actions.source.useSortedKeys = "on";
                  files.maxSize = 1024 * 1024 * 2; # 2 MiB
                };
              };
              mdformat = {
                enable = true;
                settings = {
                  number = true;
                  wrap = 100;
                };
              };
            };
            settings = {
              verbose = 1;
              on-matched = "debug";
            };
          }
        )
      );
    in
    {
      itgPacks = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        (pkgs.lib.recurseIntoAttrs (pkgs.callPackage ./default.nix { inherit pkgs; })).itgPacks
      );
      formatter = forAllSystems (system: treefmtEval.${system}.config.build.wrapper);
    };
}
