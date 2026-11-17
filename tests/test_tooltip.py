from components import tooltip_height


def test_tooltip_height_with_no_remapping():
    # 투명 여백(8+8) + 안쪽 여백(8+8) + 추가 버튼(24)
    assert tooltip_height(0) == 56


def test_tooltip_height_grows_by_one_row():
    # 리매핑 한 줄(24) + 줄 간격(12)
    step = tooltip_height(1) - tooltip_height(0)

    assert step == 36
    assert tooltip_height(3) - tooltip_height(2) == step
