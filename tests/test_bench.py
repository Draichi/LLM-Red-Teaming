from mta.eval.bench import BenchResult, BenchRow, normalize_model


def test_normalize_model():
    assert normalize_model("Qwen/Qwen2.5-72B-Instruct") == "featherless_ai/Qwen/Qwen2.5-72B-Instruct"
    assert normalize_model("featherless_ai/x/y") == "featherless_ai/x/y"
    assert normalize_model("anthropic/claude-opus-5") == "anthropic/claude-opus-5"
    # OpenAI API is never used here: `gpt-*` and `openai/*` are Featherless models
    assert normalize_model("gpt-4o") == "featherless_ai/gpt-4o"
    assert normalize_model("openai/gpt-oss-20b") == "featherless_ai/openai/gpt-oss-20b"
    assert normalize_model("microsoft/phi-2") == "featherless_ai/microsoft/phi-2"
    assert normalize_model("OBLITERATUS/Qwen3.8-27B-OBLITERATED") == "featherless_ai/OBLITERATUS/Qwen3.8-27B-OBLITERATED"


def test_headline_table():
    res = BenchResult("hotel_booking", [
        BenchRow("featherless_ai/A", False, 0, 7, True, 2, ["double_book_used_room", "parallel_premature_call"]),
        BenchRow("featherless_ai/B", True, 1, 7, True, 1, ["parallel_premature_call"]),
        BenchRow("featherless_ai/C", False, 0, 7, False, None, []),
    ])
    md = res.markdown()
    assert "single-turn vs multi-turn" in md
    assert "0/7" in md and "SOLVED (2t)" in md
    assert "double_book_used_room→parallel_premature_call" in md
    # single broke 1/3, multi broke 2/3
    assert "Single-turn broke 1/3 models. Multi-turn broke 2/3." in md
