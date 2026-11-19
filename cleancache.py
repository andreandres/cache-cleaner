import argparse
import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path


def caminho_steam():
    """Tenta encontrar o Steam instalado, incluindo instalações fora do caminho padrão."""
    candidatos = [
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("ProgramFiles", r"C:\Program Files"),
    ]

    for raiz in candidatos:
        candidato = Path(raiz) / "Steam"
        if candidato.exists():
            return candidato

    try:
        import winreg

        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            with winreg.OpenKey(hive, r"SOFTWARE\WOW6432Node\Valve\Steam") as chave:
                valor, _ = winreg.QueryValueEx(chave, "InstallPath")
                candidato = Path(valor)
                if candidato.exists():
                    return candidato
    except (ImportError, OSError):
        pass

    return Path(r"C:\Program Files (x86)\Steam")


def bytes_para_texto(valor):
    """Converte bytes para uma unidade legível."""
    for unidade in ("B", "KB", "MB", "GB"):
        if valor < 1024:
            return f"{valor:.1f} {unidade}"
        valor /= 1024
    return f"{valor:.1f} TB"


def tamanho_pasta(pasta):
    """Calcula o tamanho sem lançar exceções por arquivos bloqueados ou links quebrados."""
    total = 0
    try:
        for item in pasta.rglob("*"):
            try:
                if item.is_file() or item.is_symlink():
                    total += item.stat(follow_symlinks=False).st_size
            except (PermissionError, FileNotFoundError, OSError):
                pass
    except (PermissionError, FileNotFoundError, OSError):
        pass
    return total


def limpar_pasta(pasta, modo_teste=False):
    """Apaga o conteúdo de uma pasta e informa o espaço que deixou de ser ocupado."""
    p = Path(pasta)
    if not p.exists():
        print(f"  [--] Não encontrada: {pasta}")
        return 0

    tamanho_antes = tamanho_pasta(p)

    if not modo_teste:
        for item in list(p.iterdir()):
            try:
                if item.is_symlink() or item.is_file():
                    item.unlink(missing_ok=True)
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
            except (PermissionError, OSError):
                pass

        tamanho_restante = tamanho_pasta(p)
        liberado = max(0, tamanho_antes - tamanho_restante)
        mensagem = "[OK]"
    else:
        liberado = tamanho_antes
        mensagem = "[TESTE]"

    print(f"  {mensagem} {p.name:<35} {bytes_para_texto(liberado):>10}")
    return liberado


def limpar_arquivos_antigos(pasta, dias, modo_teste=False):
    """Remove apenas arquivos mais antigos que o período informado."""
    p = Path(pasta)
    if not p.exists():
        print(f"  [--] Não encontrada: {pasta}")
        return 0

    limite = __import__("time").time() - dias * 86400
    liberado = 0
    prefixo = "[TESTE]" if modo_teste else "[OK]"

    for item in p.rglob("*"):
        try:
            if item.is_file() and item.stat().st_mtime < limite:
                tamanho = item.stat().st_size
                if not modo_teste:
                    item.unlink(missing_ok=True)
                liberado += tamanho
        except (PermissionError, FileNotFoundError, OSError):
            pass

    print(f"  {prefixo} {p.name:<35} {bytes_para_texto(liberado):>10} antigos")
    return liberado


def checar_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def limpar_lixeira(modo_teste=False):
    """Esvazia a Lixeira do usuário atual sem apagar outros arquivos."""
    if modo_teste:
        print("  [TESTE] Lixeira                         verificar manualmente")
        return 0

    try:
        resultado = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
        if resultado == 0:
            print("  [OK] Lixeira                         limpo")
        else:
            print("  [--] Lixeira                         não foi possível limpar")
    except Exception:
        print("  [--] Lixeira                         API indisponível")
    return 0


