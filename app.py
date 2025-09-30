from fastapi import FastAPI, UploadFile
from pathlib import Path
import subprocess, os

app = FastAPI()

SDK_ROOT = Path("/app/zatca-sdk").resolve()
APPS_DIR = SDK_ROOT / "Apps"
CONFIG_JSON = SDK_ROOT / "Configuration" / "config.json"

@app.post("/sign-invoice")
async def sign_invoice(xml_invoice: UploadFile):
    xml_path = SDK_ROOT / "input_invoice.xml"
    signed_path = SDK_ROOT / "signed_invoice.xml"

    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    env = {**os.environ, "FATOORA_HOME": str(APPS_DIR)}
    cmd = [
        "java", "-jar", str(APPS_DIR / "zatca-einvoicing-sdk-238-R3.4.3.jar"),
        "-config", str(CONFIG_JSON),
        "-cmd", "sign",
        "-input", str(xml_path),
        "-output", str(signed_path),
    ]

    r = subprocess.run(cmd, cwd=str(SDK_ROOT), env=env, capture_output=True, text=True)

    if signed_path.exists():
        return {
            "status": "success",
            "stdout": r.stdout[-4000:],
            "signed_invoice": signed_path.read_text(errors="ignore")
        }

    return {
        "status": "error",
        "return_code": r.returncode,
        "stdout": r.stdout[-4000:],
        "stderr": r.stderr[-4000:],
        "message": "Signed file not created"
    }

@app.get("/zdiag")
def zdiag():
    env = {**os.environ, "FATOORA_HOME": str(APPS_DIR)}
    cmd = [
        "java", "-jar", str(APPS_DIR / "zatca-einvoicing-sdk-238-R3.4.3.jar"),
        "-config", str(CONFIG_JSON),
        "-help"
    ]
    r = subprocess.run(cmd, cwd=str(SDK_ROOT), env=env, capture_output=True, text=True)
    return {"rc": r.returncode, "stdout": r.stdout[-5000:], "stderr": r.stderr[-5000:]}

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
