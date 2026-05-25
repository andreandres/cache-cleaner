import os
import sys
import shutil
import ctypes
from pathlib import Path
import subprocess

# Configuracao dos caminhos das pastas

# Caminho da pasta da Steam
CAMINHO_STEAM = r"C:\Program Files (x86)\Steam"

# Lista de pastas que serao limpas.


PASTAS_PARA_LIMPAR = [

    # Temporarios do Windows
    os.environ.get("TEMP", ""),               # Temp do seu usuario
    r"C:\Windows\Temp",                       # Temp do sistema
    r"C:\Windows\Prefetch",                   # Cache de inicializacao

    # Cache do Windows
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer"),   # Thumbnails
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "INetCache"),  # Cache do Edge/IE
    r"C:\Windows\SoftwareDistribution\Download",  # Downloads do Windows Update

    # AMD
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "AMD", "DXCache"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "AMD", "GLCache"),
    # Shader cache geral do Windows
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "D3DSCache"),

    # Steam
    os.path.join(CAMINHO_STEAM, "config", "htmlcache"),  # Interface do Steam
    os.path.join(CAMINHO_STEAM, "logs"),                 # Logs do Steam
    os.path.join(CAMINHO_STEAM, "appcache", "httpcache"),# HTTP Cache

    # CS2
    os.path.join(CAMINHO_STEAM, "steamapps", "common", "Counter-Strike 2", "dumps"),
    os.path.join(CAMINHO_STEAM, "steamapps", "common", "Counter-Strike 2", "bin", "win64", "dumps"),

]

def bytes_para_texto(b):
    """Converte bytes em KB, MB ou GB para exibir na tela."""
    for unidade in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unidade}"
        b /= 1024
    return f"{b:.1f} TB"


def limpar_pasta(pasta):
    """Apaga tudo dentro de uma pasta e retorna quantos bytes foram liberados."""
    p = Path(pasta)
    if not p.exists():
        print(f"  [--] Nao encontrada: {pasta}")
        return 0

    liberado = 0
    for item in p.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                liberado += item.stat().st_size
                item.unlink(missing_ok=True)
            elif item.is_dir():
                liberado += sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                shutil.rmtree(item, ignore_errors=True)
        except (PermissionError, OSError):
            pass  # arquivo em uso pelo sistema — ignora e continua

    print(f"  [OK] {p.name:<35} {bytes_para_texto(liberado):>10} liberados")
    return liberado


def checar_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def main():
    subprocess.run("cls", shell=True)
    print("=" * 55)
    print("Limpeza de cache")
    print("=" * 55)

    # Se nao estiver como admin, relanca automaticamente como admin
    if not checar_admin():
        print("  Solicitando permissao de Administrador...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            " ".join(f'"{a}"' for a in sys.argv),
            None, 1
        )
        sys.exit()

    print()
    total = 0
    for pasta in PASTAS_PARA_LIMPAR:
        if pasta:  # ignora strings vazias (caso alguma variavel de ambiente nao exista)
            total += limpar_pasta(pasta)

    print()
    print("=" * 55)
    print(f"  PRONTO! Total liberado: {bytes_para_texto(total)}")
    print("=" * 55)
    input("\n  Pressione ENTER para fechar...")


if __name__ == "__main__":
    main()