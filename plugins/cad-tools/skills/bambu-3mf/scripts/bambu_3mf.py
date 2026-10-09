"""Turn mesh files into Bambu Studio project 3MFs with printer, process and filament preset.

    python3 bambu_3mf.py part.stl --printer "Bambu Lab P2S 0.4 nozzle" \
        --process "0.16mm Standard @BBL P2S" --filament "Generic PETG @BBL P2S" \
        --set enable_support=0 --set sparse_infill_density=100% -o out.3mf

Bambu Studio's own CLI writes the project, so it opens without "invalid config,
load geometry data only". Standard library only.
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

CONFIG = os.path.expanduser("~/.config/BambuStudio")
KINDS = {"printer": "machine", "process": "process", "filament": "filament"}


def find_bambu(explicit):
    if explicit:
        return explicit
    if os.environ.get("BAMBU_STUDIO"):
        return os.environ["BAMBU_STUDIO"]
    for name in ("bambu-studio", "BambuStudio"):
        if shutil.which(name):
            return shutil.which(name)
    images = sorted(glob.glob(os.path.expanduser("~/bin/appimages/BambuStudio_*.AppImage"))
                    + glob.glob(os.path.expanduser("~/Applications/BambuStudio*.AppImage")))
    if images:
        return images[-1]
    sys.exit("Bambu Studio not found: pass --bambu PATH or set BAMBU_STUDIO")


def preset_dirs(kind):
    """System presets first, then the user's own (user/<id>/<kind>)."""
    return (glob.glob(os.path.join(CONFIG, "system", "*", kind))
            + glob.glob(os.path.join(CONFIG, "user", "*", kind)))


def load_preset(kind, name):
    for d in preset_dirs(kind):
        path = os.path.join(d, name + ".json")
        if os.path.exists(path):
            return json.load(open(path))
    label = {v: k for k, v in KINDS.items()}[kind]
    sys.exit("%s preset not found: %r (run with --list %s)" % (label, name, label))


def resolve(kind, name):
    """Presets inherit from a parent chain; the CLI wants them flattened."""
    d = load_preset(kind, name)
    parent = d.pop("inherits", "")
    if parent:
        base = resolve(kind, parent)
        base.update(d)
        d = base
    return d


def list_presets(kind, needle):
    names = set()
    for d in preset_dirs(KINDS[kind]):
        for f in glob.glob(os.path.join(d, "*.json")):
            data = json.load(open(f))
            if data.get("instantiation") == "true" or "/user/" in f:
                names.add(os.path.basename(f)[:-5])
    for n in sorted(names):
        if needle.lower() in n.lower():
            print(n)


def apply_overrides(preset, sets):
    for s in sets:
        key, _, value = s.partition("=")
        if key in preset and isinstance(preset[key], list):
            preset[key] = [value] * len(preset[key])   # per-extruder / per-filament values
        else:
            preset[key] = value
    return preset


def record_changes(out, process_keys, filament_keys):
    """List changed keys in different_settings_to_system ([process, filament, printer]).

    The GUI rebuilds each preset from the system one plus these keys; the CLI leaves the
    list empty, so without it the GUI slices with stock settings.
    """
    src = zipfile.ZipFile(out)
    items = {i: src.read(i) for i in src.namelist()}
    src.close()
    proj = json.loads(items["Metadata/project_settings.config"])
    proj["different_settings_to_system"] = [";".join(sorted(process_keys)),
                                            ";".join(sorted(filament_keys)), ""]
    items["Metadata/project_settings.config"] = json.dumps(proj, indent=4).encode()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in items.items():
            z.writestr(name, data)


def changed_keys(kind, name, sets):
    stock = resolve(kind, name)
    keys = []
    for s in sets:
        key, _, value = s.partition("=")
        cur = stock.get(key)
        cur = cur[0] if isinstance(cur, list) and cur else cur
        if str(cur) != value:
            keys.append(key)
    return keys


