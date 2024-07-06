def setup_datadog():
    from datadog import initialize, statsd

    options = {
        "statsd_host": "127.0.0.1",
        "statsd_port": 8125,
    }

    initialize(**options)

    return statsd
