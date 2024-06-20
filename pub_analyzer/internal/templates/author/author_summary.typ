// Author Summary
= Author.

#let summary-card(title: "Title", body) = {
  return block(
    width: 100%,
    height: 150pt,
    fill: rgb("e5e7eb"),
    stroke: 1pt,
    radius: 2pt,
  )[
    #v(20pt)
    #align(center)[#text(size: 12pt)[#title]]
    #v(5pt)
    #block(width: 100%, inset: (x: 20pt))[#body]
  ]
}

// Cards
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 15pt,
  [
    // Last institution.
    #summary-card(title:"Last institution:")[
      {% if report.author.last_known_institutions%}
      {% set last_known_institution = report.author.last_known_institutions[0] %}
      #grid(
        rows: auto, row-gutter: 10pt,

        [*Name:* {{ last_known_institution.display_name }}],
        [*Country:* {{ last_known_institution.country_code }}],
        [*Type:* {{ last_known_institution.type.value|capitalize }}],
      )
      {% endif %}
    ]
  ],
  [
    // Author identifiers.
    #summary-card(title:"Identifiers:")[
      #grid(
        rows: auto, row-gutter: 10pt,
        {% for key, value in report.author.ids.model_dump().items() %}
          {% if value %}
          [- #underline( [#link("{{ value }}")[{{ key }}]] )],
          {% endif %}
        {% endfor %}
      )
    ]
  ],
  [
    // Citation metrics.
    #summary-card(title: "Citation metrics:")[
      #grid(
        rows: auto, row-gutter: 10pt,

        [*2-year mean:* {{ report.author.summary_stats.two_yr_mean_citedness|round(5) }}],
        [*h-index:* {{ report.author.summary_stats.h_index }}],
        [*i10 index:* {{ report.author.summary_stats.i10_index }}]
      )
    ]
  ],
)

#v(10pt)
#align(center, text(11pt)[_Counts by year_])
#grid(
  columns: (1fr, 1fr),
  column-gutter: 15pt,
  align: (auto, horizon),

  [
    #table(
      columns: (1fr, 2fr, 2fr),
      inset: 8pt,
      align: horizon,
      // Headers
      [*Year*], [*Works count*], [*Cited by count*],

      // Content
      {% set max_year_count = 0 %}
      {% for year_count in report.author.counts_by_year[:8] %}
      [{{ year_count.year }}], [{{ year_count.works_count }}], [{{ year_count.cited_by_count }}],
      {% set max_year_count = year_count %}
      {% endfor %}
    )
  ],
  grid.cell(
    inset: (x: 10pt, bottom: 10pt, top: 2.5pt),
    stroke: 1pt
  )[
    #align(center, text(10pt)[Cites by year])
    #v(5pt)
    #canvas(length: 100%, {
      plot.plot(
        size: (0.90, 0.48),
        axis-style: "scientific-auto",
        plot-style: (stroke: (1pt + BLUE),),
        x-min: auto, x-max: auto,
        x-tick-step: 1, y-tick-step: auto,
        x-label: none, y-label: none,
        {
          plot.add((
            {% for year_count in report.author.counts_by_year[:8] %}
            ({{ year_count.year }}, {{ year_count.cited_by_count }}),
            {% endfor %}
          ))
      })
    })
  ]
)
#pagebreak()
