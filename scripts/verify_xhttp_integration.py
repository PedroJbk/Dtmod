"""Static regression checks for the panel's embedded SSH_XHTTP runtime."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_APK = ROOT / "scripts/base.apk"

SOURCE_ASSERTIONS = {
    ROOT / "frontend/public/static/js/config/components/form.js": (
        "ConfigXhttpHost",
        "ConfigXhttpPath",
        "SSH_XHTTP",
        "'NONE'",
    ),
    ROOT / "src/routes/DTunnel/AppConfig/zod-schema.ts": (
        "'SSH_XHTTP'",
        "'NONE'",
    ),
    ROOT / "scripts/generate_apk.py": (
        "verify_xhttp_runtime",
        "XHttpLauncher;->start",
    ),
    ROOT / "scripts/xhttp-smali/XHttpLauncher.smali": (
        "xhttpPath",
        "xhttpHost",
        "xhttpTls",
        "XHttpSshService",
        "SharedPreferences$Editor;->commit()Z",
        "catch_xhttp_service_start",
    ),
    ROOT / "scripts/integrate_xhttp_base.py": (
        'android:process=\":xhttp\"',
        "xhttp_pdnsd_local",
        "copy_runtime_strings",
        "copy_runtime_drawables",
        "libsystem.so",
    ),
    ROOT / "scripts/xhttp-res/strings.xml": (
        "channel_name_background",
        "state_starting",
        "failedvpn",
    ),
    ROOT / "scripts/xhttp-res/drawable-anydpi-v21/ic_cloud_black_24dp.xml": (
        "<vector",
        "pathData",
    ),
    ROOT / "scripts/xhttp-res/drawable-anydpi-v21/ic_power_settings_new_black_24dp.xml": (
        "<vector",
        "pathData",
    ),
}

ZIP_MEMBERS = {
    "classes3.dex",
    "assets/xhttp-runtime-notice.txt",
    "lib/arm64-v8a/libconscrypt_jni.so",
    "lib/armeabi-v7a/libconscrypt_jni.so",
}

UNWANTED_ZIP_MEMBERS = {
    "lib/arm64-v8a/libsystem.so",
    "lib/armeabi-v7a/libsystem.so",
}

DEX_MARKERS = (
    b"com/dtunnel/xhttp/XHttpLauncher",
    b"com/dragonssh/xhttpdemo/core/XHttpSshService",
    b"com/dragonssh/xhttpdemo/core/tunnel/XHttpProxy",
    b"SSH_XHTTP",
)

APK_TEXT_MARKERS = (
    b":xhttp",
    b"xhttp_state_starting",
    b"xhttp_channel_name_background",
    b"xhttp_pdnsd_local",
)


def verify_source() -> list[str]:
    failures: list[str] = []
    for path, markers in SOURCE_ASSERTIONS.items():
        if not path.is_file():
            failures.append(f"arquivo ausente: {path.relative_to(ROOT)}")
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"marcador ausente em {path.relative_to(ROOT)}: {marker}")
    return failures


def contains_android_string(blob: bytes, marker: bytes) -> bool:
    """Match resource strings regardless of AAPT's UTF-8/UTF-16 pool encoding."""
    return marker in blob or marker.decode("utf-8").encode("utf-16le") in blob


def verify_apk() -> list[str]:
    failures: list[str] = []
    if not BASE_APK.is_file():
        return [f"APK base ausente: {BASE_APK}"]

    with zipfile.ZipFile(BASE_APK) as apk:
        members = set(apk.namelist())
        for member in sorted(ZIP_MEMBERS):
            if member not in members:
                failures.append(f"membro APK ausente: {member}")
        for member in sorted(UNWANTED_ZIP_MEMBERS):
            if member in members:
                failures.append(f"membro APK incompatível presente: {member}")

        dex_content = b"".join(apk.read(member) for member in sorted(members) if member.startswith("classes") and member.endswith(".dex"))
        for marker in DEX_MARKERS:
            if marker not in dex_content:
                failures.append(f"marcador DEX ausente: {marker.decode()}")

        apk_text = apk.read("AndroidManifest.xml") + apk.read("resources.arsc")
        for marker in APK_TEXT_MARKERS:
            if not contains_android_string(apk_text, marker):
                failures.append(f"marcador de manifesto/recurso ausente: {marker.decode()}")
    return failures


def main() -> None:
    failures = verify_source() + verify_apk()
    if failures:
        print("Falha na verificação XHTTP:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        raise SystemExit(1)
    print("Verificação XHTTP concluída: painel, recursos, isolamento e APK base estão alinhados.")


if __name__ == "__main__":
    main()
