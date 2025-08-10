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

    # Ensure SDK script is executable
    sdk_fatoora = "./zatca-sdk/Apps/fatoora"  # For Linux/Render environment
    os.chmod(sdk_fatoora, 0o755)

    os.environ["FATOORA_HOME"] = "/app/zatca-sdk/Apps"

    # Build the command (no .jar call — use fatoora CLI directly)
    cmd = [
        sdk_fatoora,
        "-sign",
        "-invoice", xml_path,
        "-signedInvoice", signed_output_path,
        "-cert", cert_path,
        "-password", cert_password
    ]

    try:
	result = subprocess.run(cmd, capture_output=True, text=True)
	if result.returncode != 0:
	    return {"status": "error", "stderr": result.stderr, "stdout": result.stdout}

	if not os.path.exists(signed_output_path):
	    return {"status": "error", "message": "Signed file not found", "stdout": result.stdout, "stderr": result.stderr}

	with open(signed_output_path, "r") as f:
	    signed_xml = f.read()

        return {"status": "success", "signed_invoice": signed_xml}
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error_output": e.stderr,
            "stdout": e.stdout
        }
