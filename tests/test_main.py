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
