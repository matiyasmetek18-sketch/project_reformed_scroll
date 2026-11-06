"""Routes, CSRF, and the `python -m loci.web` entry point."""

import os
import secrets
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
)

from loci import storage
from loci.feed import rank
from loci.quotes import author_for_slug, find_quote, merge_catalog

_PKG = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(_PKG, "templates"),
        static_folder=os.path.join(_PKG, "static"),
    )
    db_path = os.environ.get("LOCI_DB", os.path.join("instance", "loci.sqlite"))
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    secret = os.environ.get("LOCI_SECRET_KEY")
    if not secret:
        secret = secrets.token_hex(32)
    app.secret_key = secret
    app.config["LOCI_DB"] = db_path
    app.config["JSON_AS_ASCII"] = False
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    @app.before_request
    def _prepare_session():
        if not session.get("csrf"):
            session["csrf"] = secrets.token_hex(32)
        if session.get("shuffle_seed") is None:
            session["shuffle_seed"] = secrets.randbits(63)

    @app.teardown_appcontext
    def _close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    @app.context_processor
    def _inject():
        return {"csrf": session.get("csrf", ""), "nav": request.endpoint}

    @app.errorhandler(404)
    def _missing(_exc):
        return _message("That page is not on the scroll.", 404)

    @app.errorhandler(400)
    def _bad(exc):
        detail = getattr(exc, "description", None) or "The request was refused."
        return _message(detail, 400)

    def get_db():
        conn = g.get("db")
        if conn is None:
            conn = storage.connect(app.config["LOCI_DB"])
            g.db = conn
        return conn

    def catalog():
        return merge_catalog(storage.list_user_quotes(get_db()))

    def resolve(quote_id):
        return find_quote(catalog(), quote_id)

    def present(quote):
        conn = get_db()
        shown = dict(quote)
        quote_id = shown["id"]
        shown["amened"] = quote_id in storage.amen_ids(conn)
        shown["saved"] = quote_id in storage.saved_ids(conn)
        shown["note"] = storage.notes_map(conn).get(quote_id, "")
        shown["following"] = shown["author"] in storage.followed_authors(conn)
        return shown

    def ranked():
        conn = get_db()
        return rank(
            catalog(),
            storage.followed_authors(conn),
            storage.amen_ids(conn),
            session.get("shuffle_seed") or 0,
        )

    @app.route("/")
    def feed():
        quotes = [present(quote) for quote in ranked()]
        return render_template("feed.html", quotes=quotes, start=0, banner="")

    @app.route("/q/<quote_id>")
    def focus(quote_id):
        quotes = [present(quote) for quote in ranked()]
        start = 0
        found = False
        for index, quote in enumerate(quotes):
            if quote["id"] == quote_id:
                start = index
                found = True
                break
        banner = "" if found else "That line is not on the scroll."
        status = 200 if found else 404
        return render_template("feed.html", quotes=quotes, start=start, banner=banner), status

    @app.route("/explore")
    def explore():
        items = catalog()
        topics = {}
        timeline = {}
        undated = 0
        authors = []
        seen_authors = set()
        for quote in items:
            if quote["author"] not in seen_authors:
                seen_authors.add(quote["author"])
                authors.append(quote)
            if quote.get("year"):
                timeline.setdefault(quote["year"], []).append(quote)
            else:
                undated += 1
            for topic in quote.get("topics") or ():
                topics.setdefault(topic, []).append(quote)
        topic_rows = sorted(topics.items(), key=lambda pair: pair[0].lower())
        year_rows = sorted(timeline.items(), key=lambda pair: pair[0])
        return render_template(
            "explore.html",
            topics=topic_rows,
            timeline=year_rows,
            undated=undated,
            authors=authors,
            total=len(items),
        )

    @app.route("/theologian/<slug>")
    def theologian(slug):
        items = catalog()
        author = author_for_slug(items, slug)
        if not author:
            return _message("No theologian on the scroll uses that name.", 404)
        quotes = [present(quote) for quote in items if quote["author"] == author]
        return render_template("theologian.html", author=author, quotes=quotes, slug=slug)

    @app.route("/quaestio", methods=["GET"])
    def quaestio():
        items = catalog()
        if not items:
            return render_template("quaestio.html", question=None, result=None)
        question = _draw_question(items)
        session["quaestio"] = {
            "quote_id": question["quote_id"],
            "answer": question["answer"],
            "kind": question["kind"],
        }
        public = dict(question)
        public.pop("answer", None)
        return render_template("quaestio.html", question=public, result=None)

    @app.route("/quaestio", methods=["POST"])
    def quaestio_answer():
        refused = _guard()
        if refused is not None:
            return refused
        items = catalog()
        stored = session.get("quaestio") or {}
        quote = find_quote(items, stored.get("quote_id"))
        choice = (request.form.get("choice") or "").strip()
        if not quote or not stored:
            return redirect(url_for("quaestio"))
        correct = choice == stored.get("answer")
        result = {
            "correct": correct,
            "choice": choice,
            "answer": stored.get("answer") or "",
            "kind": stored.get("kind") or "author",
            "quote": present(quote),
        }
        session.pop("quaestio", None)
        if _wants_json():
            return jsonify(
                {
                    "ok": True,
                    "correct": correct,
                    "answer": result["answer"],
                    "quote_id": quote["id"],
                }
            )
        return render_template("quaestio.html", question=None, result=result)

    @app.route("/book")
    def book():
        return render_template("book.html", entries=_book_entries(), export_href=url_for("book_markdown"))

    @app.route("/book.md")
    def book_markdown():
        body = _markdown(_book_entries())
        response = make_response(body)
        response.headers["Content-Type"] = "text/markdown; charset=utf-8"
        response.headers["Content-Disposition"] = "attachment; filename=commonplace.md"
        return response

    @app.route("/add", methods=["GET"])
    def add_form():
        return render_template("add.html", error="")

    @app.route("/add", methods=["POST"])
    def add_quote():
        refused = _guard()
        if refused is not None:
            return refused
        try:
            fields = _quote_fields(request.form)
        except ValueError as exc:
            if _wants_json():
                return jsonify({"ok": False, "error": str(exc)}), 400
            return render_template("add.html", error=str(exc)), 400
        quote_id = storage.add_user_quote(get_db(), fields)
        if _wants_json():
            return jsonify({"ok": True, "id": quote_id})
        return redirect(url_for("focus", quote_id=quote_id))

    @app.route("/sources")
    def sources():
        checked = [quote for quote in catalog() if not quote.get("reader_added") and quote.get("source_url")]
        return render_template("sources.html", quotes=checked)

    @app.post("/quote/<quote_id>/amen")
    def amen(quote_id):
        refused = _guard()
        if refused is not None:
            return refused
        if resolve(quote_id) is None:
            abort(404)
        mode = request.form.get("mode") or "toggle"
        if mode == "set":
            state = storage.set_amen(get_db(), quote_id, True)
        else:
            state = storage.toggle_amen(get_db(), quote_id)
        return _respond({"ok": True, "amen": state, "id": quote_id})

    @app.post("/quote/<quote_id>/save")
    def save(quote_id):
        refused = _guard()
        if refused is not None:
            return refused
        if resolve(quote_id) is None:
            abort(404)
        state = storage.toggle_save(get_db(), quote_id)
        return _respond({"ok": True, "saved": state, "id": quote_id})

    @app.post("/quote/<quote_id>/note")
    def note(quote_id):
        refused = _guard()
        if refused is not None:
            return refused
        if resolve(quote_id) is None:
            abort(404)
        body = request.form.get("body") or ""
        if len(body) > 10000:
            abort(400, description="That note is too long.")
        stored = storage.set_note(get_db(), quote_id, body)
        return _respond({"ok": True, "note": stored, "id": quote_id})

    @app.post("/follow")
    def follow():
        refused = _guard()
        if refused is not None:
            return refused
        author = (request.form.get("author") or "").strip()
        known = {quote["author"] for quote in catalog()}
        if author not in known:
            abort(404)
        state = storage.toggle_follow(get_db(), author)
        return _respond({"ok": True, "following": state, "author": author})

    @app.post("/quote/<quote_id>/delete")
    def delete_quote(quote_id):
        refused = _guard()
        if refused is not None:
            return refused
        row_id = _user_row_id(quote_id)
        if row_id is None or not storage.delete_user_quote(get_db(), row_id):
            abort(404)
        return _respond({"ok": True, "deleted": quote_id})

    def _book_entries():
        items = catalog()
        by_id = {quote["id"]: quote for quote in items}
        conn = get_db()
        saved = storage.saved_ids(conn)
        notes = storage.notes_map(conn)
        wanted = []
        seen = set()
        for quote in items:
            if quote["id"] in saved or quote["id"] in notes:
                wanted.append(quote["id"])
                seen.add(quote["id"])
        for quote_id in sorted(saved | set(notes)):
            if quote_id not in seen:
                wanted.append(quote_id)
        entries = []
        for quote_id in wanted:
            quote = by_id.get(quote_id)
            if quote is None:
                entries.append(
                    {
                        "missing": True,
                        "id": quote_id,
                        "saved": quote_id in saved,
                        "note": notes.get(quote_id, ""),
                    }
                )
            else:
                shown = present(quote)
                shown["missing"] = False
                entries.append(shown)
        return entries

    return app


