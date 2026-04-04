# itg-songpacks-flake

Manage ITGmania songspacks declaratively using nix

### Adding new songs to this flake

#### Manually

Add a new item to the root object in the `songs.json` file:

- The object should have a nix derivation friendly name (all lowercase and no special characters)
  and contain a hash, URL and optionally a file extension in case the songpack is not a ZIP file.
- If the pack name starts with a number, make sure to prefix it using an underscore (`_`).
  - E.g. `15gays1pack` -> `_15gays1pack`
- To generate the hash, attempt to built it first using an empty hash, then paste in the correct
  hash from the failed build output.

#### Import songpack batch

1. Create a new CSV file containg songpacks:
   - First column must be the pack name (can be the original name, script will sanitize the name).
   - Second column must be the URL.
   - Use `,` for the field delimiter and `"` for the string delimiter.
2. Generate the JSON file using `./gen-itgpacks.py gen_json -i <input.csv>`.
3. Merge the JSON output file with `songs.json`.
4. Collect the hashes using `nix-build --no-out-link --keep-going 2>&1 | tee itgpacks-hashes.txt`.
5. Create a JSON file for filling the hashes in `songs.json` with the following schema:
   ```
   {
     "song-drv-name-1": "sha256-AAA...",
     "song-drv-name-2": "sha256-BBB..."
   }
   ```
6. Fill hashes using `./gen-itgpacks.py fill_hashes`.
7. Merge the output file with `songs.json`.

#### Notes

- When using songs.json, only direct downloads or MEGA links are supported.
  - For more complicated songpacks, a separate derivation should be created.
- Run `nix fmt` to format all changed files.

### Requests

Requests are welcome! Submit your PR or songpack request issue on
[Codeberg](https://codeberg.org/ungeskriptet/itg-songpacks-flake) or
[GitHub](https://github.com/ungeskriptet/itg-songpacks-flake). Or alternatively just ping me on
whichever messaging platform I am with the songpack you would like :)
