"""Built-in catalog.

Each line below was copied after the source page was opened. Wording,
dates, Latin, and the author line follow that page. Footnote numbers
and a page-break numeral are not part of the quotation. Nothing in this
module is a guess filled in from memory.
"""

import re

# Checked  against the page named on each item.
QUOTES = (
    {
        "id": "wsc-q1",
        "author": "Westminster Assembly",
        "work": "The Shorter Catechism",
        "citation": "Question 1",
        "year": 1647,
        "question": "What is the chief end of man?",
        "text": "Man's chief end is to glorify God, and to enjoy him forever.",
        "latin": "Præcipuus hominis finis est, Deum glorificare, eodemque frui in æternum.",
        "topics": (),
        "attribution": "",
        "source_url": "https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html",
        "source_note": "The page says this catechism was prepared by the Westminster Assembly in 1647. English and Latin are the parallel answer printed for Question 1.",
    },
    {
        "id": "wsc-q4",
        "author": "Westminster Assembly",
        "work": "The Shorter Catechism",
        "citation": "Question 4",
        "year": 1647,
        "question": "What is GOD?",
        "text": "God is a Spirit, infinite, eternal, and unchangeable, in his being, wisdom, power, holiness, justice, goodness, and truth.",
        "latin": "Deus est Spiritus essentia, sapientia, potentia, sanctitate, justitia, bonitate ac veritate infinitus, æternus, ac immutabilis.",
        "topics": (),
        "attribution": "",
        "source_url": "https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html",
        "source_note": "The English answer and the Latin answer are each split by a page break. The page number between the halves is not part of the text.",
    },
    {
        "id": "wsc-q14",
        "author": "Westminster Assembly",
        "work": "The Shorter Catechism",
        "citation": "Question 14",
        "year": 1647,
        "question": "What is sin?",
        "text": "Sin is any want of conformity unto, or transgression of, the law of God.",
        "latin": "Peccatum est defectus quilibet conformitatis cum lege Divina, seu quævis ejusdem transgressio.",
        "topics": (),
        "attribution": "",
        "source_url": "https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html",
        "source_note": "English and Latin are the parallel answer printed for Question 14.",
    },
    {
        "id": "wsc-q33",
        "author": "Westminster Assembly",
        "work": "The Shorter Catechism",
        "citation": "Question 33",
        "year": 1647,
        "question": "What is justification?",
        "text": "Justification is an act of God's free grace, wherein he pardoneth all our sins, and accepteth us as righteous in his sight, only for the righteousness of Christ imputed to us, and received by faith alone.",
        "latin": "Justificatio est actus gratiæ Dei gratuitæ, quo peccata nobis condonat omnia, nosque tanquam justos in conspectu suo acceptat, propter solam Christi justitiam nobis imputatam, per fidem tantum apprehensam.",
        "topics": (),
        "attribution": "",
        "source_url": "https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html",
        "source_note": "English and Latin are the parallel answer printed for Question 33.",
    },
    {
        "id": "wsc-q86",
        "author": "Westminster Assembly",
        "work": "The Shorter Catechism",
        "citation": "Question 86",
        "year": 1647,
        "question": "What is faith in Jesus Christ?",
        "text": "Faith in Jesus Christ is a saving grace, whereby we receive and rest upon him alone for salvation, as he is offered to us in the gospel.",
        "latin": "Fides in Jesum Christum est gratia salvifica, qua illum recipimus, eoque solo nitimur, ut salvi simus, prout ille nobis offertur in evangelio.",
        "topics": (),
        "attribution": "",
        "source_url": "https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html",
        "source_note": "English and Latin are the parallel answer printed for Question 86.",
    },
    {
        "id": "hc-q1",
        "author": "Zacharius Ursinus and Caspar Olevianus",
        "work": "Heidelberg Catechism",
        "citation": "Lord's Day 1, Q&A 1",
        "year": 1563,
        "question": "What is your only comfort in life and in death?",
        "text": "That I am not my own, but belong—body and soul, in life and in death—to my faithful Savior, Jesus Christ. He has fully paid for all my sins with his precious blood, and has set me free from the tyranny of the devil. He also watches over me in such a way that not a hair can fall from my head without the will of my Father in heaven; in fact, all things must work together for my salvation. Because I belong to him, Christ, by his Holy Spirit, assures me of eternal life and makes me wholeheartedly willing and ready from now on to live for him.",
        "latin": "",
        "topics": (),
        "attribution": "traditionally attributed",
        "source_url": "https://www.rca.org/about/theology/creeds-and-confessions/the-heidelberg-catechism/",
        "source_note": "The page says the catechism was written in 1563 and is traditionally attributed to Zacharius Ursinus and Caspar Olevianus. Proof numbers printed in the answer are not part of the quotation. That page does not print a Latin text.",
    },
    {
        "id": "hc-q2",
        "author": "Zacharius Ursinus and Caspar Olevianus",
        "work": "Heidelberg Catechism",
        "citation": "Lord's Day 1, Q&A 2",
        "year": 1563,
        "question": "What must you know to live and die in the joy of this comfort?",
        "text": "Three things: first, how great my sin and misery are; second, how I am set free from all my sins and misery; third, how I am to thank God for such deliverance.",
        "latin": "",
        "topics": (),
        "attribution": "traditionally attributed",
        "source_url": "https://www.rca.org/about/theology/creeds-and-confessions/the-heidelberg-catechism/",
        "source_note": "The page says the catechism was written in 1563 and is traditionally attributed to Zacharius Ursinus and Caspar Olevianus. Proof numbers printed in the answer are not part of the quotation. That page does not print a Latin text.",
    },
    {
        "id": "inst-1-1-1",
        "author": "John Calvin",
        "work": "Institutes of the Christian Religion",
        "citation": "Book First, Chapter 1, section 1. Translated by Henry Beveridge.",
        "year": 1559,
        "question": "",
        "text": "Our wisdom, in so far as it ought to be deemed true and solid Wisdom, consists almost entirely of two parts: the knowledge of God and of ourselves.",
        "latin": "",
        "topics": (),
        "attribution": "",
        "source_url": "https://www.ccel.org/ccel/c/calvin/institutes/cache/institutes.txt",
        "source_note": "The file names John Calvin as author and Henry Beveridge as translator. The preface on that file is dated Geneva, 1st August 1559, and the introduction says the work received its definitive edition in 1559. The sentence is the opening of Book First, Chapter 1, section 1. The file gives no Latin for this sentence.",
    },
)


