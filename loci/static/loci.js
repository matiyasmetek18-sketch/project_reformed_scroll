(function () {
  document.documentElement.classList.add("js");

  function boot() {
    var stage = document.getElementById("stage");
    var reel = document.getElementById("reel");

    document.querySelectorAll(".saying").forEach(wrapWords);
    document.querySelectorAll("form.inline, form.note-form, form.delete-form").forEach(bindForm);
    document.querySelectorAll("a.share").forEach(function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
        shareCard(link.closest(".card") || link);
      });
    });
    document.querySelectorAll(".card").forEach(bindDouble);

    if (!stage || !reel) return;

    var cards = Array.prototype.slice.call(reel.querySelectorAll(".card"));
    if (!cards.length) return;

    var index = parseInt(reel.getAttribute("data-start") || "0", 10);
    if (isNaN(index) || index < 0 || index >= cards.length) index = 0;

    var progress = document.getElementById("progress");
    var prev = document.getElementById("prev");
    var next = document.getElementById("next");
    var lectio = document.getElementById("lectio");
    var lectioTimer = 0;
    var wheelLock = 0;
    var startY = 0;
    var deltaY = 0;
    var dragging = false;
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prev) prev.hidden = false;
    if (next) next.hidden = false;
    if (lectio) lectio.hidden = false;

    function height() {
      return stage.clientHeight || window.innerHeight;
    }

    function place(animate) {
      if (!animate) reel.classList.add("dragging");
      reel.style.transform = "translateY(" + (-index * height()) + "px)";
      if (!animate) {
        void reel.offsetWidth;
        reel.classList.remove("dragging");
      }
    }

    function reveal(card) {
      cards.forEach(function (other) {
        var on = other === card;
        other.classList.toggle("active", on);
        other.setAttribute("aria-hidden", on ? "false" : "true");
      });
      if (reduce) {
        card.classList.add("active", "shown");
        return;
      }
      card.classList.remove("active", "shown");
      void card.offsetWidth;
      card.classList.add("active", "shown");
    }

    function go(nextIndex, options) {
      if (!cards.length) return;
      index = Math.max(0, Math.min(cards.length - 1, nextIndex));
      place(true);
      reveal(cards[index]);
      if (progress) progress.textContent = (index + 1) + " / " + cards.length;
      var path = cards[index].getAttribute("data-path");
      if (path && options && options.replace) {
        history.replaceState({}, "", path);
      }
    }

    place(false);
    reveal(cards[index]);
    if (progress) progress.textContent = (index + 1) + " / " + cards.length;

    document.addEventListener("loci:done", function (event) {
      var form = event.target;
      if (!form.classList || !form.classList.contains("delete-form")) return;
      var card = form.closest(".card");
      if (!card || !reel.contains(card)) {
        window.location.reload();
        return;
      }
      var removedAt = cards.indexOf(card);
      card.remove();
      cards = cards.filter(function (item) { return item !== card; });
      if (!cards.length) {
        window.location.href = "/";
        return;
      }
      if (removedAt >= 0 && removedAt < index) index -= 1;
      go(Math.min(index, cards.length - 1), { replace: true });
    });

    window.addEventListener("resize", function () { place(false); });

    if (prev) prev.addEventListener("click", function () { go(index - 1, { replace: true }); });
    if (next) next.addEventListener("click", function () { go(index + 1, { replace: true }); });

    function typing() {
      var el = document.activeElement;
      if (!el) return false;
      var tag = (el.tagName || "").toLowerCase();
      return tag === "textarea" || tag === "input" || el.isContentEditable;
    }

    function setLectio(on) {
      if (lectioTimer) window.clearInterval(lectioTimer);
      lectioTimer = 0;
      if (on) {
        lectioTimer = window.setInterval(function () {
          if (typing()) return;
          if (index >= cards.length - 1) {
            setLectio(false);
            say("Lectio paused at the end");
            return;
          }
          go(index + 1, { replace: true });
        }, 8000);
      }
      if (lectio) {
        lectio.setAttribute("aria-pressed", on ? "true" : "false");
        lectio.textContent = on ? "Pause" : "Lectio";
      }
    }

    if (lectio) {
      lectio.addEventListener("click", function () {
        setLectio(lectio.getAttribute("aria-pressed") !== "true");
      });
    }

    stage.addEventListener("touchstart", function (event) {
      if (event.target.closest("textarea, input, button, a, summary, label")) return;
      dragging = true;
      startY = event.touches[0].clientY;
      deltaY = 0;
      reel.classList.add("dragging");
    }, { passive: true });

    stage.addEventListener("touchmove", function (event) {
      if (!dragging) return;
      deltaY = event.touches[0].clientY - startY;
      var pull = deltaY;
      if ((index === 0 && pull > 0) || (index === cards.length - 1 && pull < 0)) pull *= 0.3;
      reel.style.transform = "translateY(" + ((-index * height()) + pull) + "px)";
    }, { passive: true });

    stage.addEventListener("touchend", function () {
      if (!dragging) return;
      dragging = false;
      reel.classList.remove("dragging");
      if (deltaY < -56) go(index + 1, { replace: true });
      else if (deltaY > 56) go(index - 1, { replace: true });
      else go(index, { replace: false });
      deltaY = 0;
    });

    stage.addEventListener("wheel", function (event) {
      if (event.target.closest("textarea")) return;
      event.preventDefault();
      var now = Date.now();
      if (now < wheelLock) return;
      if (Math.abs(event.deltaY) < 16) return;
      wheelLock = now + 620;
      go(index + (event.deltaY > 0 ? 1 : -1), { replace: true });
    }, { passive: false });

    document.addEventListener("keydown", function (event) {
      if (!stage || typing()) return;
      if (event.key === "ArrowDown" || event.key === "PageDown" || event.key === "j") {
        event.preventDefault();
        go(index + 1, { replace: true });
      } else if (event.key === "ArrowUp" || event.key === "PageUp" || event.key === "k") {
        event.preventDefault();
        go(index - 1, { replace: true });
      } else if (event.key === "Home") {
        event.preventDefault();
        go(0, { replace: true });
      } else if (event.key === "End") {
        event.preventDefault();
        go(cards.length - 1, { replace: true });
      } else if (event.key === "l" || event.key === "L") {
        if (lectio) lectio.click();
      }
    });

  }

  function wrapWords(paragraph) {
    if (paragraph.dataset.wrapped) return;
    var text = paragraph.textContent;
    paragraph.textContent = "";
    text.split(/(\s+)/).forEach(function (part, i) {
      if (!part) return;
      if (!part.trim()) {
        paragraph.appendChild(document.createTextNode(part));
        return;
      }
      var span = document.createElement("span");
      span.className = "word";
      span.style.transitionDelay = Math.min(i, 28) * 16 + "ms";
      span.textContent = part;
      paragraph.appendChild(span);
    });
    paragraph.dataset.wrapped = "1";
  }

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf"]');
    return meta ? meta.getAttribute("content") : "";
  }

  function say(message) {
    var toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    window.clearTimeout(say._timer);
    say._timer = window.setTimeout(function () { toast.classList.remove("show"); }, 1600);
  }

  function bindForm(form) {
    form.addEventListener("submit", function (event) {
      if (form.classList.contains("delete-form")) {
        if (!window.confirm("Delete this line from the scroll?")) {
          event.preventDefault();
          return;
        }
      }
      if (!window.fetch) return;
      event.preventDefault();
      form.dataset.ajax = "1";
      var data = new FormData(form);
      var token = data.get("csrf") || csrfToken();
      fetch(form.action, {
        method: "POST",
        body: data,
        headers: {
          "X-Requested-With": "fetch",
          "X-CSRF": token,
          "Accept": "application/json"
        }
      }).then(function (response) {
        if (!response.ok) throw new Error("bad");
        return response.json();
      }).then(function (payload) {
        applyPayload(form, payload);
        form.dispatchEvent(new CustomEvent("loci:done", { bubbles: true }));
      }).catch(function () {
        form.dataset.ajax = "";
        form.submit();
      });
    });
  }

  function applyPayload(form, payload) {
    var card = form.closest(".card") || document;
    if (typeof payload.amen === "boolean") {
      document.querySelectorAll(".card").forEach(function (item) {
        if (item.getAttribute("data-id") !== payload.id) return;
        var button = item.querySelector(".amen");
        if (!button) return;
        button.classList.toggle("on", payload.amen);
        button.setAttribute("aria-pressed", payload.amen ? "true" : "false");
      });
      say(payload.amen ? "Amen" : "Amen lifted");
    }
    if (typeof payload.saved === "boolean") {
      var save = form.querySelector(".save");
      if (save) {
        save.classList.toggle("on", payload.saved);
        save.setAttribute("aria-pressed", payload.saved ? "true" : "false");
        save.textContent = payload.saved ? "Saved" : "Save";
      }
      say(payload.saved ? "Saved" : "Unsaved");
    }
    if (typeof payload.following === "boolean") {
      document.querySelectorAll(".follow").forEach(function (button) {
        if (button.getAttribute("data-author") !== payload.author) return;
        button.classList.toggle("on", payload.following);
        button.setAttribute("aria-pressed", payload.following ? "true" : "false");
        button.textContent = payload.following ? "Following" : "Follow";
      });
      say(payload.following ? "Following" : "Unfollowed");
    }
    if (typeof payload.note === "string") {
      say(payload.note ? "Note kept" : "Note cleared");
    }
    if (payload.deleted) {
      say("Deleted");
      if (!document.getElementById("stage")) window.location.reload();
    }
    return card;
  }

  var lastBurst = 0;

  function bindDouble(card) {
    var last = 0;
    function fire(event) {
      if (event.target.closest("button, a, input, textarea, summary, label, form")) return;
      var now = Date.now();
      if (now - last > 320) {
        last = now;
        return;
      }
      last = 0;
      if (now - lastBurst < 400) return;
      lastBurst = now;
      burst(event.clientX, event.clientY);
      amenSet(card);
    }
    card.addEventListener("click", fire);
    card.addEventListener("dblclick", function (event) {
      if (event.target.closest("button, a, input, textarea, summary, label")) return;
      if (Date.now() - lastBurst < 400) return;
      lastBurst = Date.now();
      burst(event.clientX, event.clientY);
      amenSet(card);
    });
  }

  function amenSet(card) {
    var id = card.getAttribute("data-id");
    var token = csrfToken();
    var body = new FormData();
    body.set("csrf", token);
    body.set("mode", "set");
    fetch("/quote/" + encodeURIComponent(id) + "/amen", {
      method: "POST",
      body: body,
      headers: { "X-Requested-With": "fetch", "X-CSRF": token, "Accept": "application/json" }
    }).then(function (response) {
      if (!response.ok) throw new Error("bad");
      return response.json();
    }).then(function (payload) {
      document.querySelectorAll(".card").forEach(function (item) {
        if (item.getAttribute("data-id") !== id) return;
        var button = item.querySelector(".amen");
        if (!button) return;
        button.classList.add("on");
        button.setAttribute("aria-pressed", "true");
      });
      if (payload && payload.amen) say("Amen");
    }).catch(function () {
      say("Could not amen");
    });
  }

  function burst(x, y) {
    if (typeof x !== "number") {
      x = window.innerWidth / 2;
      y = window.innerHeight / 2;
    }
    var offsets = [[-30, -70], [10, -90], [40, -60], [-50, -40], [24, -36], [0, -110]];
    offsets.forEach(function (pair) {
      var heart = document.createElement("span");
      heart.className = "burst";
      heart.textContent = "♥";
      heart.style.left = x + "px";
      heart.style.top = y + "px";
      heart.style.setProperty("--dx", pair[0] + "px");
      heart.style.setProperty("--dy", pair[1] + "px");
      document.body.appendChild(heart);
      window.setTimeout(function () { heart.remove(); }, 720);
    });
  }

  function shareCard(node) {
    var card = node.classList && node.classList.contains("card") ? node : node.closest(".card");
    var url = (card && card.getAttribute("data-share")) || node.href || window.location.href;
    var text = card ? card.getAttribute("data-text") || "" : "";
    var author = card ? card.getAttribute("data-author") || "" : "";
    var title = author ? author + " · Loci" : "Loci";
    if (navigator.share) {
      navigator.share({ title: title, text: text, url: url }).then(function () {
        say("Shared");
      }).catch(function (error) {
        if (error && error.name === "AbortError") return;
        copyLink(url);
      });
      return;
    }
    copyLink(url);
  }

  function copyLink(url) {
    var done = function () { say("Link copied"); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done).catch(function () { legacyCopy(url); done(); });
      return;
    }
    legacyCopy(url);
    done();
  }

  function legacyCopy(url) {
    var area = document.createElement("textarea");
    area.value = url;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); } catch (error) { /* still show the toast */ }
    area.remove();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
