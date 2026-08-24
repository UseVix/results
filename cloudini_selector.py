#!/usr/bin/env python3
import re
import sys
from pathlib import Path

import rosbag2_py


def get_kc_size(bag_path):
    """Return the ROS 2 bag size in bytes using rosbag2 metadata."""
    path = Path(bag_path)
    storage_id = "mcap" if path.suffix == ".mcap" else "sqlite3"
    bag_uri = path.parent if path.is_file() else path

    metadata = rosbag2_py.Info().read_metadata(str(bag_uri), storage_id)
    return sum(bag_file.size for bag_file in metadata.files)


regex = re.compile(r'0p(\d+)')
selected_files = {}
kc_precisions = [0.001,0.01,0.1,0.2,0.5]
with open(sys.argv[1], 'r') as file:
    f = file.readlines()
    for filename,size in zip(f[::2],f[1::2]):
        for match in regex.finditer(filename):
            precision = float("0." + match.group(1))

            selected_files[precision] = size
print("################")
print(sys.argv[1])
data_sequence_regex=re.compile(r"NewerCollege/(.*)/saved")
for key in sorted(selected_files):
    
    if key in kc_precisions:

        precision = f"{key:.3g}".replace(".", "p")
        data_sequence_match = data_sequence_regex.search(sys.argv[1])
        first_data_sequence_name = {data_sequence_match.group(1)}
        if first_data_sequence_name=="maths_institute":
            second_data_sequence_name = "maths_easy"
        kc_size = get_kc_size(
            f"/dataset/NewerCollege/{first_data_sequence_name}/bag/cloudini/{second_data_sequence_name}_res{precision}/restored_rosbag/data_0.mcap"
        )
        print(f"0p{key}: {selected_files[key]} {kc_size}")
    else:
        print(f"0p{key}: {selected_files[key]}")
print("################")
