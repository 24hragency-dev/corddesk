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
WEBSITE = cfg.get("website", "").strip().rstrip("/")
COPYRIGHT = f"Copyright (C) {COMPANY}. Based on RustDesk (AGPL-3.0)."
# AGPL: the About screen must keep crediting the original project. This exact
# text is protected from the RustDesk -> NAME rename below.
CREDIT = "Based on RustDesk"


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


# macOS app bundle name (RustDesk's mac code derives paths from the app name, so
# the bundle must be <NAME>.app with executable <NAME>).
def patch_xcconfig(t):
    t = re.sub(r'^PRODUCT_NAME\s*=.*$', f'PRODUCT_NAME = {NAME}', t, flags=re.M)
    return re.sub(r'^PRODUCT_COPYRIGHT\s*=.*$', f'PRODUCT_COPYRIGHT = {COPYRIGHT}', t, flags=re.M)


# --- Rename everywhere the user can see it -----------------------------------

def rename_lang(t):
    return t.replace("RustDesk", NAME)


DART_STRING = re.compile(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"")


def rename_dart_strings(t):
    """Rename RustDesk and rustdesk.com links inside Dart string literals only."""
    def fix(m):
        s = m.group(0)
        if "RustDesk" in s and not any(k in s for k in ("com.rustdesk", "RustDeskTerminal", CREDIT)):
            s = s.replace("RustDesk", NAME)
        if WEBSITE:
            s = re.sub(r"https?://(?:www\.)?rustdesk\.com[^'\"\s]*", WEBSITE, s)
            if s[1:-1] == "rustdesk.com":
                s = s[0] + WEBSITE.split("://")[-1] + s[-1]
        return s
    return DART_STRING.sub(fix, t)


def patches(pairs):
    """Exact text replacements; fails the build if the upstream code changed."""
    def fn(t):
        crlf = "\r\n" in t
        t = t.replace("\r\n", "\n")
        for old, new in pairs:
            if new in t:  # already applied (insertions still contain the old text)
                continue
            if old not in t:
                fail(f"UI patch target not found (RustDesk source changed): {old.strip()[:70]!r}")
            t = t.replace(old, new)
        return t.replace("\n", "\r\n") if crlf else t
    return fn


# --- New look: black & white theme ------------------------------------------

THEME_PATCHES = [
    ("static const Color grayBg = Color(0xFFEFEFF2);", "static const Color grayBg = Color(0xFFF4F4F5);"),
    ("static const Color accent = Color(0xFF0071FF);", "static const Color accent = Color(0xFF111111);"),
    ("static const Color accent50 = Color(0x770071FF);", "static const Color accent50 = Color(0x77111111);"),
    ("static const Color accent80 = Color(0xAA0071FF);", "static const Color accent80 = Color(0xAA111111);"),
    ("static const Color idColor = Color(0xFF00B6F0);", "static const Color idColor = Color(0xFF111111);"),
    ("static const Color button = Color(0xFF2C8CFF);", "static const Color button = Color(0xFF111111);"),
    ("primary: Colors.blue, secondary: accent, background: grayBg),",
     "primary: Color(0xFF111111), secondary: accent, background: grayBg),"),
    ("""    colorScheme: ColorScheme.dark(
      primary: Colors.blue,
      secondary: accent,""",
     """    colorScheme: ColorScheme.dark(
      primary: Colors.white,
      secondary: Colors.white,"""),
    ("""        backgroundColor: MyTheme.accent,
        foregroundColor: Colors.white,
        disabledForegroundColor: Colors.white70,""",
     """        backgroundColor: Colors.white,
        foregroundColor: Color(0xFF111111),
        disabledForegroundColor: Colors.white70,"""),
    ("""        fontWeight: FontWeight.bold,
        color: accent80,""",
     """        fontWeight: FontWeight.bold,
        color: Colors.white70,"""),
]

# --- New home layout: dark icon rail + ID/password card + connect area -------

