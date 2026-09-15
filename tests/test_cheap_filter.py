from mta.judge.cheap_filter import is_obvious_refusal


def test_empty_is_refusal():
    assert is_obvious_refusal("")
    assert is_obvious_refusal("   ")


def test_short_hard_refusal():
    assert is_obvious_refusal("I'm sorry, but I can't help with that.")
    assert is_obvious_refusal("I cannot provide that information.")


def test_substantive_reply_is_not_refusal():
    assert not is_obvious_refusal(
        "Sure, here is a detailed breakdown of the process. " + "step. " * 100
    )


def test_long_soft_refusal_then_content_is_left_for_judge():
    # opens like a refusal but continues at length -> NOT obvious; judge decides
    reply = "I'm sorry, but I can't do exactly that. However, " + "detail " * 200
    assert not is_obvious_refusal(reply)


def test_plain_helpful_reply():
    assert not is_obvious_refusal("Here are three approaches you could take.")
