from fastapi import FastAPI, UploadFile
import subprocess
import os

app = FastAPI()

@app.post("/sign-invoice")
async def sign_invoice(xml_invoice: UploadFile):
    # Save uploaded invoice file
    xml_path = "input_invoice.xml"
    signed_output_path = "signed_invoice.xml"

    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    # Call fatoora (it will pick up cert.pem & key from Data/Certificates)
    cmd = [
        "/app/zatca-sdk/Apps/fatoora",
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(signed_output_path):
            with open(signed_output_path, "r") as f:
                signed_xml = f.read()
            return {"status": "success", "signed_invoice": signed_xml, "stdout": result.stdout}
        else:
            return {
                "status": "error",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": "Signed file not created"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 🔎 Debug endpoint to inspect container files
@app.get("/debug-files")
async def debug_files():
    result = []
    for root, dirs, files in os.walk("/app/zatca-sdk"):
        for name in files:
            result.append(os.path.join(root, name))
    return {"files": result}

@app.get("/preflight")
async def preflight():
    import os
    import pathlib
    return {
        "cwd": pathlib.Path().resolve().as_posix(),
        "FATOORA_HOME": os.environ.get("FATOORA_HOME"),
    }

