#!/usr/bin/env python3
"""CordDesk branding.

Rewrites the app name, built-in server, server key and icons in the RustDesk
source tree right before it is compiled. It is called from the top of build.py,
so it runs on GitHub's build machine (after git submodules are checked out).
Safe to run more than once.
"""
import base64
import io
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

cfg = json.loads((HERE / "branding.json").read_text(encoding="utf-8"))
NAME = cfg["app_name"].strip()
COMPANY = cfg["company"].strip()
SERVER = cfg["server"].strip()
KEY = cfg["public_key"].strip()
COPYRIGHT = f"Copyright (C) {COMPANY}. Based on RustDesk (AGPL-3.0)."


# Log to stderr only: CI runs "build.py --print-features" and captures stdout.
def log(msg):
    print(f"[corddesk] {msg}", file=sys.stderr, flush=True)


def fail(msg):
    print(f"[corddesk] ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


if not SERVER or SERVER.startswith("PUT_"):
    fail("Put your server IP/domain in branding/branding.json")
if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", KEY):
    fail("public_key in branding/branding.json must be the 44-character key from id_ed25519.pub")


def read(path):
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        enc = "utf-16"
    elif raw.startswith(b"\xef\xbb\xbf"):
        enc = "utf-8-sig"
    else:
        enc = "utf-8"
    return raw.decode(enc, errors="surrogateescape"), enc


def edit(rel, fn, required=False):
    path = ROOT / rel
    if not path.exists():
        if required:
            fail(f"missing {rel} - RustDesk source layout changed")
        log(f"skip (not found) {rel}")
        return
    text, enc = read(path)
    new = fn(text)
    if new != text:
        path.write_bytes(new.encode(enc, errors="surrogateescape"))
        log(f"patched {rel}")
    else:
        log(f"unchanged {rel}")


# --- Server, key and app name (hbb_common submodule) ------------------------

def patch_config(t):
    t, n_server = re.subn(
        r'(RENDEZVOUS_SERVERS\s*:\s*&\[&str\]\s*=\s*&\[)[^\]]*(\])',
        lambda m: f'{m[1]}"{SERVER}"{m[2]}', t)
    t, n_key = re.subn(
        r'(RS_PUB_KEY\b[^;]*?")[A-Za-z0-9+/]{43}=(")',
        lambda m: f"{m[1]}{KEY}{m[2]}", t, flags=re.S)
    t, n_name = re.subn(
        r'(APP_NAME\s*:\s*RwLock<String>\s*=\s*RwLock::new\(\s*")[^"]*(")',
        lambda m: f"{m[1]}{NAME}{m[2]}", t)
    for count, what in ((n_server, "server list"), (n_key, "public key"), (n_name, "app name")):
        if not count:
            fail(f"could not find the {what} in config.rs - RustDesk source layout changed")
    return t


# --- Windows file properties (name / company shown in Properties > Details) --

def fix_value(key, val):
    if key == "CompanyName":
        return COMPANY
    if key == "LegalCopyright":
        return COPYRIGHT
    if key in ("ProductName", "FileDescription", "InternalName", "OriginalFilename"):
        return re.sub("rustdesk", NAME, val, flags=re.I)
    return val


def patch_rc(t):
    return re.sub(r'VALUE\s+"(\w+)"\s*,\s*"([^"]*)"',
                  lambda m: f'VALUE "{m[1]}", "{fix_value(m[1], m[2])}"', t)


def patch_cargo(t):
    return re.sub(r'^(ProductName|FileDescription|CompanyName|LegalCopyright|InternalName|OriginalFilename)\s*=\s*"([^"]*)"',
                  lambda m: f'{m[1]} = "{fix_value(m[1], m[2])}"', t, flags=re.M)


def patch_cpp(t):
    return t.replace('L"RustDesk"', f'L"{NAME}"')


# --- Icons -------------------------------------------------------------------

ICON_NAMES = {
    "icon.ico", "icon.png", "icon.svg", "logo.png", "logo.svg", "tray-icon.ico",
    "app_icon.ico", "32x32.png", "64x64.png", "128x128.png", "128x128@2x.png",
}
ICON_DIRS = ["res", "flutter/assets", "flutter/windows/runner/resources", "libs/portable"]


def load_pillow():
    try:
        from PIL import Image
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "pillow"],
                              stdout=sys.stderr)
        from PIL import Image
    return Image


def fit(Image, src, size):
    """Scale the square icon into a canvas of the given size, centered, keeping its shape."""
    w, h = size
    side = min(w, h)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(src.resize((side, side), Image.LANCZOS), ((w - side) // 2, (h - side) // 2))
    return canvas


FONT_CANDIDATES = [
    r"C:\Windows\Fonts\consolab.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/System/Library/Fonts/Menlo.ttc",
]


def draw_icon(Image, size=1024):
    """Draw the CordDesk icon: white bold "<or/>" on a black rounded square."""
    from PIL import ImageDraw, ImageFont
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.11), fill=(0, 0, 0, 255))
    font_path = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)
    text = "<or/>"

    def font(px):
        return ImageFont.truetype(font_path, px) if font_path else ImageFont.load_default(size=px)

    left, _, right, _ = d.textbbox((0, 0), text, font=font(400))
    f = font(int(400 * size * 0.82 / (right - left)))
    left, top, right, bottom = d.textbbox((0, 0), text, font=f)
    d.text(((size - (right - left)) / 2 - left, (size - (bottom - top)) / 2 - top), text, font=f, fill=(255, 255, 255, 255))
    return img


def replace_icons():
    Image = load_pillow()
    icon_file = HERE / "icon.png"
    src = Image.open(icon_file).convert("RGBA") if icon_file.exists() else draw_icon(Image)
    found = []
    for d in ICON_DIRS:
        base = ROOT / d
        if base.exists():
            found += [p for p in base.rglob("*")
                      if p.name in ICON_NAMES and "build" not in p.relative_to(ROOT).parts]
    for p in found:
        ext = p.suffix.lower()
        if ext == ".png":
            with Image.open(p) as old:
                size = old.size
            fit(Image, src, size).save(p)
        elif ext == ".ico":
            src.save(p, format="ICO", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
        elif ext == ".svg":
            buf = io.BytesIO()
            src.resize((256, 256), Image.LANCZOS).save(buf, "PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            p.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                'width="256" height="256" viewBox="0 0 256 256">'
                f'<image width="256" height="256" xlink:href="data:image/png;base64,{b64}"/></svg>\n',
                encoding="utf-8")
        log(f"icon replaced {p.relative_to(ROOT).as_posix()}")
    if not found:
        log("WARNING: no icon files found to replace")


def main():
    log(f"branding as {NAME}, server {SERVER}")
    edit("libs/hbb_common/src/config.rs", patch_config, required=True)
    edit("flutter/windows/runner/Runner.rc", patch_rc)
    edit("flutter/windows/runner/main.cpp", patch_cpp)
    edit("Cargo.toml", patch_cargo)
    edit("libs/portable/Cargo.toml", patch_cargo)
    replace_icons()
    log("done")


if __name__ == "__main__":
    main()
