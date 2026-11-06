"""Feed order for this app.

Followed authors come first, quotes not yet Amen'd come before Amen'd
ones, and a shuffle seeded for the session breaks the remaining ties.
The shuffle places are fixed for a given seed, so a later Amen moves a
line between groups without reshuffling the rest.
"""

import random


def rank(quotes, followed_authors, amened_ids, seed):
    followed = set(followed_authors or ())
    amened = set(amened_ids or ())
    order = [quote.get("id") for quote in quotes]
    random.Random(seed).shuffle(order)
    place = {}
    for index, quote_id in enumerate(order):
        place[quote_id] = index

    def sort_key(quote):
        follow_band = 0 if quote.get("author") in followed else 1
        amen_band = 0 if quote.get("id") not in amened else 1
        return (follow_band, amen_band, place.get(quote.get("id"), 0))

    return sorted(quotes, key=sort_key)
