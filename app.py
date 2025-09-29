from fastapi import FastAPI, UploadFile
import subprocess, os
from pathlib import Path

app = FastAPI()

# Resolve SDK root relative to this file, works on Windows & Linux
SDK_ROOT = (Path(__file__).parent / "zatca-sdk").resolve()
APPS_DIR = SDK_ROOT / "Apps"
CERTS_DIR = SDK_ROOT / "Data" / "Certificates"

@app.get("/preflight")
def preflight():
    return {
        "cwd": str(Path().resolve()),
        "sdk_root": str(SDK_ROOT),
        "fatoora_home": os.environ.get("FATOORA_HOME"),
        "cert_exists": (CERTS_DIR / "cert.pem").exists(),
        "key_exists": (CERTS_DIR / "ec-secp256k1-priv-key.pem").exists(),
    }

@app.post("/sign-invoice")
async def sign_invoice(xml_invoice: UploadFile):
    xml_name = "input_invoice.xml"
    signed_name = "signed_invoice.xml"
    xml_path = SDK_ROOT / xml_name
    signed_path = SDK_ROOT / signed_name

    # Save uploaded invoice under the SDK root (so relative lookups work)
    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    env = {**os.environ, "FATOORA_HOME": str(APPS_DIR)}

    # IMPORTANT: run from SDK root so the CLI sees Data/Certificates
    cmd = ["./Apps/fatoora", "-sign", "-invoice", xml_name, "-signedInvoice", signed_name]
    result = subprocess.run(cmd, cwd=str(SDK_ROOT), env=env, capture_output=True, text=True)

    if signed_path.exists():
        with open(signed_path, "r", encoding="utf-8", errors="ignore") as f:
            signed_xml = f.read()
        return {"status": "success", "stdout": result.stdout, "signed_invoice": signed_xml}

    return {
        "status": "error",
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "message": "Signed file not created"
    }

@app.get("/zdebug")
def zdebug():
    import os, json
    from pathlib import Path

    sdk_root = Path(__file__).parent.joinpath("zatca-sdk").resolve()
    cert_dir = sdk_root / "Data" / "Certificates"
    apps_dir = sdk_root / "Apps"

    def ls(p: Path):
        try:
            return [{"name": f.name, "size": f.stat().st_size} for f in p.iterdir()]
        except Exception as e:
            return f"ERR: {e}"

    # Try fatoora -help from both /app and sdk root
    import subprocess
    def run(cmd, cwd=None, env=None):
        try:
            r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=8)
            return {"rc": r.returncode, "stdout": r.stdout[-5000:], "stderr": r.stderr[-5000:], "cwd": str(cwd)}
        except Exception as e:
            return {"error": str(e)}

    env = {**os.environ, "FATOORA_HOME": str(apps_dir)}
    out1 = run(["./Apps/fatoora", "-help"], cwd=str(sdk_root), env=env)
    out2 = run(["./Apps/fatoora", "-help"], cwd="/app", env=env)

    return {
        "cwd": str(Path().resolve()),
        "FATOORA_HOME": os.environ.get("FATOORA_HOME"),
        "sdk_root": str(sdk_root),
        "exists": {
            "apps_dir": apps_dir.exists(),
            "cert_dir": cert_dir.exists(),
            "cert": (cert_dir / "cert.pem").exists(),
            "key": (cert_dir / "ec-secp256k1-priv-key.pem").exists()
        },
        "ls": {
            "/app": ls(Path("/app")),
            "/app/zatca-sdk": ls(Path("/app/zatca-sdk")),
            "/app/zatca-sdk/Apps": ls(Path("/app/zatca-sdk/Apps")),
            "/app/zatca-sdk/Data/Certificates": ls(Path("/app/zatca-sdk/Data/Certificates")),
        },
        "fatoora_help_from_sdk_root": out1,
        "fatoora_help_from_app": out2
    }
