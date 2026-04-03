# itg-songpacks-flake
Manage ITGmania songspacks declaratively using nix

### Adding new songs to this flake
Add a new item to the root object in the `songs.json` file:
 - The object should have a nix derivation friendly name (all lowercase and no special characters)
   and contain a hash, URL and optionally a file extension in case the songpack is not a ZIP file.
 - If the pack name starts with a number, make sure to prefix it using an underscore (`_`).
   - E.g. `15gays1pack` -> `_15gays1pack`
 - To generate the hash, attempt to built it first using an empty hash, then paste in the correct
   hash from the failed build output.

When using songs.json, only direct downloads or MEGA links are supported.
For more complicated songpacks, a separate derivation should be created.

Afterwards, run `nix fmt` to format all changed files.

### Requests
Requests are welcome! Submit your PR or songpack request issue on [Codeberg](https://codeberg.org/ungeskriptet/itg-songpacks-flake) or [GitHub](https://github.com/ungeskriptet/itg-songpacks-flake). Or alternatively just ping me on whichever messaging platform I am with the songpack you would like :)
