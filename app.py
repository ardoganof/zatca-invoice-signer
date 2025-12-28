from fastapi import FastAPI, UploadFile, Form
from pathlib import Path
import subprocess, json, os

app = FastAPI()

SDK_ROOT = Path("/app/zatca-sdk").resolve()
APPS = SDK_ROOT / "Apps"
CONF = SDK_ROOT / "Configuration" / "config.json"

def ext_version():
    return json.loads((APPS / "global.json").read_text())["version"]

def jar_path():
    v = ext_version()
    return APPS / f"zatca-einvoicing-sdk-{v}.jar"

@app.post("/sign-invoice")
async def sign_invoice(
    xml_invoice: UploadFile,
    unsigned_name: str = Form("invoice.xml"),
    signed_name: str = Form("invoice_signed.xml")
):
    unsigned_file = SDK_ROOT / unsigned_name
    signed_file = SDK_ROOT / signed_name

    unsigned_file.write_bytes(await xml_invoice.read())
    if signed_file.exists():
        signed_file.unlink()

    cmd = [
        "java",
        "-Duser.dir=" + str(SDK_ROOT),
        "-jar", str(jar_path()),
        "--globalVersion", ext_version(),
        "--config", str(CONF),
        "-sign",
        "-invoice", str(unsigned_file),
        "-signedInvoice", str(signed_file)
    ]

    r = subprocess.run(
        cmd,
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True
    )

    if signed_file.exists():
        return {
            "status": "success",
            "signed_invoice": signed_file.read_text(errors="ignore"),
            "stdout": r.stdout[-4000:]
        }

    return {
        "status": "error",
        "return_code": r.returncode,
        "stdout": r.stdout[-4000:],
        "stderr": r.stderr[-4000:],
        "message": "Signed file not created"
    }


@app.get("/debug/certs")
def debug_certs():
    cert_dir = SDK_ROOT / "Data" / "Certificates"
    info = {"path": str(cert_dir), "exists": cert_dir.exists(), "files": []}
    if cert_dir.exists():
        for f in sorted(cert_dir.iterdir()):
            try:
                s = f.stat()
                info["files"].append({"name": f.name, "size": s.st_size})
            except Exception as e:
                info["files"].append({"name": f.name, "error": str(e)})
    # include the loaded config JSON to verify paths used by the SDK
    try:
        info["config"] = json.loads(CONF.read_text())
    except Exception as e:
        info["config_error"] = str(e)
    return info


@app.get("/")
def root():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