def limpar_dns(modo_teste=False):
    """Limpa apenas a resolução DNS do Windows."""
    if modo_teste:
        print("  [TESTE] DNS Cache                        ipconfig /flushdns")
        return

    resultado = subprocess.run(
        ["ipconfig", "/flushdns"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("  [OK] DNS Cache                        limpo" if resultado.returncode == 0 else "  [--] DNS Cache                        não foi possível limpar")


def montar_lista(pasta_steam, incluir_prefetch=True, incluir_updates=True):
    local = os.environ.get("LOCALAPPDATA", "")
    usuario = os.environ.get("USERPROFILE", "")
    temp = os.environ.get("TEMP", "")

    pastas = [
        temp,
        r"C:\Windows\Temp",
        os.path.join(local, "Microsoft", "Windows", "Explorer"),
        os.path.join(local, "Microsoft", "Windows", "INetCache"),
        os.path.join(local, "AMD", "DXCache"),
        os.path.join(local, "AMD", "GLCache"),
        os.path.join(local, "D3DSCache"),
        os.path.join(local, "pip", "Cache"),
        os.path.join(local, "npm", "_cacache"),
        os.path.join(local, "CrashDumps"),
        os.path.join(usuario, "AppData", "Local", "Dumps"),
        os.path.join(pasta_steam, "config", "htmlcache"),
        os.path.join(pasta_steam, "logs"),
        os.path.join(pasta_steam, "appcache", "httpcache"),
        os.path.join(pasta_steam, "steamapps", "common", "Counter-Strike 2", "dumps"),
        os.path.join(pasta_steam, "steamapps", "common", "Counter-Strike 2", "bin", "win64", "dumps"),
    ]

    if incluir_prefetch:
        pastas.append(r"C:\Windows\Prefetch")
    if incluir_updates:
        pastas.append(r"C:\Windows\SoftwareDistribution\Download")

    # Chrome e Edge: inclui perfis com nomes dinâmicos, não apenas os quatro padrões.
    for navegador in ("Google", "Microsoft"):
        base = (
            os.path.join(local, "Google", "Chrome", "User Data")
            if navegador == "Google"
            else os.path.join(local, "Microsoft", "Edge", "User Data")
        )
        base_pasta = Path(base)
        if base_pasta.exists():
            perfis = [base_pasta / "Default"]
            perfis.extend(pasta for pasta in base_pasta.glob("Profile *") if pasta.is_dir())
            for perfil in perfis:
                pastas.append(str(perfil / "Cache" / "Cache_Data"))
                pastas.append(str(perfil / "Code Cache"))

    # Steam: caches de shaders e da interface podem ser regenerados automaticamente.
    pastas.extend([
        os.path.join(pasta_steam, "shadercache"),
        os.path.join(pasta_steam, "dumps"),
    ])

    # Caches comuns de launchers e aplicativos que ficam ativos em segundo plano.
    pastas.extend([
        os.path.join(local, "Discord", "Cache"),
        os.path.join(local, "Discord", "Code Cache"),
        os.path.join(local, "Discord", "GPUCache"),
        os.path.join(local, "EpicGamesLauncher", "Saved", "webcache"),
        os.path.join(local, "EpicGamesLauncher", "Saved", "webcache_4147"),
        os.path.join(local, "Battle.net", "Cache"),
        os.path.join(local, "Microsoft", "Windows", "WebCache"),
    ])

    # Firefox organiza os perfis em AppData/Roaming/Mozilla/Firefox/Profiles.
    perfis_firefox = Path(usuario) / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
    if perfis_firefox.exists():
        for perfil in perfis_firefox.iterdir():
            pastas.append(str(perfil / "cache2"))

    # Cache de GPU mais comum no Windows.
    pastas.extend([
        os.path.join(local, "NVIDIA", "DXCache"),
        os.path.join(local, "NVIDIA", "GLCache"),
    ])

    return [p for p in pastas if p]


def main():
    parser = argparse.ArgumentParser(description="Limpeza completa de caches e temporários no Windows")
    parser.add_argument("--teste", action="store_true", help="Mostra o que poderia ser limpo, sem apagar")
    parser.add_argument("--jogos", action="store_true", help="Alias para a limpeza completa padrão")
    parser.add_argument("--dns", action="store_true", help="Limpa o cache DNS do Windows")
    parser.add_argument("--lixeira", action="store_true", help="Esvazia a Lixeira")
    parser.add_argument("--sem-prefetch", action="store_true", help="Não limpa o Prefetch")
    parser.add_argument("--sem-windows-update", action="store_true", help="Não limpa downloads pendentes do Windows Update")
    args = parser.parse_args()

    if os.name == "nt":
        os.system("cls")

    print("=" * 55)
    print("Limpeza completa" + (" - MODO TESTE" if args.teste else ""))
    print("=" * 55)

    if not checar_admin() and not args.teste:
        print("  Solicitando permissão de Administrador...")
        parametros = subprocess.list2cmdline(sys.argv)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, parametros, None, 1)
        sys.exit(0)

    pasta_steam = caminho_steam()
    total = 0

    incluir_prefetch = not args.sem_prefetch
    incluir_updates = not args.sem_windows_update

    for pasta in montar_lista(
        pasta_steam,
        incluir_prefetch=incluir_prefetch,
        incluir_updates=incluir_updates,
    ):
        total += limpar_pasta(pasta, modo_teste=args.teste)

    total += limpar_lixeira(modo_teste=args.teste)
    limpar_dns(modo_teste=args.teste)

    print()
    print("=" * 55)
    etiqueta = "Poderiam ser liberados" if args.teste else "Espaço liberado"
    print(f"  {etiqueta}: {bytes_para_texto(total)}")
    print("=" * 55)

    if not args.teste:
        input("\n  Pressione ENTER para fechar...")


if __name__ == "__main__":
    main()