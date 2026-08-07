"""Markup generators for the block library.

Every generator owns exactly one ``<section>`` (or one shell landmark) and is
keyed by the block id declared in ``blocks/<id>/block.json``. Contracts describe
what a block needs; these functions decide how it is expressed as semantic HTML.
"""
from __future__ import annotations

import html
import json
from typing import Any, Callable, Mapping, Sequence

Renderer = Callable[[str, Mapping[str, Any]], str]


class BlockRenderError(ValueError):
    """Raised when a block cannot be rendered from the supplied data."""


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _rows(data: Mapping[str, Any], key: str) -> Sequence[Mapping[str, Any]]:
    value = data.get(key) or ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise BlockRenderError(f"Slot '{key}' must be a list")
    return value


def _anchor(section_id: str) -> str:
    return f' id="{_esc(section_id)}"' if section_id else ""


def _eyebrow(data: Mapping[str, Any]) -> str:
    value = data.get("eyebrow")
    return f'<span class="eyebrow">{_esc(value)}</span>' if value else ""


def _section_head(data: Mapping[str, Any], level: str = "h2") -> str:
    """The recurring `eyebrow + heading | note` band used by most blocks."""
    note = f"<p>{_esc(data['note'])}</p>" if data.get("note") else ""
    return (
        '<div class="container section-head">'
        f"<div>{_eyebrow(data)}<{level}>{_esc(data.get('title', ''))}</{level}></div>"
        f"{note}</div>"
    )


def _open(block_id: str, section_id: str, classes: str) -> str:
    return f'<section class="{classes}"{_anchor(section_id)} data-block="{_esc(block_id)}">'


# --------------------------------------------------------------------------- content


def render_hero_split_scene(section_id: str, data: Mapping[str, Any]) -> str:
    crumbs = ""
    trail = _rows(data, "breadcrumb")
    if trail:
        parts = []
        for index, crumb in enumerate(trail):
            last = index == len(trail) - 1
            label = _esc(crumb.get("label", ""))
            if last or not crumb.get("href"):
                parts.append(f"<strong>{label}</strong>")
            else:
                parts.append(f'<a href="{_esc(crumb["href"])}">{label}</a>')
            if not last:
                parts.append("<span>/</span>")
        crumbs = f'<nav class="sp-breadcrumb" aria-label="مسیر صفحه">{"".join(parts)}</nav>'

    lead = f'<p class="sp-lead">{_esc(data["lead"])}</p>' if data.get("lead") else ""

    actions = ""
    if _rows(data, "actions"):
        buttons = "".join(
            f'<a class="btn btn--{_esc(action.get("variant", "primary"))}" '
            f'href="{_esc(action.get("href", "#"))}">{_esc(action.get("label", ""))}</a>'
            for action in _rows(data, "actions")
        )
        actions = f'<div class="sp-actions">{buttons}</div>'

    proof = ""
    if _rows(data, "proof"):
        entries = "".join(f"<li>{_esc(item.get('label', ''))}</li>" for item in _rows(data, "proof"))
        proof = f'<ul class="sp-hero-proof">{entries}</ul>'

    labels = "".join(
        f'<span class="sp-orbit sp-orbit--{index}">{_esc(item.get("label", ""))}</span>'
        for index, item in enumerate(_rows(data, "scene_labels"), start=1)
    )
    scene = (
        '<div class="sp-hero-visual" aria-hidden="true">'
        '<div class="sp-grid-lines"></div>'
        '<div class="sp-structure sp-structure--wide"><i></i><b></b></div>'
        '<div class="sp-structure sp-structure--vertical"><i></i><b></b></div>'
        '<div class="sp-structure sp-structure--light"><i></i><b></b></div>'
        f"{labels}</div>"
    )

    hint = data.get("scroll_hint") or {}
    scroll = (
        f'<a class="sp-scroll" href="{_esc(hint.get("href", "#"))}">{_esc(hint.get("label", ""))}</a>'
        if hint
        else ""
    )

    return (
        f"{_open('hero-split-scene', section_id, 'sp-hero')}"
        '<div class="container sp-hero-grid"><div>'
        f"{crumbs}{_eyebrow(data)}<h1>{_esc(data.get('title', ''))}</h1>{lead}{actions}{proof}"
        f"</div>{scene}</div>{scroll}</section>"
    )


