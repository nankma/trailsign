"""Verifies OracleKeyVaultResolver end to end against a real OCI Vault
secret -- not just that the code compiles, but that instance-principal
auth actually fetches and decodes a live secret.

Must run FROM INSIDE an OCI compute instance: instance-principal auth
(this project's real auth shape, confirmed against a sibling project's
own production config) has no static credential and only works there --
running this from a laptop will fail with an instance-metadata error,
which is expected, not a bug.

Takes the secret's own OCID via CLI arg only, never hardcoded, so this
file stays safe to commit with zero secrets in it -- pair with a
gitignored local-infra/ note for the real value (see .gitignore) and a
dev VM to SSH into and run this on.

    python tools/verify_oracle_vault.py --secret-ocid <ocid> [--expected test]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from trailsign import Settings  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--secret-ocid", required=True, help="OCID of the vault secret to fetch")
    parser.add_argument("--expected", help="if given, assert the resolved value equals this exactly")
    args = parser.parse_args()

    # credential_sources' vault_ocid/compartment_ocid are deliberately left
    # out here: get_secret_bundle-by-OCID under instance-principal auth
    # needs neither, so this check also doubles as confirmation of that
    # (see docs/design.md's "Still open" section).
    raw = {
        "credential_sources": {
            "dev-vault": {"type": "oracleKeyVault"},
        },
        "check": {
            "secret": {
                "trailsign-resolve": "oracleKeyVault",
                "source": "dev-vault",
                "secret_ocid": args.secret_ocid,
            },
        },
    }
    settings = Settings(raw)

    print("Fetching secret via OracleKeyVaultResolver (instance-principal auth)...")
    value = settings.resolved("check.secret", required=True)
    print(f"Resolved value: {value!r}")

    if args.expected is not None:
        if value != args.expected:
            print(f"FAIL: expected {args.expected!r}, got {value!r}")
            raise SystemExit(1)
        print("OK: resolved value matches --expected.")


if __name__ == "__main__":
    main()
