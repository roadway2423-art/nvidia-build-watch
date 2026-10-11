"""normalize 테스트 — M2에서 병합/first_seen 유지 케이스를 추가한다."""


def test_module_importable():
    import src.normalize

    assert src.normalize is not None
