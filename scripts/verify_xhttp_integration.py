#!/usr/bin/env python3
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
    ),
}

ZIP_MEMBERS = {
    "classes3.dex",
    "assets/xhttp-runtime-notice.txt",
    "lib/arm64-v8a/libconscrypt_jni.so",
    "lib/armeabi-v7a/libconscrypt_jni.so",
}

DEX_MARKERS = (
    b"com/dtunnel/xhttp/XHttpLauncher",
    b"com/dragonssh/xhttpdemo/core/XHttpSshService",
    b"com/dragonssh/xhttpdemo/core/tunnel/XHttpProxy",
    b"SSH_XHTTP",
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


def verify_apk() -> list[str]:
    failures: list[str] = []
    if not BASE_APK.is_file():
        return [f"APK base ausente: {BASE_APK}"]

    with zipfile.ZipFile(BASE_APK) as apk:
        members = set(apk.namelist())
        for member in sorted(ZIP_MEMBERS):
            if member not in members:
                failures.append(f"membro APK ausente: {member}")

        dex_content = b"".join(apk.read(member) for member in sorted(members) if member.startswith("classes") and member.endswith(".dex"))
        for marker in DEX_MARKERS:
            if marker not in dex_content:
                failures.append(f"marcador DEX ausente: {marker.decode()}")
    return failures


def main() -> None:
    failures = verify_source() + verify_apk()
    if failures:
        print("Falha na verificação XHTTP:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        raise SystemExit(1)
    print("Verificação XHTTP concluída: painel, gerador e APK base estão alinhados.")


if __name__ == "__main__":
    main()