def _user_row_id(quote_id):
    if not quote_id or quote_id[0] != "u" or not quote_id[1:].isdigit():
        return None
    return int(quote_id[1:])


def _quote_fields(form):
    text = (form.get("text") or "").strip()
    author = (form.get("author") or "").strip()
    if not text:
        raise ValueError("Write the line you want to keep.")
    if not author:
        raise ValueError("Name whose line it is.")
    if len(text) > 8000 or len(author) > 200:
        raise ValueError("That entry is too long.")
    work = (form.get("work") or "").strip()
    citation = (form.get("citation") or "").strip()
    question = (form.get("question") or "").strip()
    latin = (form.get("latin") or "").strip()
    for label, value, limit in (
        ("work", work, 300),
        ("citation", citation, 300),
        ("question", question, 300),
        ("latin", latin, 8000),
    ):
        if len(value) > limit:
            raise ValueError("The %s is too long." % label)
    year_raw = (form.get("year") or "").strip()
    year = None
    if year_raw:
        if not year_raw.isdigit() or int(year_raw) < 1 or int(year_raw) > 9999:
            raise ValueError("Year should be a number, or left blank.")
        year = int(year_raw)
    topics = []
    for part in (form.get("topics") or "").split(","):
        topic = part.strip()
        if not topic:
            continue
        if len(topic) > 40:
            raise ValueError("Keep each topic label short.")
        if topic not in topics:
            topics.append(topic)
        if len(topics) > 8:
            raise ValueError("Eight topic labels is the limit.")
    return {
        "text": text,
        "author": author,
        "work": work,
        "citation": citation,
        "year": year,
        "latin": latin,
        "topics": topics,
        "question": question,
    }


