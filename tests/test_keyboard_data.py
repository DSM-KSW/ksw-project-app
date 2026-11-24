from view.keyboard_view import KEY_NAMES, KEYBOARD_BUTTON_DATA, vk_label

# US ANSI 풀배열 기준 키 개수
FULL_SIZE_KEY_COUNT = 104


def key_ids():
    return [data["id"] for data_list in KEYBOARD_BUTTON_DATA for data in data_list]


def test_full_size_key_count():
    assert len(key_ids()) == FULL_SIZE_KEY_COUNT


def test_key_ids_are_unique():
    # id가 겹치면 리매핑 하이라이트가 엉뚱한 키에 걸린다
    ids = key_ids()

    assert len(ids) == len(set(ids))


def test_key_names_cover_every_key():
    assert set(KEY_NAMES) == set(key_ids())


def test_vk_label_uses_key_names():
    # 키는 화면에 보이는 이름으로 표시한다 (0x11은 백엔드가 쓰는 공용 Ctrl)
    assert vk_label([0x11, 0x47, 0x43]) == "Ctrl+G+C"


def test_vk_label_shows_unknown_vk_code():
    # 화면에 없는 VK는 코드 그대로 보여준다
    assert vk_label([0x11, 0xFF]) == "Ctrl+VK 0xff"
