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

    r = subprocess.run(cmd, cwd=str(SDK_ROOT), env=BASE_ENV,
                       capture_output=True, text=True)

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

@app.get("/defaults-audit")
def defaults_audit():
    import json
    from pathlib import Path

    dpath = Path("/app/zatca-sdk/Configuration/defaults.json")
    if not dpath.exists():
        return {"error": "defaults.json not found", "path": str(dpath)}

    raw = dpath.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except Exception as e:
        return {
            "path": str(dpath),
            "size": len(raw),
            "decode_preview": text[:500],
            "json_parse": f"ERROR: {e}",
        }

    keys = [
        "xsdPath","enSchematron","zatcaSchematron",
        "certPath","privateKeyPath","pihPath",
        "inputPath","usagePathFile"
    ]
    check = {}
    for k in keys:
        val = data.get(k)
        check[k] = {"value": val, "is_null": (val is None)}

    return {
        "path": str(dpath),
        "size": len(raw),
        "data": data,
        "keys_check": check,
    }

