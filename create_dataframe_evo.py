#!/usr/bin/env python3

import os
from pathlib import Path
import re
import pandas as pd
import sys
from evo.tools import file_interface
path_prefix = sys.argv[1]
df = pd.DataFrame(columns=[
    "data_sequence",
    "method",
    "encode_speed",
    "decode_speed",
    "quantization_precision",
    "slam_method",
    "rmse",
    "mean",
    "median",
    "std",
    "min",
    "max",
    "sse"
])
for root, dirs, files in os.walk(path_prefix):
    for file in files:
        if file.endswith("_tum"):
            data = file_interface.load_res_files(os.path.join(root, file)).stats
            folder = Path(root).parts
            data['slam_method'] = folder[-4]
            data['data_sequence'] = folder[-2]
            data['method'] = folder[-1]
            if method == "draco":
                data['encode_speed'] = int(re.search("ES:(\d)+", file).group(1))
                data['decode_speed'] = int(re.search("DS:(\d)+", file).group(1))
                data['quantization_precision'] = int(re.search("QP:(\d)+", file).group(1))
            if method == "cloudini":
                data['encode_speed'] = None
                data['decode_speed'] = None
                data['quantization_precision'] = float(re.search("0p\d+", file).group(0).replace("p", "."))
            df.loc[len(df)] = data
output_csv_path = os.path.join(path_prefix, "summary.csv")
if not os.path.exists(output_csv_path):
    df.to_csv(output_csv_path, index=False)
elif not df.empty:
    print(f"Summary CSV already exists for {root}. Skipping.")
