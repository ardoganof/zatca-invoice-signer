from fastapi import FastAPI, UploadFile
import subprocess
import os

app = FastAPI()

@app.post("/sign-invoice")
async def sign_invoice(xml_invoice: UploadFile):
    # Paths relative to the SDK root
    sdk_root = "/app/zatca-sdk"
    xml_path = "input_invoice.xml"
    signed_output_path = "signed_invoice.xml"

    # Save invoice into the SDK root
    with open(os.path.join(sdk_root, xml_path), "wb") as f:
        f.write(await xml_invoice.read())

    # Prepare environment and command
    env = {**os.environ, "FATOORA_HOME": "/app/zatca-sdk/Apps"}
    cmd = ["./Apps/fatoora", "-sign",
           "-invoice", xml_path,
           "-signedInvoice", signed_output_path]

    # Run CLI from the SDK root
    result = subprocess.run(
        cmd,
        cwd=sdk_root,       # run from /app/zatca-sdk so Data/Certificates can be found
        env=env,
        capture_output=True,
        text=True
    )

    # Return the result
    signed_file = os.path.join(sdk_root, signed_output_path)
    if os.path.exists(signed_file):
        with open(signed_file, "r") as f:
            signed_xml = f.read()
        return {"status": "success", "stdout": result.stdout, "signed_invoice": signed_xml}
    else:
        return {"status": "error",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": "Signed file not created"}

# existing debug and preflight endpoints stay the same
