from pathlib import Path


SCRIPT = (Path(__file__).parents[1] / "generate_video.sh").read_text()
ROOT = Path(__file__).parents[2]
PYTHON_HELPERS = [
    (ROOT / "product-videos/batch_veo2.py").read_text(),
    (ROOT / "product-videos/generate_videos.py").read_text(),
]


def test_external_credentials_are_required_from_environment():
    for name in ("DEEPSEEK_API_KEY", "FAL_KEY", "GH_TOKEN"):
        assert f'required_env "{name}"' in SCRIPT


def test_operator_credentials_are_not_embedded_or_scraped():
    assert "sk-" not in SCRIPT
    assert "6e917d89-" not in SCRIPT
    assert ".credentials-dan.json" not in SCRIPT
    for helper in PYTHON_HELPERS:
        assert "6e917d89-" not in helper
        assert 'os.environ.get("FAL_KEY", "")' in helper


def test_dynamic_provider_payloads_are_json_encoded():
    assert 'DEEPSEEK_PAYLOAD=$(python3 -c' in SCRIPT
    assert 'FAL_PAYLOAD=$(python3 -c' in SCRIPT
