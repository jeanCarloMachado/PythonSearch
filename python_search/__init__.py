# type: ignore

import os

os.environ["NUMEXPR_MAX_THREADS"] = "10"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

os.environ["DD_SERVICE"] = "python-search"
os.environ["DD_ENV"] = "local"
os.environ["DD_LOGS_INJECTION"] = "true"
os.environ["DD_PROFILING_ENABLED"] = "true"
# os.environ['DD_TRACE_DEBUG'] = 'true'

# from ddtrace.profiling import Profiler
# import sys
# prof = Profiler(
#    env="local",  # if not specified, falls back to environment variable DD_ENV
#    service="python_search",  # if not specified, falls back to environment variable DD_SERVICE
#    version=str(sys.argv[0]),   # if not specified, falls back to environment variable DD_VERSION
#    tags={'entrypoint': sys.argv[0]},
# )
# prof.start()
