from fastapi import FastAPI, UploadFile, Form
import subprocess
import os

app = FastAPI()

FATOORA_HOME = "/app/zatca-sdk/Apps"

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

    # Build the fatoora command exactly like in your local tests
    cmd = [
        f"{FATOORA_HOME}/fatoora",
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path,
        "-cert", cert_path,
        "-password", cert_password
    ]

    env = os.environ.copy()
    env["FATOORA_HOME"] = FATOORA_HOME

    # Run fatoora
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env
    )

    # If something went wrong
    if result.returncode != 0 or not os.path.exists(signed_output_path):
        return {
            "status": "error",
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": "Signing failed — check logs above."
        }

    # If everything went well
    with open(signed_output_path, "r") as f:
        signed_xml = f.read()

    return {
        "status": "success",
        "signed_invoice": signed_xml
    }
