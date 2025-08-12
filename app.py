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
    # Paths
    xml_path = "/app/input_invoice.xml"
    cert_path = "/app/cert.pfx"
    signed_output_path = "/app/signed_invoice.xml"
    certs_dir = "/app/zatca-sdk/Data/Certificates"

    # Save uploaded files
    with open(xml_path, "wb") as f:
        f.write(await xml_invoice.read())

    with open(cert_path, "wb") as f:
        f.write(await cert_file.read())

    # Log certificate folder contents
    if os.path.exists(certs_dir):
        print("Certificates folder exists. Contents:", os.listdir(certs_dir))
    else:
        return {"status": "error", "message": f"Certificates folder not found: {certs_dir}"}

    # Check for private key
    priv_key_path = os.path.join(certs_dir, "ec-secp256k1-priv-key.pem")
    if not os.path.exists(priv_key_path):
        return {"status": "error", "message": f"Private key file not found: {priv_key_path}"}

    # Fix permissions
    subprocess.run(["chmod", "644", priv_key_path], check=True)
    subprocess.run(["chmod", "644", os.path.join(certs_dir, "cert.pem")], check=True)

    # Prepare environment for SDK
    env = os.environ.copy()
    env["FATOORA_HOME"] = "/app/zatca-sdk/Apps"

    # Sign invoice
    cmd = [
        "/app/zatca-sdk/Apps/fatoora",
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
        if os.path.exists(signed_output_path):
            with open(signed_output_path, "r") as f:
                signed_xml = f.read()
            return {"status": "success", "signed_invoice": signed_xml, "stdout": result.stdout}
        else:
            return {"status": "error", "stdout": result.stdout, "stderr": result.stderr, "message": "Signing failed — signed file not created."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "return_code": e.returncode, "stdout": e.stdout, "stderr": e.stderr}