def render_answer_statement(section_id: str, data: Mapping[str, Any]) -> str:
    rule = ""
    if data.get("rule_text"):
        label = f"<b>{_esc(data['rule_label'])}</b> " if data.get("rule_label") else ""
        rule = f'<div class="sp-rule">{label}{_esc(data["rule_text"])}</div>'
    return (
        f"{_open('answer-statement', section_id, 'section section--white')}"
        '<div class="container sp-answer-grid">'
        f"<div>{_eyebrow(data)}<h2>{_esc(data.get('title', ''))}</h2></div>"
        f'<div class="sp-answer-copy"><p>{_esc(data.get("body", ""))}</p>{rule}</div>'
        "</div></section>"
    )


def render_index_strip(section_id: str, data: Mapping[str, Any]) -> str:
    cells = "".join(
        f'<a href="{_esc(entry.get("href", "#"))}">'
        f"<span>{index:02d}</span>{_esc(entry.get('label', ''))}</a>"
        for index, entry in enumerate(_rows(data, "entries"), start=1)
    )
    return (
        f"{_open('index-strip', section_id, 'sp-index-section')}"
        f'<nav class="container sp-index" aria-label="فهرست بخش‌های صفحه">{cells}</nav>'
        "</section>"
    )


def render_sticky_narrative(section_id: str, data: Mapping[str, Any]) -> str:
    lead = f"<p>{_esc(data['lead'])}</p>" if data.get("lead") else ""
    track = "".join(
        # The oversized numeral is a ghost graphic that repeats the DOM order,
        # so it is hidden from assistive technology rather than read twice.
        f'<article><span aria-hidden="true">{index:02d}</span>'
        f"<h3>{_esc(step.get('title', ''))}</h3>"
        f"<p>{_esc(step.get('body', ''))}</p></article>"
        for index, step in enumerate(_rows(data, "steps"), start=1)
    )
    return (
        f"{_open('sticky-narrative', section_id, 'section sp-story')}"
        '<div class="container sp-story-grid">'
        f'<div class="sp-story-copy">{_eyebrow(data)}'
        f"<h2>{_esc(data.get('title', ''))}</h2>{lead}</div>"
        f'<div class="sp-story-track">{track}</div>'
        "</div></section>"
    )


def render_decision_finder(section_id: str, data: Mapping[str, Any]) -> str:
    questions = _rows(data, "questions")
    fieldsets = []
    for question in questions:
        options = question.get("options") or []
        if not options:
            raise BlockRenderError("Each finder question needs at least one option")
        buttons = "".join(
            f'<button type="button" aria-pressed="{"true" if index == 0 else "false"}" '
            f'data-value="{_esc(option.get("value", ""))}">{_esc(option.get("label", ""))}</button>'
            for index, option in enumerate(options)
        )
        fieldsets.append(
            f"<fieldset><legend>{_esc(question.get('legend', ''))}</legend>"
            f'<div class="sp-choice" role="group" data-group="{_esc(question.get("group", ""))}">'
            f"{buttons}</div></fieldset>"
        )

    outcomes = data.get("outcomes")
    if not isinstance(outcomes, Mapping) or not outcomes:
        raise BlockRenderError("decision-finder requires a non-empty outcomes map")
    fallback = "|".join(
        str((question.get("options") or [{}])[0].get("value", "")) for question in questions
    )
    if fallback not in outcomes:
        raise BlockRenderError(
            f"decision-finder outcomes must cover the default combination '{fallback}'"
        )
    initial = outcomes[fallback]
    points = "".join(f"<li>{_esc(point)}</li>" for point in initial.get("points", []))
    payload = json.dumps(outcomes, ensure_ascii=False, separators=(",", ":"))

    return (
        f'<section class="section section--white"{_anchor(section_id)} '
        f'data-block="decision-finder" data-finder-fallback="{_esc(fallback)}">'
        f"{_section_head(data)}"
        '<div class="container sp-finder">'
        f'<div class="sp-finder-controls">{"".join(fieldsets)}</div>'
        '<aside class="sp-result" aria-live="polite">'
        f"<small>{_esc(data.get('result_label', ''))}</small>"
        f'<h3 data-finder-title>{_esc(initial.get("title", ""))}</h3>'
        f'<p data-finder-body>{_esc(initial.get("body", ""))}</p>'
        f"<ul data-finder-points>{points}</ul></aside></div>"
        f'<script type="application/json" data-finder-outcomes>{payload}</script>'
        "</section>"
    )


