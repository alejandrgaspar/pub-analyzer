// This document was generated using Pub Analyzer.
// https://pub-analyzer.com


// Page Layoput
#set page("us-letter")
#set page(flipped: true)

#set heading(numbering: "1.")

#set page(footer: grid(
    columns: (1fr, 1fr),
    align(left)[Made with #link("https://gaspar.land")[_pub-analyzer_] version {{ version }}],
    align(right)[#counter(page).display("1")],
  )
)

// Text config
#set text(size: 10pt)

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
  {% if report.author.last_known_institution %}
  [#align(center, text(size: 15pt, weight: "thin")[{{ report.author.last_known_institution.display_name }}])],
  {% endif %}
)

{% include 'author_resume.typ' %}

{% include 'works.typ' %}

{% include 'works_extended.typ' %}

{% include 'sources.typ' %}

#pagebreak()

= Bibliography

Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. ArXiv. https://arxiv.org/abs/2205.01833
