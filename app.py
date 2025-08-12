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
    xml_path = "/app/input_invoice.xml"
    cert_path = "/app/cert.pfx"
    signed_output_path = "/app/signed_invoice.xml"

    # Save uploaded XML
    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    # Save uploaded certificate
    with open(cert_path, "wb") as f:
        f.write(await cert_file.read())

    # Make fatoora executable (important for Render/Linux)
    subprocess.run(["chmod", "+x", "./zatca-sdk/Apps/fatoora"], check=True)

    # Run the signing command
    cmd = [
        "./zatca-sdk/Apps/fatoora",
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path,
        "-pk", cert_path,
        "-pkPassword", cert_password
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if os.path.exists(signed_output_path):
            with open(signed_output_path, "r") as f:
                signed_xml = f.read()
            return {
                "status": "success",
                "stdout": result.stdout,
                "signed_invoice": signed_xml
            }
        else:
            return {
                "status": "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": "Signing failed — signed file not created."
            }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "return_code": e.returncode,
            "stdout": e.stdout,
            "stderr": e.stderr
        }