def render_family_stack(section_id: str, data: Mapping[str, Any]) -> str:
    cards = []
    for index, family in enumerate(_rows(data, "families"), start=1):
        tags = "".join(f"<span>{_esc(tag)}</span>" for tag in family.get("tags", []))
        kicker = f"<small>{_esc(family['kicker'])}</small>" if family.get("kicker") else ""
        cards.append(
            f'<article class="sp-family"><div class="sp-family-number" aria-hidden="true">{index:02d}</div>'
            f'<div class="sp-family-copy">{kicker}<h3>{_esc(family.get("title", ""))}</h3>'
            f'<p>{_esc(family.get("body", ""))}</p><div class="sp-tags">{tags}</div></div>'
            '<div class="sp-family-art" aria-hidden="true"><i></i><b></b></div></article>'
        )
    return (
        f"{_open('family-stack', section_id, 'section section--dark sp-catalog')}"
        f"{_section_head(data)}"
        f'<div class="container sp-family-stack">{"".join(cards)}</div>'
        "</section>"
    )


def render_comparison_table(section_id: str, data: Mapping[str, Any]) -> str:
    columns = _rows(data, "columns")
    head = "".join(f'<th scope="col">{_esc(column.get("label", ""))}</th>' for column in columns)
    body = []
    for row in _rows(data, "rows"):
        cells = row.get("cells") or []
        if len(cells) != len(columns) - 1:
            raise BlockRenderError(
                f"Comparison row '{row.get('header', '')}' has {len(cells)} cells "
                f"but the table declares {len(columns) - 1} data columns"
            )
        body.append(
            f'<tr><th scope="row">{_esc(row.get("header", ""))}</th>'
            + "".join(f"<td>{_esc(cell)}</td>" for cell in cells)
            + "</tr>"
        )
    return (
        f"{_open('comparison-table', section_id, 'section section--white')}"
        f"{_section_head(data)}"
        '<div class="container sp-table-wrap" tabindex="0" role="region" aria-label="جدول مقایسه">'
        f'<table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
        "</section>"
    )


def render_process_line(section_id: str, data: Mapping[str, Any]) -> str:
    steps = "".join(
        f'<article><b aria-hidden="true">{index:02d}</b><h3>{_esc(step.get("title", ""))}</h3>'
        f"<p>{_esc(step.get('body', ''))}</p></article>"
        for index, step in enumerate(_rows(data, "steps"), start=1)
    )
    return (
        f"{_open('process-line', section_id, 'section sp-process')}"
        f"{_section_head(data)}"
        f'<div class="container sp-process-line">{steps}</div>'
        "</section>"
    )


def render_faq_grid(section_id: str, data: Mapping[str, Any]) -> str:
    entries = "".join(
        f'<details{" open" if index == 0 else ""}><summary>{_esc(item.get("q", ""))}</summary>'
        f"<p>{_esc(item.get('a', ''))}</p></details>"
        for index, item in enumerate(_rows(data, "questions"))
    )
    return (
        f"{_open('faq-grid', section_id, 'section section--white')}"
        f"{_section_head(data)}"
        f'<div class="container sp-faq">{entries}</div>'
        "</section>"
    )


def render_closing_band(section_id: str, data: Mapping[str, Any]) -> str:
    action = data.get("action") or {}
    if not action.get("label") or not action.get("href"):
        raise BlockRenderError("closing-band requires an action with a label and href")
    body = f"<p>{_esc(data['body'])}</p>" if data.get("body") else ""
    return (
        f"{_open('closing-band', section_id, 'sp-contact')}"
        '<div class="container sp-contact-grid">'
        f"<div>{_eyebrow(data)}<h2>{_esc(data.get('title', ''))}</h2>{body}</div>"
        f'<div><a class="btn btn--light" href="{_esc(action["href"])}">'
        f"{_esc(action['label'])}</a></div>"
        "</div></section>"
    )


# ----------------------------------------------------------------------------- shell


