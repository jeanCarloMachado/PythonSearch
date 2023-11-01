# type: ignore

import os

os.environ["NUMEXPR_MAX_THREADS"] = "10"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

os.environ['DD_SERVICE'] = 'python-search'
os.environ['DD_ENV'] = 'local'
os.environ['DD_LOGS_INJECTION'] = 'true'
os.environ['DD_PROFILING_ENABLED'] = 'true'
#os.environ['DD_TRACE_DEBUG'] = 'true'

#from ddtrace.profiling import Profiler

#prof = Profiler(
#    env="local",  # if not specified, falls back to environment variable DD_ENV
#    service="python_search",  # if not specified, falls back to environment variable DD_SERVICE
#    version="1.0.3",   # if not specified, falls back to environment variable DD_VERSION
#)
#prof.start()