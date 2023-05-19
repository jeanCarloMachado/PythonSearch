# type: ignore

import os

os.environ["NUMEXPR_MAX_THREADS"] = "10"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
