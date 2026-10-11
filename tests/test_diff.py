"""diff 엔진 테스트 — M2에서 신규/제거/카운트다운 케이스를 추가한다 (픽스처 기반, 네트워크 없음)."""


def test_module_importable():
    import src.diff

    assert src.diff is not None
