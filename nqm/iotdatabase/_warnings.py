"""Stores custom warnings
"""

class EmptyDictWarning(UserWarning):
    """Warning for when an empty dict is passed as an input.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