def _draw_question(items):
    authors = []
    works = []
    citations = []
    for quote in items:
        if quote["author"] not in authors:
            authors.append(quote["author"])
        work = quote.get("work") or ""
        if work and work not in works:
            works.append(work)
        citation = quote.get("citation") or ""
        if citation and citation not in citations:
            citations.append(citation)
    quote = secrets.choice(items)
    if len(authors) >= 2:
        return _choice_question(quote, "author", "Who is this line from?", quote["author"], authors)
    if len(works) >= 2:
        return _choice_question(quote, "work", "Which work is this line from?", quote.get("work") or "", works)
    if len(citations) >= 2:
        return _choice_question(
            quote,
            "citation",
            "Which citation belongs to this line?",
            quote.get("citation") or "",
            citations,
        )
    only = quote["author"]
    return {
        "quote_id": quote["id"],
        "kind": "author",
        "prompt": "Who is this line from?",
        "choices": [only],
        "answer": only,
        "text": quote["text"],
        "question": quote.get("question") or "",
    }


def _choice_question(quote, kind, prompt, answer, pool):
    others = [item for item in pool if item != answer]
    picker = secrets.SystemRandom()
    picker.shuffle(others)
    choices = others[:3] + [answer]
    picker.shuffle(choices)
    return {
        "quote_id": quote["id"],
        "kind": kind,
        "prompt": prompt,
        "choices": choices,
        "answer": answer,
        "text": quote["text"],
        "question": quote.get("question") or "",
    }


