#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p "python3.withPackages (ps: with ps; [ lxml ])"
import csv
import json
import re
import sys
from argparse import ArgumentParser
from lxml import html
from pathlib import Path
from subprocess import Popen, PIPE
from urllib.error import HTTPError
from urllib.parse import urlparse, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from urllib.response import addinfourl

"""This is a mess"""


USER_AGENT = {"User-Agent": "ungeskriptet/itg-songpacks-flake"}


def info(text):
    print(f"\033[94mINFO: \033[00m{text}")


def warning(text):
    print(f"\033[93mWARNING: \033[00m{text}")


def sanitize(name: str):
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

    # Fix possessive nouns
    name = "s-".join(name.split("-s-"))

    if len(name) >= 30:
        warning(f"'{name}' has a long name")
    if name == "unknown":
        warning(f"Unable to sanitize '{original_name}'")

    return name


def gen_json(args):
    """
    Input file must use comma as the field delimiter
    and double quotes as the string delimiter.
    """
    packs_dict = {}
    packs_nonascii = {}

    info("Generating itgpacks-generated.json")

    with open(args.input) as f:
        packs = csv.reader(f, delimiter=",", quotechar='"')
        for name, url in packs:
            # Filter supported sources
            if (
                url.startswith("https://drive.google.com/file/d/")
                or url.startswith("https://boo.dance/")
                or url.startswith("https://fs.electr1.ca/")
                or url.startswith("https://github.com/")
                or url.startswith("https://mega.nz/")
                or url.startswith("https://mirror.reenigne.net/simfiles/")
                or url.startswith("https://nextcloud.573573573.xyz/")
                or url.startswith("https://nnty.fun/")
                or url.startswith("https://omid.gg")
                or url.startswith("https://peekingboo.com/")
                or url.startswith("https://simfiles.strykor.net/")
                or url.startswith("https://staminanation.com/")
                or url.startswith("https://stepmaniaonline.net/")
                or url.startswith("https://www.dropbox.com/")
                or url.startswith("https://zaneis.moe/")
                or url.startswith("https://zenius-i-vanisher.com/")
            ):
                name = sanitize(name)
                if url.startswith("https://peekingboo.com/"):
                    url = url.replace("https://peekingboo.com/", "https://boo.dance/")
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

        with open(args.output, "w") as file:
            json.dump(packs_dict, file, ensure_ascii=False, sort_keys=True, indent="\t")

        info(f"Finished generating '{args.output}'")


def fill_hashes(args):
    """
    Input file example:
    {
      'pack-drv-name-1': 'sha256-AAA...',
      'pack-drv-name-2': 'sha256-BBB...'
    }
    """
    with open(args.input) as input_file:
        packs = json.load(input_file)

        with open(args.hashes) as hash_file:
            hashes = json.load(hash_file)
            for pack_key, pack_value in packs.items():
                for hash_key, hash_value in hashes.items():
                    if pack_key == hash_key:
                        packs[pack_key]["hash"] = hash_value

        with open(args.output, "w") as file:
            json.dump(packs, file, ensure_ascii=False, sort_keys=True, indent="\t")
            info(f"'{args.output}' created")


def sanitize_file(args):
    with open(args.input) as input_file:
        info(f"Sanitizing '{args.output}'")
        packs = json.load(input_file)
        packs_sanitized = {}
        for key, value in packs.items():
            name = sanitize(key)
            packs_sanitized[name] = value

        with open(args.output, "w") as file:
            json.dump(
                packs_sanitized, file, ensure_ascii=False, sort_keys=True, indent="\t"
            )
            info(f"'{args.output}' created")


def ziv_scrape(args):
    packs_dict = {}
    info("Scraping Zenius -I- Vanisher")
    req = Request(
        url="https://zenius-i-vanisher.com/v5.2/simfiles.php?category=simfiles",
        method="GET",
        headers=USER_AGENT,
    )
    with urlopen(req) as ziv_html:
        tree = html.fromstring(ziv_html.read().decode())
        ziv_packs = tree.xpath("//option")
        for pack in ziv_packs:
            name = sanitize(pack.text)
            pack_id = pack.attrib["value"]
            url = f"https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid={pack_id}"
            packs_dict[name] = {"hash": "", "rootdir": pack.text, "url": url}

    with open(args.output, "w") as output:
        json.dump(packs_dict, output, ensure_ascii=False, sort_keys=True, indent="\t")
        info(f"'{args.output}' created")


