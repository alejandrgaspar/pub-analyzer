// This document was generated using Pub Analyzer.
// https://pub-analyzer.com

// Packages
#import "@preview/cetz:0.2.2": canvas, plot, chart, palette

// Colors
#let BLUE = rgb("#42a2f8")
#let GREEN = rgb("#82d452")
#let GRAY = rgb("#929292")
#let YELLOW = rgb("#f0bb40")
#let RED = rgb("#eb4025")
#let PURPLE = rgb("#c33375")

#let colors = (BLUE, GREEN, GRAY, YELLOW, RED, PURPLE)

// Page Layoput
#set page("us-letter")
#set page(flipped: true)

#set heading(numbering: "1.")

#set page(footer: grid(
    columns: (1fr, 1fr),
    align(left)[Made with #link("https://pub-analyzer.com")[_pub-analyzer_] version {{ version }}],
    align(right)[#counter(page).display("1")],
  )
)

// Text config
#set text(size: 10pt)
#set par(justify: true)

// Override reference
#show ref: it => {
  let el = it.element
  if el != none and el.func() == heading {
    // Override heading references.
    numbering(
      el.numbering,
      ..counter(heading).at(el.location())
    )
  } else {
    // Other references as usual.
    it
  }
}

// Title
#grid(
  columns: (1fr),
  row-gutter: 11pt,
  [#align(center, text(size: 17pt, weight: "bold")[{{ report.author.display_name }}])],
  {% if report.author.last_known_institutions %}
  {% set last_known_institution = report.author.last_known_institutions[0] %}
  [#align(center, text(size: 15pt, weight: "thin")[{{ last_known_institution.display_name }}])],
  {% endif %}
)

{% include 'author_summary.typ' %}

{% include 'works.typ' %}

{% include 'works_extended.typ' %}

{% include 'sources.typ' %}

#pagebreak()

= Bibliography

Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. ArXiv. https://arxiv.org/abs/2205.01833
