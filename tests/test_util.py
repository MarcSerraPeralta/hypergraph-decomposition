from hyper_decom.util import xor_lists, xor_two_probs


def test_xor_lists():
    a = [1, 2, 3]
    b = [1, 2]
    c = [1, 3, 5]

    output = xor_lists(a, b, c)

    assert output == (1, 5)

    return


def test_xor_two_probs():
    output = xor_two_probs(1, 0)
    assert output == 1

    output = xor_two_probs(0.5, 0.5)
    assert output == 0.5
    return