def check(out, expected):
    """Read the written project back and confirm the overrides landed."""
    cfg = json.loads(zipfile.ZipFile(out).read("Metadata/project_settings.config"))
    bad = []
    for key, value in expected.items():
        got = cfg.get(key)
        got = got[0] if isinstance(got, list) and got else got
        if str(got) != value:
            bad.append("%s=%r (wanted %r)" % (key, got, value))
    return cfg, bad


def main():
    ap = argparse.ArgumentParser(description="Write Bambu Studio project 3MFs from meshes.")
    ap.add_argument("meshes", nargs="*", help="STL/OBJ/STEP/3MF; each becomes its own 3MF unless --one")
    ap.add_argument("--printer", help='machine preset, e.g. "Bambu Lab P2S 0.4 nozzle"')
    ap.add_argument("--process", help='process preset, e.g. "0.16mm Standard @BBL P2S"')
    ap.add_argument("--filament", help='filament preset, e.g. "Generic PETG @BBL P2S"')
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override a process setting; repeatable")
    ap.add_argument("--set-filament", action="append", default=[], metavar="KEY=VALUE",
                    help="override a filament setting, e.g. nozzle_temperature=260")
    ap.add_argument("--orient", action="store_true", help="let Bambu auto-orient (default: keep the mesh as modelled)")
    ap.add_argument("--one", action="store_true", help="put all meshes on one plate in a single 3MF")
    ap.add_argument("-o", "--out", help="output 3MF (single mesh or --one) or directory")
    ap.add_argument("--bambu", help="Bambu Studio executable or AppImage")
    ap.add_argument("--list", choices=KINDS, help="list available presets of this kind and exit")
    ap.add_argument("--grep", default="", help="filter for --list")
    a = ap.parse_args()

    if a.list:
        return list_presets(a.list, a.grep)
    if not (a.meshes and a.printer and a.process and a.filament):
        ap.error("meshes, --printer, --process and --filament are required")

    bambu = find_bambu(a.bambu)
    tmp = tempfile.mkdtemp(prefix="bambu-3mf-")
    paths = {}
    for kind, name, sets in (("machine", a.printer, []), ("process", a.process, a.set),
                             ("filament", a.filament, a.set_filament)):
        paths[kind] = os.path.join(tmp, kind + ".json")
        json.dump(apply_overrides(resolve(kind, name), sets), open(paths[kind], "w"))

    proc_keys = changed_keys("process", a.process, a.set)
    fil_keys = changed_keys("filament", a.filament, a.set_filament)
    jobs = [a.meshes] if a.one else [[m] for m in a.meshes]
    expected = dict(s.partition("=")[::2] for s in a.set + a.set_filament)
    failed = False
    for meshes in jobs:
        if a.out and (len(jobs) == 1 and not os.path.isdir(a.out)):
            out = a.out
        else:
            out = os.path.join(a.out or os.path.dirname(meshes[0]) or ".",
                               os.path.splitext(os.path.basename(meshes[0]))[0] + ".3mf")
        cmd = [bambu, "--load-settings", "%s;%s" % (paths["machine"], paths["process"]),
               "--load-filaments", paths["filament"], "--orient", "1" if a.orient else "0",
               "--arrange", "1", "--export-3mf", os.path.abspath(out)] + [os.path.abspath(m) for m in meshes]
        # The CLI logs an OSMesa thumbnail error headless; the project is still complete.
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            print("FAILED %s\n%s" % (out, (r.stdout + r.stderr)[-2000:]), file=sys.stderr)
            failed = True
            continue
        record_changes(out, proc_keys, fil_keys)
        cfg, bad = check(out, expected)
        print("wrote %s  [%s | %s | %s]" % (out, cfg.get("printer_settings_id"),
                                           cfg.get("print_settings_id"), cfg.get("filament_settings_id")))
        for b in bad:
            print("  NOT APPLIED: " + b, file=sys.stderr)
            failed = True
    sys.exit(1 if failed else 0)


main()