def url_check(args):
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *_args: object) -> Request | None:
            return None

        def http_error_302(self, req, fp, code, msg, headers):
            infourl = addinfourl(fp, headers, req.get_full_url())
            return infourl

    OPENER = build_opener(NoRedirect)

    packs_dict = {}
    info("Checking URLs for availability")

    with open(args.input) as input_file:
        packs = json.load(input_file)
        for key, value in packs.items():
            if value["url"].startswith("https://zenius-i-vanisher.com/"):
                info(f"Checking redirect for '{key}'")
                req = Request(url=value["url"], method="GET", headers=USER_AGENT)
                with OPENER.open(req) as res:
                    if res.getheader("location") != None:
                        packs_dict[key] = value
                    else:
                        warning(f"Removing '{key}' (bad redirect)")
            else:
                info(f"Checking status code for '{key}'")
                try:
                    req = Request(url=value["url"], method="GET", headers=USER_AGENT)
                    urlopen(req)
                    packs_dict[key] = value
                except HTTPError as e:
                    warning(f"Removing '{key}' (bad status code)")
                    continue

    with open(args.output, "w") as output:
        json.dump(packs_dict, output, ensure_ascii=False, sort_keys=True, indent="\t")
        info(f"'{args.output}' created")


def collect_hashes(args):
    with open(args.input) as input_file:
        info("Collecting hashes")
        packs = json.load(input_file)
        for key, value in packs.items():
            if value["hash"] == "":
                info(f"Building {key}")
                cmd = ["nix-build", "--no-out-link", "-A", f"itgPacks.{key}"]
                process = Popen(cmd, stderr=PIPE, text=True, bufsize=1)
                prev_line = ""
                for line in iter(process.stderr.readline, ""):
                    print(line, end="")
                    if (
                        prev_line
                        == "         specified: sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
                    ):
                        if "            got:    sha256" in line:
                            nix_hash = line.lstrip("            got:    ").rstrip("\n")
                    prev_line = line.rstrip("\n")
                process.wait()
                packs[key]["hash"] = nix_hash
                with open(args.output, "w") as output:
                    json.dump(
                        packs, output, ensure_ascii=False, sort_keys=True, indent="\t"
                    )
                    info(f"Filled hash for '{key}'")


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    gen_json_arg = subparsers.add_parser(
        "gen_json", aliases=["g"], help="Generate JSON file"
    )
    gen_json_arg.set_defaults(func=gen_json)
    gen_json_arg.add_argument(
        "--input", "-i", default="itgpacks.csv", type=Path, help="CSV input file"
    )
    gen_json_arg.add_argument(
        "--output",
        "-o",
        default="itgpacks-generated.json",
        type=Path,
        help="JSON output file",
    )

    fill_hashes_arg = subparsers.add_parser(
        "fill_hashes", aliases=["f"], help="Fill hashes"
    )
    fill_hashes_arg.set_defaults(func=fill_hashes)
    fill_hashes_arg.add_argument(
        "--input", "-i", default="itgpacks-generated.json", type=Path, help="Input file"
    )
    fill_hashes_arg.add_argument(
        "--hashes",
        "-H",
        default="itgpacks-hashes.json",
        type=Path,
        help="Input file with hashes",
    )
    fill_hashes_arg.add_argument(
        "--output",
        "-o",
        default="itgpacks-filled-hashes.json",
        type=Path,
        help="Output file",
    )

    sanitize_arg = subparsers.add_parser(
        "sanitize", aliases=["s"], help="Sanitize pack names"
    )
    sanitize_arg.set_defaults(func=sanitize_file)
    sanitize_arg.add_argument(
        "--input", "-i", default="songs.json", type=Path, help="Input file"
    )
    sanitize_arg.add_argument(
        "--output",
        "-o",
        default="itgpacks-sanitized.json",
        type=Path,
        help="Output file",
    )

    ziv_scrape_arg = subparsers.add_parser(
        "ziv_scrape", aliases=["z"], help="Scrape Zenius -I- Vanisher songpacks"
    )
    ziv_scrape_arg.set_defaults(func=ziv_scrape)
    ziv_scrape_arg.add_argument(
        "--output",
        "-o",
        default="itgpacks-ziv.json",
        type=Path,
        help="Output file",
    )

    url_check_arg = subparsers.add_parser(
        "url_check", aliases=["uc"], help="Check URLs for availability"
    )
    url_check_arg.set_defaults(func=url_check)
    url_check_arg.add_argument(
        "--input", "-i", default="songs.json", type=Path, help="Input file"
    )
    url_check_arg.add_argument(
        "--output",
        "-o",
        default="itgpacks-filtered.json",
        type=Path,
        help="Output file",
    )

    collect_hashes_arg = subparsers.add_parser(
        "collect_hashes",
        aliases=["ch"],
        help="Collect hashes for songspacks with empty hash",
    )
    collect_hashes_arg.set_defaults(func=collect_hashes)
    collect_hashes_arg.add_argument(
        "--input", "-i", default="songs.json", type=Path, help="Input file"
    )
    collect_hashes_arg.add_argument(
        "--output",
        "-o",
        default="itgpacks-hashes.json",
        type=Path,
        help="Output file",
    )

    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    args.func(args)


if __name__ == "__main__":
    main()
