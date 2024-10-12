// This document was generated using Pub Analyzer version {{ version }}.
//
// Pub Analyzer is a tool designed to retrieve, process and present in a concise and understandable
// way the scientific production of a researcher, including detailed information about their articles,
// citations, collaborations and other relevant metrics.
//
// See more here: https://pub-analyzer.com

// Packages
//
// This document uses the Cetz package to render plots and graphs. For more information
// on how to edit the plots see: https://typst.app/universe/package/cetz/

#import "@preview/cetz:0.2.2": canvas, plot, chart, palette

// Colors
//
// The following variables control all colors used in the document.
// You can modify the color codes by specifying the four RGB(A) components or by
// using the hexadecimal code.
//
// See more here: https://typst.app/docs/reference/visualize/color/#definitions-rgb

#let SUCCESS = rgb("#909d63")
#let ERROR   = rgb("#bc5653")

#let CATEGORY_1 = rgb("#42a2f8")
#let CATEGORY_2 = rgb("#82d452")
#let CATEGORY_3 = rgb("#929292")
#let CATEGORY_4 = rgb("#f0bb40")
#let CATEGORY_5 = rgb("#eb4025")
#let CATEGORY_6 = rgb("#c33375")

#let PALETTE = (CATEGORY_1, CATEGORY_2, CATEGORY_3, CATEGORY_4, CATEGORY_5, CATEGORY_6)

// Page Layout
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
