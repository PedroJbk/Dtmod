"""Integrate the GPLv3 XHTTP runtime into a decoded DTunnel base APK.

The integration is intentionally static and reproducible. It stages the XHTTP class
closure, installs an adapter for panel profiles, gives the runtime its own resource
IDs, and runs all XHTTP Android components in a dedicated application process.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
RESOURCE_DIR = SCRIPT_DIR / "xhttp-res"
REFERENCE_URL = "https://git.dr2.site/penguinehis/SocksRevive-XHTTP-DEMO"
PUBLIC_RE = re.compile(
    r'<public\s+type="(?P<type>[^"]+)"\s+name="(?P<name>[^"]+)"\s+id="(?P<id>0x[0-9a-fA-F]+)"\s*/>'
)
FIELD_RE = re.compile(r"(\.field public static final (?P<name>[A-Za-z0-9_$]+):I = )0x[0-9a-fA-F]+")


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


def normalize_apktool_metadata(base: Path) -> None:
    """Make decoded metadata accepted by Apktool 3.x.

    Apktool 2.x may serialize numeric package and version fields as quoted YAML
    scalars. Apktool 3.x parses selected fields strictly as integers when building.
    """
    metadata = base / "apktool.yml"
    if not metadata.exists():
        return
    text = metadata.read_text(encoding="utf-8")
    for field in ("forcedPackageId", "minSdkVersion", "targetSdkVersion", "versionCode"):
        text = re.sub(
            rf"^(\s*{field}:\s*)'(\d+)'\s*$",
            r"\1\2",
            text,
            flags=re.MULTILINE,
        )
    metadata.write_text(text, encoding="utf-8")


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

    components = """        <receiver android:exported=\"false\" android:name=\"com.dragonssh.xhttpdemo.core.MainReceiver\" android:process=\":xhttp\"/>\n        <service android:exported=\"false\" android:foregroundServiceType=\"dataSync\" android:name=\"com.dragonssh.xhttpdemo.core.XHttpSshService\" android:process=\":xhttp\" android:stopWithTask=\"false\"/>\n        <service android:enabled=\"true\" android:exported=\"false\" android:name=\"com.dragonssh.xhttpdemo.core.tunnel.vpn.TunnelVpnService\" android:permission=\"android.permission.BIND_VPN_SERVICE\" android:process=\":xhttp\">\n            <intent-filter>\n                <action android:name=\"android.net.VpnService\"/>\n            </intent-filter>\n        </service>\n"""
    if "com.dragonssh.xhttpdemo.core.XHttpSshService" not in text:
        marker = "    </application>"
        if marker not in text:
            raise RuntimeError("Could not find application closing tag")
        text = text.replace(marker, components + marker, 1)
    else:
        # Upgrade a base created by an older integration in place.
        text = re.sub(
            r'(<receiver\s+android:exported="false"\s+android:name="com\.dragonssh\.xhttpdemo\.core\.MainReceiver")(\s*/>)',
            r'\1 android:process=":xhttp"\2',
            text,
        )
        text = re.sub(
            r'(<service\s+android:exported="false"\s+android:foregroundServiceType="dataSync"\s+android:name="com\.dragonssh\.xhttpdemo\.core\.XHttpSshService")(\s+android:stopWithTask="false"\s*/>)',
            r'\1 android:process=":xhttp"\2',
            text,
        )
        text = re.sub(
            r'(<service\s+android:enabled="true"\s+android:exported="false"\s+android:name="com\.dragonssh\.xhttpdemo\.core\.tunnel\.vpn\.TunnelVpnService"\s+android:permission="android\.permission\.BIND_VPN_SERVICE")(>)',
            r'\1 android:process=":xhttp"\2',
            text,
        )

    manifest.write_text(text, encoding="utf-8")


def parse_public_resources(public_text: str) -> dict[tuple[str, str], int]:
    return {
        (match.group("type"), match.group("name")): int(match.group("id"), 16)
        for match in PUBLIC_RE.finditer(public_text)
    }


def allocate_public_id(resources: dict[tuple[str, str], int], resource_type: str) -> int:
    ids = [resource_id for (kind, _), resource_id in resources.items() if kind == resource_type]
    if not ids:
        raise RuntimeError(f"No existing public resource type found for {resource_type}")
    prefix = ids[0] & 0xFFFF0000
    if any((resource_id & 0xFFFF0000) != prefix for resource_id in ids):
        raise RuntimeError(f"Inconsistent public resource IDs for {resource_type}")
    next_entry = max(resource_id & 0xFFFF for resource_id in ids) + 1
    if next_entry > 0xFFFF:
        raise RuntimeError(f"No public resource IDs remaining for {resource_type}")
    return prefix | next_entry


