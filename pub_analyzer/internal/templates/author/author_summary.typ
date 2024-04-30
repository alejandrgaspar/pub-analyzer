// Author Summary
= Author.

// Cards
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 15pt,
  [
    // Card
    #rect(
      width: 100%,
      height: 150pt,
      fill: rgb("e5e7eb"),
      stroke: 1pt,
      radius: 2pt,
      [#linebreak()
        #grid(
        columns: 1fr,
        row-gutter: (15pt, 12pt),

        // Card Title
        [#align(center)[#text(size: 12pt)[Last institution:]]],

        // Card content
        {% if report.author.last_known_institutions%}
        {% set last_known_institution = report.author.last_known_institutions[0] %}
        [#align(left)[#text(size: 10pt)[- *Name:* {{ last_known_institution.display_name }}]]],
        [#align(left)[#text(size: 10pt)[- *Country:* MX]]],
        [#align(left)[#text(size: 10pt)[- *Type:* education]]],
        {% endif %}
      )]
    )
  ],
  [
    // Card
    #rect(
      width: 100%,
      height: 150pt,
      fill: rgb("e5e7eb"),
      stroke: 1pt,
      radius: 2pt,
      [#linebreak()
        #grid(
        columns: 1fr,
        row-gutter: (15pt, 12pt),

        // Card Title
        [#align(center)[#text(size: 12pt)[Identifiers:]]],

        // Card content
        {% for key, value in report.author.ids.model_dump().items() %}
            {% if value %}
            [#align(left)[#text(size: 10pt)[- #underline( [#link("{{ value }}")[{{ key }}]] )]]],
            {% endif %}
        {% endfor %}
      )]
    )
  ],
  [
    // Card
    #rect(
      width: 100%,
      height: 150pt,
      fill: rgb("e5e7eb"),
      stroke: 1pt,
      radius: 2pt,
      [#linebreak()
        #grid(
        columns: 1fr,
        row-gutter: (15pt, 12pt),

        // Card Title
        [#align(center)[#text(size: 12pt)[Citation metrics:]]],

        // Card content
        [#align(left)[#text(size: 10pt)[- *2-year mean:* {{ report.author.summary_stats.two_yr_mean_citedness|round(5) }}]]],
        [#align(left)[#text(size: 10pt)[- *h-index:* {{ report.author.summary_stats.h_index }}]]],
        [#align(left)[#text(size: 10pt)[- *i10 index:* {{ report.author.summary_stats.i10_index }}]]],
      )]
    )
  ],
)

#align(center, text(11pt)[_Counts by year_])
#table(
  columns: (1fr, 2fr, 2fr),
  inset: 8pt,
  align: horizon,
  // Headers
  [*Year*], [*Works count*], [*Cited by count*],

  // Content
  {% for year_count in report.author.counts_by_year[:8] %}
  [{{ year_count.year }}], [{{ year_count.works_count }}], [{{ year_count.cited_by_count }}],
  {% endfor %}
)
#pagebreak()
