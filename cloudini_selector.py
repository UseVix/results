#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path

import rosbag2_py


def get_kc_size(bag_path):
    """Return the ROS 2 bag size in bytes using ``ros2 bag info``."""
    path = Path(bag_path)
    result = subprocess.run(
        ["ros2", "bag", "info", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    size_match = re.search(
        r"^Bag size:(.*)$",
        result.stdout,
        re.MULTILINE,
    ).group(1)
    if size_match is None:
        raise RuntimeError(f"Could not parse bag size from ros2 bag info for {path}")

    #size = float(size_match.group(1))
    #unit = size_match.group(2)
    #units = {"B": 1, "KB": 1000, "MB": 1000**2, "GB": 1000**3, "TB": 1000**4}
    #units.update({f"{prefix}iB": 1024 ** index for index, prefix in enumerate(("", "K", "M", "G", "T"))})
    return size_match


regex = re.compile(r'0p(\d+)')
selected_files = {}
kc_precisions = [0.001,0.01,0.1,0.2,0.5]
with open(sys.argv[1], 'r') as file:
    f = file.readlines()
    for filename,size in zip(f[::2],f[1::2]):
        for match in regex.finditer(filename):
            precision = float("0." + match.group(1))

            selected_files[precision] = size[:-1]
print("################")
print(sys.argv[1])
data_sequence_regex=re.compile(r"NewerCollege/(.*)/saved")
for key in sorted(selected_files):
    
    if key in kc_precisions:

        precision = f"{key:.3g}".replace(".", "p")
        data_sequence_match = data_sequence_regex.search(sys.argv[1])
        first_data_sequence_name = data_sequence_match.group(1)
        second_data_sequence_name = first_data_sequence_name
        if first_data_sequence_name=="maths_institute":
            second_data_sequence_name = "maths_easy"
        if first_data_sequence_name == "underground_mine":
            second_data_sequence_name = "underground_easy"
        kc_size = get_kc_size(
            f"/dataset/NewerCollege/{first_data_sequence_name}/bag/cloudini/{second_data_sequence_name}_res{precision}/restored_rosbag/data_0.mcap"
        )
        print(f"{key}: {selected_files[key]} {kc_size}")
    else:
        print(f"{key}: {selected_files[key]}")
print("################")
