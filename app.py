from fastapi import FastAPI, UploadFile, Form
import subprocess
import os

app = FastAPI()

@app.post("/sign-invoice")
async def sign_invoice(
    xml_invoice: UploadFile,
    cert_file: UploadFile,
    cert_password: str = Form(...)
):
    # Save uploaded files
    xml_path = "input_invoice.xml"
    cert_path = "cert.pfx"
    signed_output_path = "signed_invoice.xml"

    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    with open(cert_path, "wb") as f:
        f.write(await cert_file.read())

    # Call the ZATCA SDK sign command
    cmd = [
        "/app/zatca-sdk/Apps/fatoora",
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, "FATOORA_HOME": "/app/zatca-sdk/Apps"}
        )
        if result.returncode == 0 and os.path.exists(signed_output_path):
            with open(signed_output_path, "r") as f:
                signed_xml = f.read()
            return {"status": "success", "signed_invoice": signed_xml}
        else:
            return {
                "status": "error",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": "Signing failed — signed file not created."
            }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error_output": e.stderr,
            "stdout": e.stdout,
            "message": "Subprocess failed."
        }
