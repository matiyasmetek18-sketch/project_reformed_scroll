# Loci

Loci is a single-reader scroll for lines that have been checked against a page, plus lines you add yourself. It is a small Flask app. The only dependency is Flask. Storage is the standard-library `sqlite3`.

## Run

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m loci.web
```

The server binds to `127.0.0.1` only. The default port is `5070`.

| Variable | Default | Role |
| --- | --- | --- |
| `LOCI_DB` | `instance/loci.sqlite` | SQLite file, created on first use |
| `LOCI_PORT` | `5070` | Port |
| `LOCI_SECRET_KEY` | a new random value each start | Flask session secret |

There is one reader and no accounts. The database holds amens, saves, notes, follows, and quotes you add. Built-in lines live in code, not in the database.

## Feed order

This is the current rule of this app. It is not a recovery of an earlier formula.

1. Quotes from authors you follow come first.
2. Quotes you have not Amen'd come before quotes you have Amen'd.
3. Within those groups, order is a shuffle fixed for the browser session.

Amen'ing a line moves it between groups. It does not reshuffle the session.

## What the scroll does

- The feed is one card tall. Move with a vertical swipe, the wheel, the arrow keys, or the on-screen arrows.
- Amen toggles. A double-tap or double-click bursts a heart and Amens the line.
- Save toggles. Notes are kept per line.
- Follow and unfollow a theologian from the card or their page.
- Share uses the Web Share API when the browser has it, and otherwise copies the quote link.
- Latin is a toggle, and only when that quote's checked page printed Latin.
- Lectio advances the feed on its own. The same control pauses it.
- Explore lists loci (topic labels) and a timeline of years the sources state.
- Theologian pages are built from the merged catalog.
- Quaestio draws a question only from quotes that are actually in the catalog.
- The commonplace book collects saves and notes and exports Markdown at `/book.md`.
- Add a line of your own, or delete it. Reader quote ids look like `u1`. Built-in ids are short slugs.
- Sources lists each built-in quote and the page it was checked against. Reader lines are not listed there.

Every POST sends a `csrf` form field or an `X-CSRF` header, checked against the session token. If the request header `X-Requested-With` is `fetch`, the response is JSON. Otherwise the app redirects back.

With JavaScript, the class `js` is added to `<html>`. Words, chips, the citation, and the big quote mark are hidden only in that case, and they show when a card has `active` or `shown`. Without the class, the text stays visible.

## Checked catalog

A built-in line is included only after its source page was opened and the wording checked. Dates, topic labels, and Latin are stored only when that page states them. The pages below do not give topic labels for these lines, so the loci list stays empty until you add labels of your own.

| Id | Author, as the page puts it | Year the page states | Latin on that page | Source opened |
| --- | --- | --- | --- | --- |
| `wsc-q1` | Westminster Assembly | 1647 | yes | https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html |
| `wsc-q4` | Westminster Assembly | 1647 | yes | https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html |
| `wsc-q14` | Westminster Assembly | 1647 | yes | https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html |
| `wsc-q33` | Westminster Assembly | 1647 | yes | https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html |
| `wsc-q86` | Westminster Assembly | 1647 | yes | https://www.ccel.org/ccel/schaff/creeds3/creeds3.iv.xviii.html |
| `hc-q1` | Zacharius Ursinus and Caspar Olevianus, traditionally attributed | 1563 | no | https://www.rca.org/about/theology/creeds-and-confessions/the-heidelberg-catechism/ |
| `hc-q2` | Zacharius Ursinus and Caspar Olevianus, traditionally attributed | 1563 | no | https://www.rca.org/about/theology/creeds-and-confessions/the-heidelberg-catechism/ |
| `inst-1-1-1` | John Calvin, translated by Henry Beveridge | 1559 | no | https://www.ccel.org/ccel/c/calvin/institutes/cache/institutes.txt |

Question 4 of the Shorter Catechism is split by a page break on the Schaff page. The page number between the two halves is not part of the quotation. The Heidelberg page prints proof numbers inside the answers; those numbers are not part of the quotation. Calvin's English sentence is Beveridge's translation. The same file dates the preface Geneva, 1st August 1559, and says the work received its definitive edition in 1559. It does not print the Latin of that sentence.

## Layout

```
loci/quotes.py     built-in catalog
loci/storage.py    sqlite
loci/feed.py       ranking
loci/web.py        routes, CSRF, entry point
loci/templates/    pages
loci/static/       loci.css and loci.js
```

Python 3.9 is enough. The code does not use 3.10-only syntax.
