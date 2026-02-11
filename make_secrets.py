import json
from pathlib import Path

key = json.loads(Path("key.json").read_text())

# 👉 Convertimos los \n del JSON a saltos reales ANTES
private_key_multiline = key["private_key"].replace("\\n", "\n")

toml = f"""[gcp_service_account]
type = "{key['type']}"
project_id = "{key['project_id']}"
private_key_id = "{key['private_key_id']}"
private_key = \"\"\"{private_key_multiline}\"\"\"
client_email = "{key['client_email']}"
client_id = "{key['client_id']}"
auth_uri = "{key['auth_uri']}"
token_uri = "{key['token_uri']}"
auth_provider_x509_cert_url = "{key['auth_provider_x509_cert_url']}"
client_x509_cert_url = "{key['client_x509_cert_url']}"
universe_domain = "{key.get('universe_domain', 'googleapis.com')}"
"""

Path(".streamlit").mkdir(exist_ok=True)
Path(".streamlit/secrets.toml").write_text(toml)

print("✅ secrets.toml creado correctamente")
