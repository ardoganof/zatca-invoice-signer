from fastapi import FastAPI, UploadFile
from pathlib import Path
import subprocess, os, json

app = FastAPI()

SDK_ROOT   = Path("/app/zatca-sdk").resolve()
APPS_DIR   = SDK_ROOT / "Apps"
CONFIG_JSON = SDK_ROOT / "Configuration" / "config.json"
JAR        = APPS_DIR / "zatca-einvoicing-sdk-238-R3.4.3.jar"

def _extver() -> str:
    # Read global.json to get the version string (e.g., "238-R3.4.3")
    gj = json.loads((APPS_DIR / "global.json").read_text())
    return gj["version"]

BASE_ENV = {**os.environ, "FATOORA_HOME": str(APPS_DIR)}

@app.post("/sign-invoice")
async def sign_invoice(xml_invoice: UploadFile):
    xml_path    = SDK_ROOT / "input_invoice.xml"
    signed_path = SDK_ROOT / "signed_invoice.xml"

    xml_path.write_bytes(await xml_invoice.read())

    cmd = [
        "java",
        "-Djdk.module.illegalAccess=deny",
        "-Djdk.sunec.disableNative=false",
        "-jar", str(JAR),
        "--globalVersion", _extver(),
        "-config", str(CONFIG_JSON),
        "-cmd", "sign",
        "-input", str(xml_path),
        "-output", str(signed_path),
    ]

    r = subprocess.run(["./Apps/fatoora", "-sign", "-invoice", xml_path, "-signedInvoice", signed_output_path],
               cwd="/app/zatca-sdk", capture_output=True, text=True)


    if signed_path.exists():
        return {
            "status": "success",
            "stdout": r.stdout[-4000:],
            "signed_invoice": signed_path.read_text(errors="ignore")
        }
    else:
        return {
            "status": "error",
            "return_code": r.returncode,
            "stdout": r.stdout[-4000:],
            "stderr": r.stderr[-4000:],
            "message": "Signed file not created"
        }

@app.get("/zdiag")
def zdiag():
    # Prove the JAR loads config + resources when globalVersion is provided
    cmd = [
        "java",
        "-Djdk.module.illegalAccess=deny",
        "-Djdk.sunec.disableNative=false",
        "-jar", str(JAR),
        "--globalVersion", _extver(),
        "-config", str(CONFIG_JSON),
        "-help"
    ]
    r = subprocess.run(cmd, cwd=str(SDK_ROOT), env=BASE_ENV,
                       capture_output=True, text=True, timeout=10)
    return {"rc": r.returncode, "stdout": r.stdout[-5000:], "stderr": r.stderr[-5000:]}

@app.get("/preflight")
async def preflight():
    import os
    def info(p):
        return {"exists": os.path.exists(p), "size": os.path.getsize(p) if os.path.exists(p) else 0}
    return {
        "sdk_root": info("/app/zatca-sdk"),
        "fatoora": info("/app/zatca-sdk/Apps/fatoora"),
        "global_json": info("/app/zatca-sdk/Apps/global.json"),
        "jar_in_apps": [f for f in (os.listdir("/app/zatca-sdk/Apps") if os.path.exists("/app/zatca-sdk/Apps") else []) if f.endswith(".jar")],
        "cert_pem": info("/app/zatca-sdk/Data/Certificates/cert.pem"),
        "key_pem": info("/app/zatca-sdk/Data/Certificates/ec-secp256k1-priv-key.pem")
    }

@app.get("/config-audit")
def config_audit():
    import json
    from pathlib import Path

    sdk_root = Path("/app/zatca-sdk")
    cfg_path = sdk_root / "Configuration" / "config.json"

    # Read config.json that Java actually uses
    if not cfg_path.exists():
        return {"error": f"config.json not found at {cfg_path}"}
    cfg = json.loads(cfg_path.read_text(errors="ignore"))

    keys = [
        "xsdPath", "enSchematron", "zatcaSchematron",
        "certPath", "privateKeyPath", "pihPath",
        "inputPath", "usagePathFile"
    ]
    report = {}
    for k in keys:
        val = cfg.get(k)
        item = {"value": val}
        if val:
            p = Path(val)
            item["exists"] = p.exists()
            item["is_file"] = p.is_file()
            item["size"] = (p.stat().st_size if p.exists() and p.is_file() else None)
        report[k] = item

    # Also dump directory listings for sanity
    def list_files(base):
        base = Path(base)
        if not base.exists():
            return "MISSING"
        out = {}
        for child in sorted(base.rglob("*")):
            if child.is_file():
                out[str(child)] = child.stat().st_size
        return out

    return {
        "config_path": str(cfg_path),
        "config_used_here": cfg,
        "checks": report,
        "listings": {
            "/app/zatca-sdk/Data/Schemas": list_files("/app/zatca-sdk/Data/Schemas"),
            "/app/zatca-sdk/Data/Rules/schematrons": list_files("/app/zatca-sdk/Data/Rules/schematrons"),
            "/app/zatca-sdk/Data/PIH": list_files("/app/zatca-sdk/Data/PIH"),
            "/app/zatca-sdk/Configuration": list_files("/app/zatca-sdk/Configuration"),
        }
    }

@app.get("/symlink-check")
def symlink_check():
    import os
    def stat(p):
        return {"exists": os.path.exists(p),
                "is_symlink": os.path.islink(p),
                "realpath": os.path.realpath(p) if os.path.exists(p) else None}
    return {
        "/app/Data": stat("/app/Data"),
        "/app/Configuration": stat("/app/Configuration"),
    }
