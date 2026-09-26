from unittest.mock import patch

from vidius.main import main


def test_main_prompt_only():
    with (
        patch("sys.argv", ["vidius", "test prompt"]),
        patch("vidius.main.VideoGenerator") as MockGen,
        patch("vidius.main.HistoryManager"),
    ):
        mock_gen_instance = MockGen.return_value
        main()

        mock_gen_instance.generate.assert_called_once()
        call_args = mock_gen_instance.generate.call_args[1]
        assert call_args["prompt"] == "test prompt"
        assert call_args["duration"] == 8
        assert call_args["generate_audio"] is True


def test_main_no_audio():
    with (
        patch("sys.argv", ["vidius", "test prompt", "--no-audio"]),
        patch("vidius.main.VideoGenerator") as MockGen,
        patch("vidius.main.HistoryManager"),
    ):
        mock_gen_instance = MockGen.return_value
        main()

        call_args = mock_gen_instance.generate.call_args[1]
        assert call_args["generate_audio"] is False


def test_main_history():
    with (
        patch("sys.argv", ["vidius", "--history"]),
        patch("vidius.main.VideoGenerator") as MockGen,
        patch("vidius.main.HistoryManager") as MockHist,
    ):
        mock_hist_instance = MockHist.return_value
        main()

        mock_hist_instance.display.assert_called_once()
        mock_gen_instance = MockGen.return_value
        mock_gen_instance.generate.assert_not_called()


def test_model_alias_resolves():
    from vidius.config import MODELS, settings

    with (
        patch("sys.argv", ["vidius", "test prompt", "-m", "lite"]),
        patch("vidius.main.VideoGenerator"),
        patch("vidius.main.HistoryManager"),
    ):
        main()
    assert settings.model_id == MODELS["lite"]


def test_client_uses_api_key():
    from vidius import api_client
    from vidius.config import settings

    with patch.object(settings, "api_key", "fake-key"), patch("vidius.api_client.genai.Client") as MockClient:
        api_client.VideoGenerator()
    MockClient.assert_called_once_with(api_key="fake-key")


def test_api_key_mode_omits_generate_audio():
    from unittest.mock import MagicMock

    from vidius import api_client
    from vidius.config import settings

    with patch.object(settings, "api_key", "fake-key"), patch("vidius.api_client.genai.Client") as MockClient:
        client = MagicMock()
        MockClient.return_value = client
        gen = api_client.VideoGenerator()
        with patch.object(gen, "_wait_and_save"):
            gen.generate(prompt="p", output_file="o.mp4", generate_audio=False)
    cfg = client.models.generate_videos.call_args.kwargs["config"]
    assert cfg.generate_audio is None
