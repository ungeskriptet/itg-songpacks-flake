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
    recursiveHash ? false,
  }:
  runCommand name
    {
      inherit outputHash outputHashAlgo;
      outputHashMode = if recursiveHash then "recursive" else "flat";
      nativeBuildInputs = [ megatools ];
    }
    ''
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
      done < <(megadl ${url} --path "$out" 2>&1)
      set -e
    ''
)
