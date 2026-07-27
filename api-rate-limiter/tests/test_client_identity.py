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
                "203.0.113.9", "198.51.100.7", trusted_proxy_hops=0
            ),
            "203.0.113.9",
        )

    def test_configured_proxy_hops_are_selected_from_the_right(self):
        self.assertEqual(
            client_identity.resolve_client_ip(
                "10.0.0.5",
                "198.51.100.7, 192.0.2.12",
                trusted_proxy_hops=1,
            ),
            "192.0.2.12",
        )
        self.assertEqual(
            client_identity.resolve_client_ip(
                "10.0.0.5",
                "198.51.100.7, 192.0.2.12",
                trusted_proxy_hops=2,
            ),
            "198.51.100.7",
        )

    def test_invalid_forwarded_values_fall_back_to_socket_peer(self):
        for forwarded in ("attacker.example", "unknown", "", "198.51.100.7, bad"):
            with self.subTest(forwarded=forwarded):
                self.assertEqual(
                    client_identity.resolve_client_ip(
                        "203.0.113.9", forwarded, trusted_proxy_hops=1
                    ),
                    "203.0.113.9",
                )


if __name__ == "__main__":
    unittest.main()