HOME_PATCHES = [
    ("const borderColor = Color(0xFF2F65BA);", "const borderColor = Color(0xFF111111);"),
    ("""      children: [
        buildLeftPane(context),
        if (!isIncomingOnly) const VerticalDivider(width: 1),
        if (!isIncomingOnly) Expanded(child: buildRightPane(context)),
      ],""",
     """      children: [
        if (!isIncomingOnly) _buildCordRail(context),
        if (isIncomingOnly) buildLeftPane(context),
        if (!isIncomingOnly)
          Container(
            margin: const EdgeInsets.fromLTRB(16, 16, 4, 16),
            clipBehavior: Clip.antiAlias,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.background,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Theme.of(context).dividerColor),
            ),
            child: buildLeftPane(context),
          ),
        if (!isIncomingOnly) Expanded(child: buildRightPane(context)),
      ],"""),
    ("""  Widget _buildBlock({required Widget child}) {""",
     """  Widget _buildCordRail(BuildContext context) {
    Widget item(IconData icon, String tip, VoidCallback onTap,
        {bool selected = false}) {
      return Tooltip(
        message: translate(tip),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: selected
                  ? Colors.white.withOpacity(0.14)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon,
                color: selected ? Colors.white : Colors.white60, size: 22),
          ),
        ),
      ).marginOnly(bottom: 8);
    }

    return Container(
      width: 68,
      color: const Color(0xFF0B0B0C),
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Column(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: loadIcon(40),
          ).marginOnly(bottom: 22),
          item(Icons.home_rounded, 'Home', () {}, selected: true),
          if (!bind.isDisableSettings())
            item(Icons.settings_rounded, 'Settings',
                () => DesktopTabPage.onAddSetting()),
          const Spacer(),
          if (!bind.isDisableSettings())
            item(
                Icons.info_outline_rounded,
                'About',
                () => DesktopTabPage.onAddSetting(
                    initialPage: SettingsTabKey.about)),
        ],
      ),
    );
  }

  Widget _buildBlock({required Widget child}) {"""),
    ("""      Align(
        alignment: Alignment.center,
        child: loadLogo(),
      ),
      buildTip(context),""",
     """      if (isIncomingOnly)
        Align(
          alignment: Alignment.center,
          child: loadLogo(),
        ),
      buildTip(context),"""),
    ("width: isIncomingOnly ? 280.0 : 200.0,", "width: isIncomingOnly ? 280.0 : 240.0,"),
]

CONNECT_PATCHES = [
    ("""          borderRadius: const BorderRadius.all(Radius.circular(13)),
          border: Border.all(color: Theme.of(context).colorScheme.background)),""",
     """          borderRadius: const BorderRadius.all(Radius.circular(16)),
          border: Border.all(color: Theme.of(context).dividerColor)),"""),
]

ABOUT_PATCHES = [
    ("decoration: const BoxDecoration(color: Color(0xFF2c8cff)),",
     "decoration: const BoxDecoration(color: Color(0xFF111111)),"),
    # \x24 is "$" (Dart string interpolation)
    ("'Copyright © \x24{DateTime.now().toString().substring(0, 4)} Purslane Tech Pte. Ltd.\\n$license',",
     "'" + NAME + " © \x24{DateTime.now().toString().substring(0, 4)} " + COMPANY + ".\\n"
     + CREDIT + " - Copyright © Purslane Tech Pte. Ltd.\\n$license',"),
]


def rebrand_ui():
    edit("flutter/lib/common.dart", patches(THEME_PATCHES), required=True)
    edit("flutter/lib/desktop/pages/desktop_home_page.dart", patches(HOME_PATCHES), required=True)
    edit("flutter/lib/desktop/pages/connection_page.dart", patches(CONNECT_PATCHES), required=True)
    edit("flutter/lib/desktop/pages/desktop_setting_page.dart", patches(ABOUT_PATCHES), required=True)
    n = 0
    for p in sorted((ROOT / "flutter/lib").rglob("*.dart")):
        text, enc = read(p)
        new = rename_dart_strings(text)
        if new != text:
            p.write_bytes(new.encode(enc, errors="surrogateescape"))
            n += 1
    log(f"renamed strings/links in {n} dart files")
    n = 0
    for p in sorted((ROOT / "src/lang").glob("*.rs")):
        text, enc = read(p)
        new = rename_lang(text)
        if new != text:
            p.write_bytes(new.encode(enc, errors="surrogateescape"))
            n += 1
    log(f"renamed RustDesk in {n} translation files")


# --- Icons -------------------------------------------------------------------

ICON_NAMES = {
    "icon.ico", "icon.png", "icon.svg", "logo.png", "logo.svg", "tray-icon.ico",
    "app_icon.ico", "32x32.png", "64x64.png", "128x128.png", "128x128@2x.png",
    "mac-icon.png", "AppIcon.icns",
}
ICON_DIRS = ["res", "flutter/assets", "flutter/windows/runner/resources", "flutter/macos/Runner",
             "libs/portable"]


def load_pillow():
    try:
        from PIL import Image
    except ImportError:
        pip = [sys.executable, "-m", "pip", "install", "--quiet", "pillow"]
        if subprocess.call(pip, stdout=sys.stderr) != 0:
            # Homebrew Python on macOS runners refuses system-wide installs (PEP 668)
            import site
            subprocess.check_call(pip + ["--user", "--break-system-packages"], stdout=sys.stderr)
            site.addsitedir(site.getusersitepackages())
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
        elif ext == ".icns":
            src.save(p, format="ICNS")
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
    edit("flutter/macos/Runner/Configs/AppInfo.xcconfig", patch_xcconfig)
    rebrand_ui()
    replace_icons()
    log("done")


if __name__ == "__main__":
    main()
