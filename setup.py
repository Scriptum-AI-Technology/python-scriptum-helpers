from distutils.core import setup

setup(name="scriptum-helpers",
    version="1.0.0",
    description="Scriptum utilities and helpers",
    author="Javier Palacios",
    author_email="javier.palacios@scriptum-ai.com",
    packages=["scriptum_helpers", "scriptum_helpers.product"],
    install_requires=[
        "digitalocean",
        "uVault",
        "google-auth==2.40.2",
        "parse==1.19.0",
        "boto3",
        "jinja2",
        "pyyaml"
    ]
)
