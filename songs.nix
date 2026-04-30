{
  lib,
  stdenvNoCC,
  makeSetupHook,
  newScope,
  writeShellScript,
  fetchzip,
  fetchMega,
  _7zz,
  unrar-free,
}:
let
  _7zzHook = makeSetupHook { name = "_7zzHook"; } (
    writeShellScript "7zz-hook.sh" ''
      unpackCmdHooks+=(_try7zip)
      _try7zip() {
        if ! [[ $curSrc =~ \.zip$ ]]; then return 1; fi
        ${lib.getExe _7zz} x "$curSrc"
      }
    ''
  );
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
          (fetchzip.override { withUnzip = false; } {
            inherit
              url
              hash
              name
              extension
              ;
            nativeBuildInputs = [
              _7zzHook
              unrar-free
            ];
            stripRoot = false;
          })
        else
          fetchMega { inherit url hash name; };

      nativeBuildInputs = [
        _7zzHook
        unrar-free
      ];

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
          dest = if rootdir != null then lib.escapeShellArg "/${baseNameOf rootdir}" else "";
        in
        ''
          if [ -d */${source} ]; then
            cd *
            mkdir -p "$out"/itgmania/Songs
            if [ -d ${source} ]; then
              mv -- ${source} "$out"/itgmania/Songs${dest}
            else
              mkdir -p "$out"/itgmania/Songs${dest}
              mv * "$out"/itgmania/Songs${dest}
            fi
          elif [ -d ${source} ]; then
            mkdir -p "$out"/itgmania/Songs
            mv -- ${source} "$out"/itgmania/Songs${dest}
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
