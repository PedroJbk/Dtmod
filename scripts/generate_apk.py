#!/usr/bin/env python3
"""Generate a branded DTunnel APK from the integrated XHTTP base.

The generator changes the panel endpoint domains in Smali files and updates the
``assets/dtunnelmod.json`` so the app points to the correct panel URL. The XHTTP
transport itself is part of ``base.apk`` and is verified after decoding, preventing
a generated APK from silently accepting a profile mode without carrying the
corresponding runtime.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import shlex
import subprocess
import sys
from pathlib import Path

APKTOOL = os.environ.get("APKTOOL_BIN", "apktool")
SIGNER_JAR = Path(os.environ.get("UBER_APK_SIGNER_JAR", "/usr/local/bin/uber-apk-signer.jar"))

OLD_DOMAINS = (
    "device.dtunnel.com.br",
    "text.dtunnel.com.br",
    "config.dtunnel.com.br",
    "app.dtunnel.com.br",
)

RUNTIME_FILES = (
    "smali_classes3/com/dtunnel/xhttp/XHttpLauncher.smali",
    "smali_classes3/com/dragonssh/xhttpdemo/core/tunnel/XHttpProxy.smali",
    "smali_classes3/com/dragonssh/xhttpdemo/core/XHttpSshService.smali",
)


def run_command(command: list[str], *, cwd: Path | None = None) -> None:
    print(f"Executando: {shlex.join(command)}")
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
        raise RuntimeError(f"Comando falhou com código {completed.returncode}")


def normalize_domain(value: str) -> str:
    """Normaliza o domínio do painel, aceitando host:porta ou apenas host."""
    domain = value.strip()
    domain = re.sub(r"^https?://", "", domain, flags=re.IGNORECASE).strip("/")
    # Aceitar host:porta (ex: meudominio.com:3000) ou apenas host
    host_part = domain.split(":")[0]
    if not re.fullmatch(r"[A-Za-z0-9.-]+", host_part) or "." not in host_part:
        raise ValueError("Informe somente um domínio válido, sem protocolo ou caminho. Porta é opcional (ex: meudominio.com:3000).")
    return domain


def verify_xhttp_runtime(work_dir: Path) -> None:
    missing = [str(path) for path in RUNTIME_FILES if not (work_dir / path).is_file()]
    manager = work_dir / "smali/com/ssh/service/SshVpnServiceManager.smali"
    dispatch_present = manager.is_file() and "XHttpLauncher;->start" in manager.read_text(encoding="utf-8")

    if missing or not dispatch_present:
        details = []
        if missing:
            details.append("arquivos ausentes: " + ", ".join(missing))
        if not dispatch_present:
            details.append("ponte de despacho SSH_XHTTP ausente")
        raise RuntimeError(
            "A APK base não contém o runtime XHTTP integrado (" + "; ".join(details) + "). "
            "Atualize scripts/base.apk com a base XHTTP fornecida pelo repositório."
        )


def replace_domains(work_dir: Path, new_domain: str) -> int:
    """Substitui os domínios antigos pelo novo domínio nos arquivos Smali."""
    # Para substituição nos Smali, usar apenas o host sem porta
    new_host = new_domain.split(":")[0]
    replacements = 0
    for smali_file in work_dir.glob("smali*/**/*.smali"):
        content = smali_file.read_text(encoding="utf-8")
        updated = content
        for old_domain in OLD_DOMAINS:
            updated = updated.replace(old_domain, new_host)
        if updated != content:
            smali_file.write_text(updated, encoding="utf-8")
            replacements += 1
    return replacements


def update_dtunnelmod_json(work_dir: Path, new_domain: str) -> None:
    """Atualiza o assets/dtunnelmod.json com a URL do painel do usuário."""
    dtunnelmod_json = work_dir / "assets" / "dtunnelmod.json"
    if not dtunnelmod_json.is_file():
        print("Aviso: assets/dtunnelmod.json não encontrado, pulando atualização.")
        return

    try:
        data = json.loads(dtunnelmod_json.read_text(encoding="utf-8"))
        # Construir URL completa com protocolo
        new_url = f"https://{new_domain}"
        data["url"] = new_url
        dtunnelmod_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"dtunnelmod.json atualizado: url = {new_url}")
    except Exception as e:
        print(f"Aviso: não foi possível atualizar dtunnelmod.json: {e}")


def fix_target_sdk_version(work_dir: Path) -> None:
    """Preserva o targetSdkVersion original da APK."""
    pass


def fix_foreground_service_type(work_dir: Path) -> None:
    """Garante que foregroundServiceType=dataSync está declarado corretamente no manifest."""
    manifest = work_dir / "AndroidManifest.xml"
    if not manifest.is_file():
        return

    content = manifest.read_text(encoding="utf-8")

    # Verificar se a permissão FOREGROUND_SERVICE_DATA_SYNC está presente
    if 'android.permission.FOREGROUND_SERVICE_DATA_SYNC' not in content:
        # Adicionar a permissão
        content = re.sub(
            r'(<uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>)',
            r'\1\n    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC"/>',
            content,
            count=1
        )
        manifest.write_text(content, encoding="utf-8")
        print("Permissão FOREGROUND_SERVICE_DATA_SYNC adicionada ao manifest")


def find_signed_apk(output_dir: Path) -> Path:
    candidates = sorted(output_dir.glob("*-aligned-*-signed.apk"))
    if not candidates:
        candidates = sorted(output_dir.glob("*-aligned-debugSigned.apk"))
    if not candidates:
        candidates = sorted(output_dir.glob("*.apk"))
    if not candidates:
        raise RuntimeError("O assinador não produziu uma APK de saída.")
    return candidates[-1]


def generate_apk(new_domain: str, output_name: str = "dtmod-custom.apk") -> Path:
    script_dir = Path(__file__).resolve().parent
    panel_dir = script_dir.parent
    apk_path = script_dir / "base.apk"
    work_dir = panel_dir / "apk_work"
    output_dir = panel_dir / "apk_output"

    if not apk_path.is_file():
        raise FileNotFoundError(f"APK base não encontrada: {apk_path}")
    if not SIGNER_JAR.is_file():
        raise FileNotFoundError(f"Assinador não encontrado: {SIGNER_JAR}")

    for directory in (work_dir, output_dir):
        if directory.exists():
            shutil.rmtree(directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        print("Decompilando APK base...")
        run_command([APKTOOL, "d", "-f", str(apk_path), "-o", str(work_dir)])
        verify_xhttp_runtime(work_dir)

        changed_files = replace_domains(work_dir, new_domain)
        print(f"Domínio aplicado em {changed_files} arquivo(s) Smali.")

        # Atualizar o dtunnelmod.json com a URL do painel
        update_dtunnelmod_json(work_dir, new_domain)

        # Corrigir targetSdkVersion para evitar crash em Android 14+
        pass # fix_target_sdk_version(work_dir)

        # Garantir permissões de foreground service
        fix_foreground_service_type(work_dir)

        unsigned_apk = output_dir / "unsigned.apk"
        print("Reconstruindo APK...")
        run_command([APKTOOL, "b", str(work_dir), "-o", str(unsigned_apk)])

        print("Assinando APK...")
        run_command(["java", "-jar", str(SIGNER_JAR), "--apks", str(unsigned_apk), "--out", str(output_dir)])

        final_destination = Path.home() / output_name
        signed_apk = find_signed_apk(output_dir)
        shutil.move(str(signed_apk), final_destination)
        print(f"Sucesso: APK gerada em {final_destination}")
        return final_destination
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python3 generate_apk.py <dominio-do-painel>")
        print("Exemplos:")
        print("  python3 generate_apk.py meudominio.com")
        print("  python3 generate_apk.py meudominio.com:3000")
        raise SystemExit(1)

    try:
        domain = normalize_domain(sys.argv[1])
        generate_apk(domain)
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
