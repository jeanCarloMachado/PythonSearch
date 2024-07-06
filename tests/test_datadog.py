def test_datadog():
    from python_search.search.search_ui.search_utils import setup_datadog

    statsd = setup_datadog()
    assert statsd is not None
    # change the range to debug when needed
    for i in range(1):
        print(i)
        statsd.increment("test.increment")
