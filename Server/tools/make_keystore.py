import argparse
import os
import platform
import socket
import subprocess
from getpass import getpass
from pathlib import Path
from typing import Optional, List


def run(cmd: List[str], *, env: Optional[dict] = None) -> None:
    """
    Run command (команда: внешняя программа с аргументами) and fail loud
    (fail: завершиться с ошибкой).
    """
    try:
        subprocess.run(cmd, check=True, env=env)
    except FileNotFoundError:
        raise SystemExit(
            f"[ERROR] Command not found (команда не найдена): {cmd[0]}")
    except subprocess.CalledProcessError as e:
        raise SystemExit(
            f"[ERROR] Command failed (команда завершилась с ошибкой): "
            f"{' '.join(cmd)}\n"
            f"Exit code (код выхода): {e.returncode}"
        )


def detect_ipv4_udp() -> Optional[str]:
    """
    Detect local IPv4 via UDP connect trick
    (трюк: приём без реального трафика).
    UDP connect (UDP connect: установка "маршрута" без отправки пакетов)
    даёт локальный IP интерфейса.
    """
    candidates = [("1.1.1.1", 80), ("8.8.8.8", 80)]
    for host, port in candidates:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((host, port))
            ip = s.getsockname()[0]
            s.close()
            # 169.254.* is APIPA (APIPA: авто-IP без DHCP)
            if ip and not ip.startswith("169.254."):
                return ip
        except OSError:
            try:
                s.close()
            except Exception:
                pass
            continue
    return None


def detect_ipv4_powershell() -> Optional[str]:
    """
    Detect IPv4 using PowerShell (PowerShell: командная оболочка Windows)
    route query (route: маршрут).
    """
    if platform.system().lower() != "windows":
        return None

    ps = (
        "$r=Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
        "Sort-Object RouteMetric | Select-Object -First 1; "
        "$ip=(Get-NetIPAddress -InterfaceIndex $r.InterfaceIndex "
        "-AddressFamily IPv4 | "
        "Where-Object { $_.IPAddress -notlike '169.254*' } | "
        "Select-Object -First 1).IPAddress; "
        "if ($ip) { $ip }"
    )
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out if out else None
    except Exception:
        return None


def detect_ipv4() -> str:
    ip = detect_ipv4_udp() or detect_ipv4_powershell()
    if not ip:
        raise SystemExit(
            "[ERROR] Could not detect IPv4 (не удалось определить IPv4).")
    return ip


def which_or_exit(name: str) -> None:
    """
    Check PATH (PATH: список папок поиска команд) for tool (tool: утилита).
    """
    from shutil import which
    if which(name) is None:
        raise SystemExit(
            f"[ERROR] '{name}' not found in PATH (утилита не найдена в PATH).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate mkcert cert/key and PKCS#12 keystore for local Spring "
            "HTTPS (HTTPS: HTTP over TLS)."
        )
    )
    parser.add_argument("--outdir", default="ssl",
                        help="Output directory (папка вывода). Default: ssl")
    parser.add_argument(
        "--keystore",
        default="keystore.p12",
        help=(
            "Keystore filename (имя .p12 файла). "
            "Default: keystore.p12"
        )
    )
    parser.add_argument(
        "--extra",
        default="",
        help=(
            "Extra hosts/IPs (доп. имена/адреса) comma-separated "
            "(через запятую). "
            "Example: localhost,127.0.0.1"
        )
    )
    parser.add_argument("--noinstall", action="store_true",
                        help="Skip mkcert -install (пропустить установку CA).")
    parser.add_argument(
        "--name",
        default="spring",
        help=(
            "Friendly name (alias: имя записи) inside keystore. "
            "Default: spring"
        )
    )
    args = parser.parse_args()

    which_or_exit("mkcert")
    which_or_exit("openssl")

    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    ip = detect_ipv4()
    print(f"Detected IPv4 (обнаружен IPv4): {ip}")

    cert_file = outdir / "cert.pem"
    key_file = outdir / "key.pem"
    p12_file = outdir / args.keystore

    if not args.noinstall:
        print(
            "Running mkcert -install "
            "(установка локальной CA: центра сертификации)..."
        )
        try:
            run(["mkcert", "-install"])
        except SystemExit as e:
            # Not fatal (не фатально): cert still works
            # but may be untrusted (недоверенный)
            print(str(e))
            print(
                "[WARN] mkcert -install failed (не удалось установить CA). "
                "Browser/phone may show warning (предупреждение)."
            )
    else:
        print("Skipping mkcert -install (пропускаем установку CA).")

    extra_items = []
    if args.extra.strip():
        extra_items = [x.strip() for x in args.extra.split(",") if x.strip()]

    print("Generating certificate with mkcert (генерация сертификата)...")
    mkcert_cmd = [
        "mkcert",
        "-cert-file", str(cert_file),
        "-key-file", str(key_file),
        ip,
        *extra_items
    ]
    run(mkcert_cmd)

    # Password prompt (запрос пароля) with confirmation (подтверждение)
    while True:
        p1 = getpass("Enter keystore password (введите пароль для keystore): ")
        if not p1:
            print(
                "[ERROR] Empty password (пустой пароль) is not allowed "
                "(не допускается)."
            )
            continue
        p2 = getpass("Repeat password (повторите пароль): ")
        if p1 != p2:
            print(
                "[ERROR] Passwords do not match (пароли не совпадают). "
                "Try again (попробуйте снова)."
            )
            continue
        break

    # Export to PKCS#12 using env var (env var: переменная окружения)
    # to avoid command-line leak (утечка в историю)
    env = os.environ.copy()
    env["KEYSTORE_PASS"] = p1

    print(
        "Creating PKCS#12 keystore with OpenSSL "
        "(создание .p12 контейнера)..."
    )
    openssl_cmd = [
        "openssl", "pkcs12",
        "-export",
        "-out", str(p12_file),
        "-inkey", str(key_file),
        "-in", str(cert_file),
        "-name", args.name,
        "-passout", "env:KEYSTORE_PASS",
    ]
    run(openssl_cmd, env=env)

    # Cleanup sensitive env var (очистка: убрать пароль из окружения процесса)
    env["KEYSTORE_PASS"] = ""

    print("\nDONE (готово). Files (файлы):")
    print(f"  Certificate cert.pem (сертификат): {cert_file}")
    print(f"  Private key key.pem (приватный ключ): {key_file}")
    print(f"  Keystore {args.keystore} (.p12 контейнер): {p12_file}")
    print(
        f"\nTest URL (проверка URL): https://{ip}:8443\n"
        "  (порт 8443: типичный HTTPS-порт для dev)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
