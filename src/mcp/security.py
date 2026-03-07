import ssl
from pathlib import Path

from OpenSSL import crypto


def generate_self_signed_cert(cert_path: Path, key_path: Path, days: int = 365):
    """Generate a self-signed SSL certificate for the MCP server"""
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)

    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "Local"
    cert.get_subject().L = "Localhost"
    cert.get_subject().O = "Dark Futures"
    cert.get_subject().OU = "MCP Server"
    cert.get_subject().CN = "localhost"

    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(days * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, "sha256")

    with open(cert_path, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(key_path, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

    print(f"Generated self-signed certificate: {cert_path}")


def create_ssl_context(cert_path: Path, key_path: Path) -> ssl.SSLContext:
    """Create SSL context for MCP server (local dev — self-signed)"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(str(cert_path), str(key_path))
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context
