from tools.kb_search import load_kb, search_kb_topk

def test_tfidf_search_basic(tmp_path):
    kb = [
        {"id":"A","title":"Checkout 500 on mobile","symptoms":["500","mobile"], "content":"Users get error 500 during checkout"},
        {"id":"B","title":"Payment declined","symptoms":["payment","card"], "content":"Card declined at payment gateway"},
        {"id":"C","title":"Login fails","symptoms":["login","401"], "content":"Users see 401 when logging in"}
    ]
    p = tmp_path / "kb.json"
    p.write_text(__import__('json').dumps(kb))
    load_kb(str(p))
    hits = search_kb_topk("checkout error 500 mobile", topk=2)
    assert len(hits) == 2
    assert hits[0]['id'] == "A"
    assert hits[0]['match_score'] > 0