def render_site_header(section_id: str, data: Mapping[str, Any]) -> str:
    links = []
    for item in _rows(data, "nav"):
        label = _esc(item.get("label", ""))
        href = _esc(item.get("href", "#"))
        children = item.get("children") or []
        if not children:
            links.append(f'<a class="nav-link" href="{href}">{label}</a>')
            continue
        cards = "".join(
            f'<a class="mega-link" href="{_esc(child.get("href", "#"))}">'
            f'<strong>{_esc(child.get("label", ""))}</strong>'
            f'<small>{_esc(child.get("note", ""))}</small></a>'
            for child in children
        )
        links.append(
            f'<div class="nav-item"><a class="nav-link" href="{href}">{label}</a>'
            f'<div class="mega"><div class="mega-grid">{cards}</div></div></div>'
        )

    mobile = "".join(
        f'<a href="{_esc(item.get("href", "#"))}">{_esc(item.get("label", ""))}</a>'
        for item in _rows(data, "mobile_nav")
    )
    brand = data.get("brand") or {}
    cta = data.get("cta") or {}
    return (
        '<header class="site-header" data-block="site-header">'
        '<div class="container header-inner">'
        # logo_svg is inlined verbatim: brand marks come from the project's own
        # configuration, not from page content, so they are trusted markup.
        f'<a class="brand" href="/">{brand.get("logo_svg", "")}'
        f'<span class="brand-copy"><strong>{_esc(brand.get("name", ""))}</strong>'
        f'<small>{_esc(brand.get("tagline", ""))}</small></span></a>'
        f'<nav class="main-nav" aria-label="ناوبری اصلی">{"".join(links)}</nav>'
        '<div class="header-actions">'
        f'<a class="btn btn--primary" href="{_esc(cta.get("href", "#"))}">'
        f"{_esc(cta.get('label', ''))}</a>"
        '<button class="menu-button" type="button" aria-label="باز کردن منو" '
        'aria-expanded="false" aria-controls="mobile-panel"><span aria-hidden="true">☰</span>'
        "</button></div></div></header>"
        f'<div class="mobile-panel" id="mobile-panel">'
        f'<nav class="mobile-nav" aria-label="ناوبری موبایل">{mobile}</nav></div>'
    )


def render_mobile_jump_nav(section_id: str, data: Mapping[str, Any]) -> str:
    active = ' class="is-active"'
    entries = "".join(
        f'<a href="{_esc(entry.get("href", "#"))}"'
        f'{active if index == 0 else ""}>{_esc(entry.get("label", ""))}</a>'
        for index, entry in enumerate(_rows(data, "entries"))
    )
    return (
        '<nav class="sp-mobile-nav" aria-label="ناوبری سریع صفحه" '
        f'data-block="mobile-jump-nav">{entries}</nav>'
    )


def render_site_footer(section_id: str, data: Mapping[str, Any]) -> str:
    brand = data.get("brand") or {}
    columns = "".join(
        f'<div class="footer-links-col"><b>{_esc(column.get("title", ""))}</b>'
        + "".join(
            f'<a href="{_esc(link.get("href", "#"))}">{_esc(link.get("label", ""))}</a>'
            for link in column.get("links", [])
        )
        + "</div>"
        for column in _rows(data, "columns")
    )
    legal = "".join(
        f'<a href="{_esc(link.get("href", "#"))}">{_esc(link.get("label", ""))}</a>'
        for link in _rows(data, "legal")
    )
    return (
        '<footer class="footer-paya" data-block="site-footer"><div class="container">'
        '<div class="footer-paya-main"><div class="footer-identity">'
        f'{brand.get("logo_svg", "")}'
        f'<div><h3>{_esc(brand.get("legal_name", ""))}</h3>'
        f'<p>{_esc(data.get("summary", ""))}</p></div></div>'
        f"{columns}</div>"
        f'<div class="footer-paya-bottom"><span>{_esc(data.get("copyright", ""))}</span>'
        f"<div>{legal}</div></div></div></footer>"
    )


RENDERERS: Mapping[str, Renderer] = {
    "hero-split-scene": render_hero_split_scene,
    "answer-statement": render_answer_statement,
    "index-strip": render_index_strip,
    "sticky-narrative": render_sticky_narrative,
    "decision-finder": render_decision_finder,
    "family-stack": render_family_stack,
    "comparison-table": render_comparison_table,
    "process-line": render_process_line,
    "faq-grid": render_faq_grid,
    "closing-band": render_closing_band,
    "site-header": render_site_header,
    "site-footer": render_site_footer,
    "mobile-jump-nav": render_mobile_jump_nav,
}


def render_block(block_id: str, section_id: str, data: Mapping[str, Any]) -> str:
    try:
        renderer = RENDERERS[block_id]
    except KeyError as exc:
        raise BlockRenderError(f"No markup generator registered for block '{block_id}'") from exc
    return renderer(section_id, data)
