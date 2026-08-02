import os
import subprocess
import sys
import shutil

def run_command(command):
    print(f"Executando: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Erro ao executar comando: {stderr.decode('utf-8')}")
        return False
    return True

def generate_apk(new_domain, output_name="dtmod-custom.apk"):
    # Caminhos relativos ao diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    panel_dir = os.path.dirname(script_dir)
    
    apk_path = os.path.join(script_dir, "base.apk")
    work_dir = os.path.join(panel_dir, "apk_work")
    output_dir = os.path.join(panel_dir, "apk_output")
    
    if not os.path.exists(apk_path):
        print(f"Erro: APK base nao encontrado em {apk_path}")
        return False
    
    # 1. Limpar diretórios
    for d in [work_dir, output_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. Decompilar
    print("Decompilando APK...")
    if not run_command(f"apktool d {apk_path} -o {work_dir}"):
        return False

    # 3. Modificar domínios
    old_domains = [
        "device.dtunnel.com.br",
        "text.dtunnel.com.br",
        "config.dtunnel.com.br",
        "app.dtunnel.com.br"
    ]
    
    print(f"Alterando domínios para: {new_domain}")
    for root, dirs, files in os.walk(work_dir):
        for file in files:
            if file.endswith(".smali"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    new_content = content
                    for old in old_domains:
                        new_content = new_content.replace(old, new_domain)
                    
                    if new_content != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                except Exception as e:
                    continue

    # 4. Recompilar
    print("Recompilando APK...")
    unsigned_apk = os.path.join(output_dir, "unsigned.apk")
    if not run_command(f"apktool b {work_dir} -o {unsigned_apk}"):
        return False

    # 5. Assinar
    print("Assinando APK...")
    signer_jar = "/usr/local/bin/uber-apk-signer.jar"
    if not run_command(f"java -jar {signer_jar} --apks {unsigned_apk} --out {output_dir}"):
        return False

    # 6. Mover para o destino final
    # O uber-apk-signer gera um nome específico
    signed_apk = os.path.join(output_dir, "unsigned-aligned-debugSigned.apk")
    final_destination = os.path.join(os.path.expanduser("~"), output_name)
    
    if os.path.exists(signed_apk):
        shutil.move(signed_apk, final_destination)
        print(f"Sucesso! APK gerado em: {final_destination}")
        # Limpeza
        shutil.rmtree(work_dir)
        shutil.rmtree(output_dir)
        return True
    else:
        print("Erro: APK assinado nao encontrado.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 generate_apk.py <seu-dominio.com>")
        sys.exit(1)
    
    domain = sys.argv[1].replace("http://", "").replace("https://", "").strip("/")
    generate_apk(domain)
