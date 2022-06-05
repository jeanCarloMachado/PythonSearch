


class NextItemModel:
    """
    Class to centralize metadata about the model
    """
    x_columns = "key", "previous_key", "before_previous_key", "month", "day"
    label = 'label'
    columns = x_columns + (label,)
    # 384 is the size of the embedding
    # 3= key + prev_key + before prev_key
    # 1 month
    # 1 = day
    dimensions_X = 3 * 384 + 1 + 1
