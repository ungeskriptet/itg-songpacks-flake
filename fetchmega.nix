{
  lib,
  runCommand,
  megatools,
}:
lib.fetchers.withNormalizedHash { } (
  {
    url,
    name ? baseNameOf url,
    outputHash,
    outputHashAlgo,
    recursiveHash ? false,
  }:
  runCommand name
    {
      inherit outputHash outputHashAlgo;
      outputHashMode = if recursiveHash then "recursive" else "flat";
      nativeBuildInputs = [ megatools ];
    }
    ''
      megadl ${url} --path "$out"
    ''
)
