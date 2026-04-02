{
  pkgs ? import <nixpkgs> { },
}:
with pkgs;
let
  callPackage = lib.callPackageWith (pkgs // { inherit fetchMega; });
  fetchMega = callPackage ./fetchmega.nix { };
in
{
  inherit fetchMega;
  itgPacks = lib.recurseIntoAttrs (callPackage ./songs.nix { });
}
