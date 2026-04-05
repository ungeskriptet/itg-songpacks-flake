{
  lib,
  stdenvNoCC,
  newScope,
  fetchurl,
  fetchMega,
  _7zz,
  unrar-free,
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
    assert extension == "" -> rootdir != null;
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
        _7zz
        unrar-free
      ];

      preUnpack = ''
        unpackCmdHooks+=(_try7zip)
        _try7zip() {
          if ! [[ $curSrc =~ \.zip$ ]]; then return 1; fi
          7zz x "$curSrc"
        }
      '';

      unpackPhase = ''
        runHook preUnpack
        unpackDir="$TMPDIR/unpack"
        mkdir "$unpackDir"
        cd "$unpackDir"
        ${
          if extension != "" then
            ''
              renamed="$TMPDIR/${name}.${extension}"
              cp -r "$src" "$renamed"
              unpackFile "$renamed"
            ''
          else
            ''
              mkdir "${rootdir}"
              cp -r "$src"/{.*,*} "${rootdir}"
            ''
        }
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
          if [ -d ${source} ]; then
            mkdir -p "$out"/itgmania/Songs
            mv ${source} "$out"/itgmania/Songs${dest}
          else
            # For packs with songs in the root of the source
            # (Like songpacks from Zenius -I- Vanisher)
            mkdir -p "$out"/itgmania/Songs/${source}
            mv {.*,*} "$out"/itgmania/Songs/${source}
          fi
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
