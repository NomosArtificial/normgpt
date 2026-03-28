from unittest.mock import MagicMock, patch


def test_generate_title():
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="  My Title  "))]
    )

    with patch("app.db", mock_db), patch("app.client", mock_client):
        from app import _generate_title

        _generate_title("conv-123", "Hello world")

    mock_db.set_conversation_title.assert_called_once_with("conv-123", "My Title")
