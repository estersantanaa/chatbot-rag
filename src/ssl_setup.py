"""Configura certificados SSL para requests/huggingface (comum no Windows)."""
import os
import sys


def configure_ssl() -> None:
    # Windows: usa o repositório de certificados do SO (proxy corporativo, etc.)
    if sys.platform == "win32":
        try:
            import pip_system_certs  # noqa: F401
        except ImportError:
            pass

    try:
        import certifi

        bundle = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)
    except ImportError:
        pass
