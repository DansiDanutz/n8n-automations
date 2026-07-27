import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "client_identity.py"
SPEC = importlib.util.spec_from_file_location("client_identity", MODULE_PATH)
client_identity = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(client_identity)


class ClientIdentityTests(unittest.TestCase):
    def test_untrusted_forwarding_header_cannot_replace_socket_peer(self):
        self.assertEqual(
            client_identity.resolve_client_ip(
                "203.0.113.9",
                "198.51.100.7",
                trusted_proxy_hops=0,
                trusted_proxy_cidrs=(),
            ),
            "203.0.113.9",
        )

    def test_configured_proxy_hops_are_selected_from_the_right(self):
        self.assertEqual(
            client_identity.resolve_client_ip(
                "10.0.0.5",
                "198.51.100.7, 192.0.2.12",
                trusted_proxy_hops=1,
                trusted_proxy_cidrs=("10.0.0.0/8",),
            ),
            "192.0.2.12",
        )
        self.assertEqual(
            client_identity.resolve_client_ip(
                "10.0.0.5",
                "198.51.100.7, 192.0.2.12",
                trusted_proxy_hops=2,
                trusted_proxy_cidrs=("10.0.0.0/8",),
            ),
            "198.51.100.7",
        )

    def test_invalid_selected_forwarded_values_are_rejected(self):
        for forwarded in ("attacker.example", "unknown", "198.51.100.7, bad"):
            with self.subTest(forwarded=forwarded):
                self.assertIsNone(
                    client_identity.resolve_client_ip(
                        "10.0.0.5",
                        forwarded,
                        trusted_proxy_hops=1,
                        trusted_proxy_cidrs=("10.0.0.0/8",),
                    )
                )

    def test_untrusted_prefix_does_not_change_selected_proxy_identity(self):
        self.assertEqual(
            client_identity.resolve_client_ip(
                "10.0.0.5",
                "bad, 198.51.100.7",
                trusted_proxy_hops=1,
                trusted_proxy_cidrs=("10.0.0.0/8",),
            ),
            "198.51.100.7",
        )

    def test_direct_clients_cannot_opt_into_forwarded_identity(self):
        self.assertEqual(
            client_identity.resolve_client_ip(
                "203.0.113.9",
                "198.51.100.7",
                trusted_proxy_hops=1,
                trusted_proxy_cidrs=("10.0.0.0/8",),
            ),
            "203.0.113.9",
        )


if __name__ == "__main__":
    unittest.main()
