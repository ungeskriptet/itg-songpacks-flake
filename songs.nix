{
  lib,
  stdenvNoCC,
  newScope,
  fetchurl,
  fetchMega,
  unrar-free,
  unzip,
}:
let
  buildSongPack =
    {
      name,
      url,
      hash ? "",
      extension ? "zip",
      rootdir ? null,
    }:
    stdenvNoCC.mkDerivation (finalAttrs: {
      inherit name;

      src =
        let
          name = "${finalAttrs.name}-source";
        in
        if (builtins.match "https://mega.nz(.*)" url == null) then
          fetchurl { inherit url hash name; }
        else
          fetchMega { inherit url hash name; };

      nativeBuildInputs = [
        unrar-free
        unzip
      ];

      unpackPhase = ''
        runHook preUnpack
        unpackDir="$TMPDIR/unpack"
        mkdir "$unpackDir"
        cd "$unpackDir"

        renamed="$TMPDIR/${name}.${extension}"
        cp -r "$src" "$renamed"
        unpackFile "$renamed"
        chmod -R +w "$unpackDir"
        runHook postUnpack
      '';

      preInstall =
        if rootdir == null then
          ''
            rm -rf __MACOSX
            if [ $(ls -A . | wc -l) != 1 ]; then
              echo "error: song pack must contain a single directory."
              exit 1
            fi
          ''
        else
          "";

      postInstall =
        let
          source = if rootdir != null then lib.escapeShellArg "${rootdir}" else "*";
          dest = if rootdir != null then lib.escapeShellArg "/${rootdir}" else "";
        in
        ''
          mkdir -p "$out"/itgmania/Songs
          mv ${source} "$out"/itgmania/Songs${dest}
        '';
    });

  songPacks = lib.mapAttrs (
    n: v:
    v
    // {
      hash = v.hash or "";
      extension = v.extension or "zip";
      rootdir = v.rootdir or null;
    }
  ) (lib.importJSON ./songs.json);

  songPackAttrs = lib.mapAttrs' (
    name: value:
    lib.nameValuePair name (buildSongPack {
      inherit name;
      inherit (value)
        url
        hash
        extension
        rootdir
        ;
    })
  ) songPacks;
in
lib.makeScope newScope (self: songPackAttrs)
