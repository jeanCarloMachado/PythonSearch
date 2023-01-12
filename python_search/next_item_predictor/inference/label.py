import math


def label_formula(row):
    return (
        math.log(row["times_3"])
        + math.log(row["times_2"] * 0.5)
        + math.log(row["global_pair"] * 0.01)
        + math.log(row["times_used_previous"] * 0.001)
        + math.log(row["times_used_previous_previous"] * 0.001)
    )
