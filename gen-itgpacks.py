#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p "python3.withPackages (ps: with ps; [ lxml ])"
import csv
import json
import re
import sys
from argparse import ArgumentParser
from lxml import html
from pathlib import Path
from subprocess import Popen, PIPE, run
from urllib.error import HTTPError
from urllib.parse import urlparse, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from urllib.response import addinfourl

"""This is a mess"""


USER_AGENT = {"User-Agent": "ungeskriptet/itg-songpacks-flake"}
FLAKE_PATH = "/".join(__file__.split("/")[:-1])


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
            json.dump(packs_dict, file, ensure_ascii=False, indent="\t")

        info(f"Finished generating '{args.output}'")


def sanitize_file(args):
    with open(args.input) as input_file:
        info(f"Sanitizing '{args.output}'")
        packs = json.load(input_file)
        packs_sanitized = {}
        for key, value in packs.items():
            name = sanitize(key)
            packs_sanitized[name] = value

        with open(args.output, "w") as file:
            json.dump(packs_sanitized, file, ensure_ascii=False, indent="\t")
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
        json.dump(packs_dict, output, ensure_ascii=False, indent="\t")
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
        json.dump(packs_dict, output, ensure_ascii=False, indent="\t")
        info(f"'{args.output}' created")


def collect_hashes(args):
    with open(args.input) as input_file:
        info("Collecting hashes")
        packs = json.load(input_file)
    try:
        for key, value in packs.items():
            if value["hash"] == "" or args.all:
                info(f"Building {key}")
                cmd = [
                    "nix-instantiate",
                    "--eval",
                    "-E",
                    f"let pkgs = import <nixpkgs> {{ }}; in with pkgs.callPackage ./. {{ }}; itgPacks.{key}.src.outPath",
                    "--json",
                ]
                out_path = run(cmd, capture_output=True, cwd=FLAKE_PATH, text=True)
                out_path = json.loads(out_path.stdout)
                cmd = ["nix-build", "--no-out-link", "-A", f"itgPacks.{key}.src"]
                process = Popen(cmd, stderr=PIPE, text=True, bufsize=1)
                prev_line = ""
                for line in iter(process.stderr.readline, ""):
                    print(line, end="")
                    if prev_line.startswith("         specified: sha256"):
                        if "            got:    sha256" in line:
                            nix_hash = line.lstrip("            got:    ").rstrip("\n")
                    prev_line = line.rstrip("\n")
                process.wait()
                packs[key]["hash"] = nix_hash
                with open(args.output, "w") as output:
                    json.dump(packs, output, ensure_ascii=False, indent="\t")
                    info(f"Filled hash for '{key}'")
                try:
                    cmd = ["nix-store", "--delete", out_path]
                    run(cmd)
                except:
                    pass
    except:
        pass


class RunCmdError(Exception):
    pass


def run_cmd(cmd, cwd=None):
    process = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE, text=True, bufsize=1)
    for line in iter(process.stderr.readline, ""):
        print(line, end="")
    process.wait()
    last_line = None
    for line in iter(process.stdout.readline, ""):
        last_line = line.rstrip("\n")
    if last_line == None:
        raise RunCmdError
    return last_line


def build_test(args):
    if args.pack != None:
        packs = [args.pack]
    elif args.json != None:
        with open(args.json) as file:
            packs = json.load(file)
            packs = list(packs.keys())
    else:
        cmd = [
            "nix-instantiate",
            "--eval",
            "-E",
            "let pkgs = import <nixpkgs> { }; in with pkgs.callPackage ./. { }; builtins.attrNames itgPacks",
            "--json",
        ]
        packs = run(cmd, capture_output=True, cwd=FLAKE_PATH, text=True)
        packs = json.loads(packs.stdout)
    try:
        with open(args.input) as input_file:
            build_info = json.load(input_file)
            try:
                build_info["successful"]
                try:
                    build_info["failed"]
                except:
                    build_info["failed"] = []
            except:
                build_info["successful"] = []
    except:
        build_info = {"successful": [], "failed": []}
    for pack_name in packs:
        if pack_name in build_info["successful"]:
            info(f"Skipping '{pack_name}'")
            continue
        try:
            info(f"Fetching source for '{pack_name}'")
            cmd = ["nix-build", "--no-out-link", "-A", f"itgPacks.{pack_name}.src"]
            src = run_cmd(cmd, FLAKE_PATH)
            info(f"Testing build for '{pack_name}'")
            cmd = ["nix-build", "--no-out-link", "-A", f"itgPacks.{pack_name}"]
            out = run_cmd(cmd, FLAKE_PATH)
            build_info["successful"] += [pack_name]
        except RunCmdError:
            warning(f"Build failed for '{pack_name}'")
            build_info["failed"] = [pack_name]
        if args.output != Path(""):
            with open(args.output, "w") as file:
                json.dump(build_info, file, ensure_ascii=False, indent="\t")
        if args.delete:
            try:
                cmd = ["nix-store", "--delete", src]
                run(cmd)
                cmd = ["nix-store", "--delete", out]
                run(cmd)
            except:
                pass


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
    collect_hashes_arg.add_argument(
        "--delete", "-d", action="store_true", help="Clean up after fetching source"
    )
    collect_hashes_arg.add_argument(
        "--all", "-a", action="store_true", help="Recalculate all hashes"
    )

    build_test_arg = subparsers.add_parser(
        "build_test",
        aliases=["bt"],
        help="Test if all songpacks can build.",
    )
    build_test_arg.set_defaults(func=build_test)
    group = build_test_arg.add_mutually_exclusive_group()
    group.add_argument(
        "--json",
        "-j",
        default=None,
        type=Path,
        help="Path to JSON file containing songpacks (like songs.json). Will attempt to build all songpacks if left empty.",
    )
    group.add_argument(
        "--pack",
        "-p",
        default=None,
        type=str,
        help="Build specific songpack. Will attempt build all songpacks if left empty.",
    )
    build_test_arg.add_argument(
        "--input",
        "-i",
        default="itgpacks-build-result.json",
        type=Path,
        help="Path to input file with builds to skip. Empty argument will disable the reading of a skip list.",
    )
    build_test_arg.add_argument(
        "--output",
        "-o",
        default="itgpacks-build-result.json",
        type=Path,
        help="Path to output file with build info. Use empty argument to disable creating this file.",
    )
    build_test_arg.add_argument(
        "--delete", "-d", action="store_true", help="Clean up after each build attempt."
    )

    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    args.func(args)


if __name__ == "__main__":
    main()
