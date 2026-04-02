#!/usr/bin/env python
import json
import re
from urllib.error import HTTPError
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

"""
Input file: itgpacks.json
Example:
[
  ["Pack Name 1", "https://url-1"],
  ["Pack Name 2", "https://url-2"]
]
"""


def info(text):
    print(f"\033[94mINFO: \033[00m{text}")


def warning(text):
    print(f"\033[93mWARNING: \033[00m{text}")


def sanitize(name: str):
    """This is a mess"""

    original_name = name

    # Remove leading dots
    name = re.match("\\.*(.*)", name)[1]

    # Only keep specified characters and
    # replace invalid characters with dashes
    name = re.split("[^a-zA-Z0-9-]+", name)
    name = "-".join(filter(None, name))

    # Limit string size to 207
    # (Taken from lib.strings.sanitizeDerivationName)
    name = name[-207:]

    # Make name all lowercase
    name = name.lower()

    # Prefix names starting with a number with an underscore
    name = f"_{name}" if len(re.findall("^[0-9]+", name)) > 0 else name

    # Remove leading dashes
    name = re.match("^-+(.*)", name)[1] if len(re.findall("^-+", name)) > 0 else name

    # Remove repeating characters
    name = re.split("[-]+", name)
    name = "-".join(filter(None, name))

    # Replace empty names with "unknown"
    name = "unknown" if len(name) == 0 or name == "-" else name

    if len(name) >= 30:
        warning(f"'{name}' has a long name")
    if name == "unknown":
        warning(f"Unable to sanitize '{original_name}'")

    return name


def gen_json():
    packs_dict = {}
    packs_nonascii = {}

    info("Generating itgpacks-generated.json")

    with open("itgpacks.json") as f:
        packs = json.load(f)
        for name, url in packs:
            # Filter supported sources
            if (
                url.startswith("https://drive.google.com/file/d/")
                or url.startswith("https://fs.electr1.ca/")
                or url.startswith("https://github.com/")
                or url.startswith("https://mega.nz/")
                or url.startswith("https://mirror.reenigne.net/simfiles/")
                or url.startswith("https://nnty.fun/")
                or url.startswith("https://omid.gg")
                or url.startswith("https://peekingboo.com/")
                or url.startswith("https://simfiles.strykor.net/")
                or url.startswith("https://staminanation.com/")
                or url.startswith("https://stepmaniaonline.net/")
                or url.startswith("https://www.dropbox.com/")
                or url.startswith("https://zaneis.moe/")
            ):
                name = sanitize(name)
                if url.startswith("https://drive.google.com/file/d/"):
                    id = url.split("https://drive.google.com/file/d/")[1].split("/")[0]
                    url = f"https://drive.usercontent.google.com/download?confirm=t&id={id}"
                if url.startswith("https://stepmaniaonline.net/pack/"):
                    id = url.split("https://stepmaniaonline.net/pack/")[1].split("/")[0]
                    url = f"https://stepmaniaonline.net/download/pack/{id}/"
                if url.startswith("https://www.dropbox.com/"):
                    if "dl=0" in urlparse(url).query:
                        url = url.replace("dl=0", "dl=1")
                    else:
                        url = (
                            url
                            + ("&" if urlparse(url).query else "?")
                            + urlencode({"dl": "1"})
                        )
                packs_dict[name] = {"url": url, "hash": ""}

        with open("itgpacks-generated.json", "w") as file:
            json.dump(packs_dict, file, ensure_ascii=False, sort_keys=True, indent="\t")

        info("Finished generating itgpacks-generated.json")


def check_gdrive():
    packs_dict = {}

    info("Checking Google Drive availability")

    with open("itgpacks-generated.json") as f:
        packs = json.load(f)
        for key, value in packs.items():
            req = Request(url=value["url"], method="GET")
            if value["url"].startswith("https://drive.usercontent.google.com"):
                info(f"Checking {key}")
                try:
                    urlopen(req)
                except HTTPError as e:
                    if e.code == 404:
                        warning(f"Google Drive returned 404 for {key}")
                        packs_dict[key] = value
                        continue
                    else:
                        raise

    if packs_dicts != {}:
        with open("itgpacks-gdrive-failed.json", "w") as file:
            json.dump(packs_dict, file, ensure_ascii=False, sort_keys=True, indent="\t")

    info("Finished checking Google Drive availability")


gen_json()
# check_gdrive()
