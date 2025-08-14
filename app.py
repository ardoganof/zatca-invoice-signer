from fastapi import FastAPI, UploadFile
import subprocess
import os

app = FastAPI()

@app.post("/sign-invoice")
async def sign_invoice(xml_invoice: UploadFile):
    xml_path = "input_invoice.xml"
    signed_output_path = "signed_invoice.xml"

    # Save uploaded XML invoice
    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    # Run fatoora sign command using built-in cert and key
    cmd = [
        "./zatca-sdk/Apps/fatoora",
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "FATOORA_HOME": "/app/zatca-sdk"}
        )

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
