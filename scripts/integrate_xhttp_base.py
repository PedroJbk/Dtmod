#!/usr/bin/env python3
"""Integrate the GPLv3 XHTTP runtime into a decoded DTunnel base APK.

The script intentionally performs static source/resource assembly only. It stages the
reference XHTTP class graph, adds a small launcher that maps the remote panel profile
to the XHTTP runtime settings, adds the required Android components, and normalizes
reference resource IDs to valid resources in the DTunnel base.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
REFERENCE_URL = "https://git.dr2.site/penguinehis/SocksRevive-XHTTP-DEMO"


def require(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def replace_once(path: Path, old: str, new: str, description: str) -> None:
    content = path.read_text(encoding="utf-8")
    if new in content:
        return
    if old not in content:
        raise RuntimeError(f"Could not patch {description}: marker not found in {path}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def stage_runtime(reference: Path, base: Path) -> None:
    report = SCRIPT_DIR / "xhttp-core-report.json"
    command = [
        sys.executable,
        str(SCRIPT_DIR / "stage_xhttp_core.py"),
        "--reference",
        str(reference),
        "--base",
        str(base),
        "--report",
        str(report),
    ]
    subprocess.run(command, check=True)


def install_launcher(base: Path) -> None:
    target = base / "smali_classes3/com/dtunnel/xhttp/XHttpLauncher.smali"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT_DIR / "xhttp-smali/XHttpLauncher.smali", target)


def patch_service_manager(base: Path) -> None:
    manager = base / "smali/com/ssh/service/SshVpnServiceManager.smali"
    require(manager)
    marker = """    iget-object v7, v1, Lg4/e;->D:Ljava/lang/String;\n\n    .line 19\n    const-string v8, \"SSH_DIRECT\""""
    replacement = """    iget-object v7, v1, Lg4/e;->D:Ljava/lang/String;\n\n    # SSH_XHTTP is handled by the embedded XHTTP runtime instead of the legacy SSH transport.\n    const-string v8, \"SSH_XHTTP\"\n\n    invoke-static {v7, v8}, Lpb/j;->a(Ljava/lang/Object;Ljava/lang/Object;)Z\n\n    move-result v8\n\n    if-eqz v8, :cond_xhttp_continue\n\n    invoke-static {v0, v1}, Lcom/dtunnel/xhttp/XHttpLauncher;->start(Landroid/content/Context;Lg4/e;)V\n\n    return-void\n\n    :cond_xhttp_continue\n    .line 19\n    const-string v8, \"SSH_DIRECT\""""
    replace_once(manager, marker, replacement, "SSH_XHTTP dispatcher")


def patch_manifest(base: Path) -> None:
    manifest = base / "AndroidManifest.xml"
    require(manifest)
    text = manifest.read_text(encoding="utf-8")

    permission = '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC"/>'
    if permission not in text:
        marker = '<uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>'
        if marker not in text:
            raise RuntimeError("Could not find foreground-service permission marker")
        text = text.replace(marker, marker + "\n    " + permission, 1)

    components = """        <receiver android:exported=\"false\" android:name=\"com.dragonssh.xhttpdemo.core.MainReceiver\"/>\n        <service android:exported=\"false\" android:foregroundServiceType=\"dataSync\" android:name=\"com.dragonssh.xhttpdemo.core.XHttpSshService\" android:stopWithTask=\"false\"/>\n        <service android:enabled=\"true\" android:exported=\"false\" android:name=\"com.dragonssh.xhttpdemo.core.tunnel.vpn.TunnelVpnService\" android:permission=\"android.permission.BIND_VPN_SERVICE\">\n            <intent-filter>\n                <action android:name=\"android.net.VpnService\"/>\n            </intent-filter>\n        </service>\n"""
    if "com.dragonssh.xhttpdemo.core.XHttpSshService" not in text:
        marker = "    </application>"
        if marker not in text:
            raise RuntimeError("Could not find application closing tag")
        text = text.replace(marker, components + marker, 1)

    manifest.write_text(text, encoding="utf-8")


def patch_resources(reference: Path, base: Path) -> None:
    raw_source = reference / "res/raw/pdnsd_local"
    raw_target = base / "res/raw/pdnsd_local"
    require(raw_source)
    raw_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw_source, raw_target)

    public_xml = base / "res/values/public.xml"
    require(public_xml)
    public = public_xml.read_text(encoding="utf-8")
    public_entry = '    <public type="raw" name="pdnsd_local" id="0x7f0e0004" />'
    if public_entry not in public:
        raw_marker = '    <public type="raw" name="firebase_crashlytics_keep" id="0x7f0e0003" />'
        if raw_marker not in public:
            raise RuntimeError("Could not find raw resource marker")
        public = public.replace(raw_marker, raw_marker + "\n" + public_entry, 1)
        public_xml.write_text(public, encoding="utf-8")

    runtime_root = base / "smali_classes3/com/dragonssh/xhttpdemo/core"
    raw_r = runtime_root / "R$raw.smali"
    drawable_r = runtime_root / "R$drawable.smali"
    strings_r = runtime_root / "R$string.smali"
    for path in (raw_r, drawable_r, strings_r):
        require(path)

    raw_text = raw_r.read_text(encoding="utf-8")
    raw_text = re.sub(r"(pdnsd_local:I = )0x[0-9a-fA-F]+", r"\g<1>0x7f0e0004", raw_text)
    raw_r.write_text(raw_text, encoding="utf-8")

    drawable_text = drawable_r.read_text(encoding="utf-8")
    drawable_text = re.sub(r"(:I = )0x[0-9a-fA-F]+", r"\g<1>0x7f08008b", drawable_text)
    drawable_r.write_text(drawable_text, encoding="utf-8")

    string_text = strings_r.read_text(encoding="utf-8")
    string_text = re.sub(r"(:I = )0x[0-9a-fA-F]+", r"\g<1>0x7f0f001d", string_text)
    strings_r.write_text(string_text, encoding="utf-8")


def copy_native_libraries(reference: Path, base: Path) -> None:
    for abi in ("arm64-v8a", "armeabi-v7a"):
        source_dir = reference / "lib" / abi
        target_dir = base / "lib" / abi
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in ("libconscrypt_jni.so", "libsystem.so"):
            source = source_dir / name
            require(source)
            shutil.copy2(source, target_dir / name)


def write_notice(base: Path) -> None:
    notice = base / "assets/xhttp-runtime-notice.txt"
    notice.parent.mkdir(parents=True, exist_ok=True)
    notice.write_text(
        "This APK embeds the XHTTP runtime derived from SocksRevive-XHTTP-DEMO.\n"
        f"Source: {REFERENCE_URL}\n"
        "License: GNU General Public License v3.0 or later.\n"
        "Corresponding integration source is distributed with the panel repository under scripts/.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True, help="Decoded reference APK root")
    parser.add_argument("--base", type=Path, required=True, help="Decoded DTunnel base APK root")
    args = parser.parse_args()

    require(args.reference)
    require(args.base)
    stage_runtime(args.reference, args.base)
    install_launcher(args.base)
    patch_service_manager(args.base)
    patch_manifest(args.base)
    patch_resources(args.reference, args.base)
    copy_native_libraries(args.reference, args.base)
    write_notice(args.base)
    print("XHTTP runtime integration staged successfully")


if __name__ == "__main__":
    main()
