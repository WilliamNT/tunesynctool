from itertools import islice
from typing import List

def batch(items: List, chunk_size: int):
    """
    Split a list of tracks into batches of a given size.

    :param tracks: The list of tracks to split.
    :param batch_size: The size of each batch.
    :return: A list of lists of Track objects.
    """

    iterator = iter(items)
    while chunk := tuple(islice(iterator, chunk_size)):
        yield chunk