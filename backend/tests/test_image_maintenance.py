from scripts.manter_imagens_catalogo import should_try_alternative


def test_temporary_network_failure_keeps_current_reference_until_threshold() -> None:
    assert not should_try_alternative(
        status_code=None, consecutive_failures=0, failure_threshold=3
    )
    assert not should_try_alternative(
        status_code=503, consecutive_failures=1, failure_threshold=3
    )
    assert should_try_alternative(
        status_code=None, consecutive_failures=2, failure_threshold=3
    )


def test_definitive_not_found_or_forbidden_tries_same_product_alternative() -> None:
    for status in (403, 404):
        assert should_try_alternative(
            status_code=status, consecutive_failures=0, failure_threshold=3
        )
