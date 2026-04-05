{
  lib,
  runCommand,
  megatools,
}:
lib.fetchers.withNormalizedHash { } (
  {
    url,
    name ? baseNameOf url,
    allowedFailures ? "4",
    outputHash,
    outputHashAlgo,
  }:
  let
    isFolder = builtins.match "https://mega.nz/folder/(.*)" url != null;
  in
  runCommand name
    {
      inherit outputHash outputHashAlgo;
      outputHashMode = if isFolder then "recursive" else "flat";
      nativeBuildInputs = [ megatools ];
    }
    ''
      ${lib.optionalString isFolder ''
        mkdir -p "$out"
      ''}
      set +e
      failures=0
      while IFS= read -r line; do
        if echo "$line" | grep "WARNING: chunk download failed"; then
          ((failures++))
          echo "Detected mega.nz failure ($failures/${allowedFailures})"
        fi
        if [ $failures -ge ${allowedFailures} ]; then
          echo "Too many mega.nz failures, exiting."
          exit 1
        fi
        echo $line
      done < <(megadl ${url} --path "$out" 2>&1)
      set -e
    ''
)
