import socket

from llmlaunchpad.llama import _is_port_free, find_free_port


HOST = "127.0.0.1"


def reserve_ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def test_is_port_free_returns_true_for_free_port():
    port = reserve_ephemeral_port()

    result = _is_port_free(port, host=HOST)

    assert result is True


def test_is_port_free_returns_false_for_listening_port():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((HOST, 0))
        listener.listen(1)
        port = int(listener.getsockname()[1])

        result = _is_port_free(port, host=HOST)

        assert result is False
    finally:
        listener.close()


def test_find_free_port_returns_preferred_when_free():
    preferred = reserve_ephemeral_port()

    result = find_free_port(preferred, host=HOST)

    assert result == preferred


def test_find_free_port_returns_different_valid_port_when_preferred_occupied():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((HOST, 0))
        listener.listen(1)
        preferred = int(listener.getsockname()[1])

        result = find_free_port(preferred, host=HOST)

        assert result != preferred
        assert 1 <= result <= 65535
    finally:
        listener.close()
