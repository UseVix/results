#!/usr/bin/env python3

import sys
from pathlib import Path

import pandas as pd




left = pd.read_csv(sys.argv[1])
right = pd.read_csv(sys.argv[2])


merged_outer = left.merge(
    right,
    how="outer",
)


merged_inner = left.merge(
    right,
    how="inner"
)

print("Left columns:", left["data_sequence"].unique())
print("Right columns:", right["data_sequence"].unique())
print("Left shape:", left.shape)
print("Right shape:", right.shape)
print("Intersection of columns size:", len(set(left.columns).intersection(set(right.columns))))
print("Merged inner shape:", merged_inner.shape)
print("Merged outer shape:", merged_outer.shape)
def lookup_value(dataframe):
    print(
        dataframe.loc[
            (dataframe["data_sequence"] == "quad_easy")
            & (dataframe["method"] == "draco")
            & (dataframe["encode_speed"] == 10)
            & (dataframe["decode_speed"] == 10)
            & (dataframe["quantization_precision"] == 10)
        ]
    )
print("Inner lookup:")
lookup_value(merged_inner)
print("Outer lookup:")
lookup_value(merged_outer)
print("Left lookup:")
lookup_value(left)
print("Right lookup:")
lookup_value(right)
#print("KISS-ICP lookup:")
print("Cloister Cloudini 0p2 lookup:")
print(left.loc[
    (left["data_sequence"] == "cloister") & (left["quantization_precision"] == 0.2) & (left["method"] == "cloudini")
])
print("left unique data_sequence:", left["data_sequence"].unique())
print("right unique data_sequence:", right["data_sequence"].unique())
print("merged_inner unique data_sequence:", merged_inner["data_sequence"].unique())
print("merged_outer unique data_sequence:", merged_outer["data_sequence"].unique())
merged_inner.to_csv("merged_inner.csv", index=False)
merged_outer.to_csv("merged_outer.csv", index=False)
