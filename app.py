from fastapi import FastAPI, UploadFile
import subprocess, os

app = FastAPI()

@app.post("/sign-invoice")
async def sign_invoice(xml_invoice: UploadFile):
    sdk_root = "/app/zatca-sdk"                         # root of the SDK
    xml_file   = "input_invoice.xml"
    signed_file = "signed_invoice.xml"

    # write invoice into SDK directory
    with open(os.path.join(sdk_root, xml_file), "wb") as f:
        f.write(await xml_invoice.read())

    # environment: FATOORA_HOME must point to Apps
     env = {**os.environ, "FATOORA_HOME": f"{sdk_root}/Apps"}

    # run the CLI from the SDK root
    cmd = ["java", "-jar", f"{sdk_root}/Apps/zatca-einvoicing-sdk-238-R3.4.3.jar",
       "-config", f"{sdk_root}/Configuration/config.json",
       "-cmd", "sign",
       "-input", f"{sdk_root}/input_invoice.xml",
       "-output", f"{sdk_root}/signed_invoice.xml"]

    result = subprocess.run(
        cmd,
        cwd=sdk_root,
        env=env,
        capture_output=True,
        text=True
    )

    if os.path.exists(os.path.join(sdk_root, signed_file)):
        with open(os.path.join(sdk_root, signed_file), "r") as f:
            signed_xml = f.read()
        return {"status": "success", "signed_invoice": signed_xml, "stdout": result.stdout}
    else:
        return {"status": "error",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": "Signed file not created"}