def _slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "author"


def _copy_builtin(raw):
    quote_id = raw["id"]
    if quote_id.startswith("u") and quote_id[1:].isdigit():
        raise RuntimeError("built-in id collides with reader ids")
    if not raw.get("text") or not raw.get("author") or not raw.get("source_url"):
        raise RuntimeError("built-in quote is incomplete")
    return {
        "id": quote_id,
        "author": raw["author"],
        "work": raw.get("work") or "",
        "citation": raw.get("citation") or "",
        "year": raw.get("year"),
        "question": raw.get("question") or "",
        "text": raw["text"],
        "latin": raw.get("latin") or "",
        "topics": list(raw.get("topics") or ()),
        "attribution": raw.get("attribution") or "",
        "source_url": raw["source_url"],
        "source_note": raw.get("source_note") or "",
        "reader_added": False,
    }


def builtin_quotes():
    seen = set()
    copied = []
    for raw in QUOTES:
        item = _copy_builtin(raw)
        if item["id"] in seen:
            raise RuntimeError("duplicate built-in id")
        seen.add(item["id"])
        copied.append(item)
    return copied


def _with_slugs(items):
    used = {}
    author_slugs = {}
    for item in items:
        author = item["author"]
        if author not in author_slugs:
            base = _slug(author)
            slug = base
            number = 2
            while slug in used and used[slug] != author:
                slug = "%s-%d" % (base, number)
                number += 1
            used[slug] = author
            author_slugs[author] = slug
        item["author_slug"] = author_slugs[author]
    return items


def merge_catalog(user_quotes):
    """One catalog: checked lines, then the reader's own lines."""
    items = builtin_quotes()
    for quote in user_quotes or ():
        items.append(dict(quote))
    return _with_slugs(items)


def find_quote(items, quote_id):
    for item in items:
        if item["id"] == quote_id:
            return item
    return None


def author_for_slug(items, slug):
    for item in items:
        if item.get("author_slug") == slug:
            return item["author"]
    return None