def ensure_public_resources(base: Path, names: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
    public_xml = base / "res/values/public.xml"
    require(public_xml)
    public_text = public_xml.read_text(encoding="utf-8")
    resources = parse_public_resources(public_text)
    additions: list[str] = []
    for resource_type, name in names:
        key = (resource_type, name)
        if key not in resources:
            resource_id = allocate_public_id(resources, resource_type)
            resources[key] = resource_id
            additions.append(
                f'    <public type="{resource_type}" name="{name}" id="0x{resource_id:08x}" />'
            )
    if additions:
        marker = "</resources>"
        if marker not in public_text:
            raise RuntimeError("Could not find the end of public.xml")
        public_text = public_text.replace(marker, "\n" + "\n".join(additions) + "\n" + marker, 1)
        public_xml.write_text(public_text, encoding="utf-8")
    return resources


def copy_runtime_strings(base: Path) -> dict[str, str]:
    source = RESOURCE_DIR / "strings.xml"
    require(source)
    tree = ET.parse(source)
    source_root = tree.getroot()
    target_root = ET.Element("resources")
    mapping: dict[str, str] = {"app_name": "app_name"}
    for child in source_root:
        name = child.attrib.get("name")
        if child.tag != "string" or not name:
            raise RuntimeError(f"Unexpected XHTTP string resource: {ET.tostring(child, encoding='unicode')}")
        if name == "app_name":
            continue
        target_name = f"xhttp_{name}"
        mapping[name] = target_name
        child.attrib["name"] = target_name
        target_root.append(child)
    output = base / "res/values/xhttp_runtime_strings.xml"
    ET.indent(target_root, space="    ")
    ET.ElementTree(target_root).write(output, encoding="utf-8", xml_declaration=True)
    return mapping


def copy_runtime_drawables(base: Path) -> dict[str, str]:
    source_dir = RESOURCE_DIR / "drawable-anydpi-v21"
    require(source_dir)
    target_dir = base / "res/drawable-anydpi-v21"
    target_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    for source in sorted(source_dir.glob("*.xml")):
        target_name = f"xhttp_{source.name}"
        shutil.copy2(source, target_dir / target_name)
        mapping[source.stem] = Path(target_name).stem
    expected = {"ic_cloud_black_24dp", "ic_power_settings_new_black_24dp"}
    if set(mapping) != expected:
        raise RuntimeError("The versioned XHTTP drawable set is incomplete")
    return mapping


def remap_r_fields(path: Path, ids: dict[str, int]) -> None:
    require(path)
    text = path.read_text(encoding="utf-8")
    found = set(FIELD_RE.findall(text))
    names = {name for _, name in found}
    missing = names - set(ids)
    if missing:
        raise RuntimeError(f"Unmapped resource fields in {path}: {', '.join(sorted(missing))}")

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        return f"{match.group(1)}0x{ids[name]:08x}"

    path.write_text(FIELD_RE.sub(replace, text), encoding="utf-8")


def patch_resources(reference: Path, base: Path) -> None:
    raw_source = reference / "res/raw/pdnsd_local"
    require(raw_source)
    raw_target = base / "res/raw/xhttp_pdnsd_local"
    raw_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw_source, raw_target)

    string_names = copy_runtime_strings(base)
    drawable_names = copy_runtime_drawables(base)
    resource_names: list[tuple[str, str]] = [("raw", "xhttp_pdnsd_local")]
    resource_names.extend(("string", target) for target in string_names.values() if target != "app_name")
    resource_names.extend(("drawable", target) for target in drawable_names.values())
    resources = ensure_public_resources(base, resource_names)

    runtime_root = base / "smali_classes3/com/dragonssh/xhttpdemo/core"
    raw_ids = {"pdnsd_local": resources[("raw", "xhttp_pdnsd_local")]}
    drawable_ids = {name: resources[("drawable", target)] for name, target in drawable_names.items()}
    string_ids = {name: resources[("string", target)] for name, target in string_names.items()}
    # app_name intentionally keeps the host application's branding.
    if "app_name" in string_names:
        string_ids["app_name"] = resources[("string", "app_name")]

    remap_r_fields(runtime_root / "R$raw.smali", raw_ids)
    remap_r_fields(runtime_root / "R$drawable.smali", drawable_ids)
    remap_r_fields(runtime_root / "R$string.smali", string_ids)


def copy_native_libraries(reference: Path, base: Path) -> None:
    for abi in ("arm64-v8a", "armeabi-v7a"):
        source = reference / "lib" / abi / "libconscrypt_jni.so"
        require(source)
        target_dir = base / "lib" / abi
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_dir / source.name)
        # libsystem.so is not referenced by the staged runtime. Older integrations
        # copied it gratuitously into the application process, increasing native
        # crash surface without any consumer.
        stale = target_dir / "libsystem.so"
        if stale.exists():
            stale.unlink()


def write_notice(base: Path) -> None:
    notice = base / "assets/xhttp-runtime-notice.txt"
    notice.parent.mkdir(parents=True, exist_ok=True)
    notice.write_text(
        "This APK embeds the XHTTP runtime derived from SocksRevive-XHTTP-DEMO.\n"
        f"Source: {REFERENCE_URL}\n"
        "License: GNU General Public License v3.0 or later.\n"
        "The runtime is installed in the :xhttp process and its integration source is\n"
        "distributed with the panel repository under scripts/.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True, help="Decoded reference APK root")
    parser.add_argument("--base", type=Path, required=True, help="Decoded DTunnel base APK root")
    args = parser.parse_args()

    require(args.reference)
    require(args.base)
    normalize_apktool_metadata(args.base)
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
