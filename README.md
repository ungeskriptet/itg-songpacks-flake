# itg-songpacks-flake

Manage ITGmania songspacks declaratively using nix

### Usage

#### NixOS (Flakes)

1. Add the following input to your `flake.nix`:
   ```nix
   inputs = {
     nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
     itgpacks = {
       url = "git+https://codeberg.org/ungeskriptet/itg-songpacks-flake.git";
       inputs.nixpkgs.follows = "nixpkgs";
     };
   };
   ```
   Don't forget to pass the new input to your `nixosConfigurations` definition.
2. Now install ITGmania in your environment like so:
   ```nix
   { pkgs, inputs, ... }:
   {
     environment.systemPackages = [
       (pkgs.itgmania.override {
         extraPackages =
           with inputs.itgpacks.itgPacks.${pkgs.stdenv.hostPlatform.system};
           [
             _15gays1pack
             blue-arrow-project-3
             itl-online-2025
             # See songs.json for a full list of songpacks
           ]
           ++ (with pkgs.itgmaniaPackages; [
             # For a full list of additional packages see
             # https://github.com/NixOS/nixpkgs/blob/master/pkgs/by-name/it/itgmania/packages.nix
             digital-dance
             zmod-simply-love
           ]);
       })
     ];
   }
   ```
3. After running `nixos-rebuild` ITGmania should now have all defined songpacks and themes. You can
   still install songpacks, themes, etc. the usual way.

### Adding new songs to this flake

#### Manually

Add a new item to the root object in the `songs.json` file:

- The object should have a nix derivation friendly name (all lowercase and no special characters)
  and contain a hash, URL and optionally a file extension in case the songpack is not a ZIP file.
- If the pack name starts with a number, make sure to prefix it using an underscore (`_`).
  - E.g. `15gays1pack` -> `_15gays1pack`
- To generate the hash, attempt to build it first using an empty hash, then paste in the correct
  hash from the failed build output.
- Build using `nix-build -A itgPacks.<packname>` or `nix build path:.#itgPacks.<packname>`.

#### Import songpack batch

1. Create a new CSV file containg songpacks:
   - First column must be the pack name (can be the original name, script will sanitize the name).
   - Second column must be the URL.
   - Use `,` for the field delimiter and `"` for the string delimiter.
2. Generate the JSON file using `./gen-itgpacks.py gen_json -i <input.csv>`.
3. Check URLs for availability using `./gen-itgpacks.py url_check -i itgpacks-generated.json`
4. Collect the hashes using `./gen-itgpacks.py collect_hashes -i itgpacks-filtered.json`.
5. Merge the JSON output file with `songs.json`.

#### Notes

- When using songs.json, only direct downloads or MEGA links are supported.
  - For more complicated songpacks, a separate derivation should be created.
- Run `nix fmt` to format all changed files.

### Requests

Requests are welcome! Submit your PR or songpack request issue on
[Codeberg](https://codeberg.org/ungeskriptet/itg-songpacks-flake) or
[GitHub](https://github.com/ungeskriptet/itg-songpacks-flake). Or alternatively just ping me on
whichever messaging platform I am with the songpack you would like :)
