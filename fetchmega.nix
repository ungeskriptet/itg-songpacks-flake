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
      if ! megadl ${url} --path "$out"; then
        cat <<EOF
          Error: Couldn't download file from MEGA.
          The daily download limit might have been reached.
          Try again later or try downloading from a different
          public IP to bypass this restriction.
      EOF
      fi
    ''
)
