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
    xml_path = "/app/zatca-sdk/Data/Input/input_invoice.xml"
    cert_path = "/app/cert.pfx"
    certs_dir = "/app/zatca-sdk/Data/Certificates"
    signed_output_path = "/app/zatca-sdk/Data/Output/signed_invoice.xml"

    # Ensure directories exist
    os.makedirs("/app/zatca-sdk/Data/Input", exist_ok=True)
    os.makedirs("/app/zatca-sdk/Data/Output", exist_ok=True)
    os.makedirs(certs_dir, exist_ok=True)

    # Save XML invoice
    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    # Save PFX certificate
    with open(cert_path, "wb") as f:
        f.write(await cert_file.read())

    # Extract private key (PEM)
    subprocess.run([
        "openssl", "pkcs12",
        "-in", cert_path,
        "-nocerts",
        "-nodes",
        "-password", f"pass:{cert_password}",
        "-out", f"{certs_dir}/ec-secp256k1-priv-key.pem"
    ], check=True)

    # Extract public certificate (PEM)
    subprocess.run([
        "openssl", "pkcs12",
        "-in", cert_path,
        "-clcerts",
        "-nokeys",
        "-password", f"pass:{cert_password}",
        "-out", f"{certs_dir}/cert.pem"
    ], check=True)

    # Make fatoora executable
    subprocess.run(["chmod", "+x", "/app/zatca-sdk/Apps/fatoora"], check=True)

    # Run signing command
    cmd = [
        "/app/zatca-sdk/Apps/fatoora",
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path
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
            "stderr": e.stderr,
            "message": "Signing failed — check logs above."
        }