def _book_quote_lines(entry):
    lines = []
    if entry.get("question"):
        lines.append(entry["question"])
        lines.append("")
    for line in (entry.get("text") or "").splitlines() or [""]:
        lines.append("> %s" % line)
    return lines


def _markdown(entries):
    lines = [
        "# Commonplace book",
        "",
        "Saved lines and notes from Loci. A line added by the reader is the reader's own text and is not a checked source.",
        "",
    ]
    if not entries:
        lines.append("Nothing is saved and there are no notes yet.")
        lines.append("")
        return "\n".join(lines)
    for entry in entries:
        if entry.get("missing"):
            lines.append("## Missing line")
            lines.append("")
            lines.append("Saved id `%s` is no longer in the catalog." % entry["id"])
            if entry.get("note"):
                lines.append("")
                lines.append("Note:")
                lines.append("")
                for note_line in entry["note"].splitlines():
                    lines.append("> %s" % note_line)
            lines.append("")
            continue
        lines.append("## %s" % entry["author"])
        lines.append("")
        lines.extend(_book_quote_lines(entry))
        lines.append("")
        bits = [entry.get("work") or "", entry.get("citation") or ""]
        citation = ", ".join(bit for bit in bits if bit)
        if entry.get("year"):
            citation = ("%s, %s" % (citation, entry["year"])).strip(", ")
        if citation:
            lines.append(citation)
        if entry.get("reader_added"):
            lines.append("Added by the reader. Not a checked source.")
        elif entry.get("source_url"):
            lines.append("Source: %s" % entry["source_url"])
        if entry.get("note"):
            lines.append("")
            lines.append("Note:")
            lines.append("")
            for note_line in entry["note"].splitlines():
                lines.append("> %s" % note_line)
        lines.append("")
    return "\n".join(lines)


def _wants_json():
    return request.headers.get("X-Requested-With") == "fetch"


def _csrf_ok():
    expected = session.get("csrf") or ""
    sent = request.form.get("csrf") or request.headers.get("X-CSRF") or ""
    if not expected or not sent:
        return False
    sent = str(sent)
    expected = str(expected)
    if len(sent) != len(expected):
        return False
    return secrets.compare_digest(sent, expected)


def _guard():
    if _csrf_ok():
        return None
    if _wants_json():
        return jsonify({"ok": False, "error": "csrf"}), 400
    abort(400, description="The form token did not match this session.")


def _safe_next():
    ref = request.referrer or ""
    if ref and urlparse(ref).netloc == request.host:
        return ref
    nxt = request.form.get("next") or ""
    if nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return url_for("feed")


def _respond(payload):
    if _wants_json():
        return jsonify(payload)
    return redirect(_safe_next())


def _message(message, status):
    page = render_template_string(
        """{% extends "base.html" %}
{% block title %}Loci{% endblock %}
{% block body %}
<section class="page empty">
  <h1>{{ message }}</h1>
  <p><a href="{{ url_for('feed') }}">Back to the feed</a></p>
</section>
{% endblock %}""",
        message=message,
    )
    return page, status


def main():
    port = int(os.environ.get("LOCI_PORT", "5070"))
    create_app().run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
