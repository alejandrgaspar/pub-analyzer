// Works
= Works.

#let works_metrics_card(title: "Title", graph, body) = {
  grid(
    rows: (18pt, 175pt, 60pt),
    columns: 100%,

    [
      #block(width: 100%, height: 100%)[
        #align(center + horizon)[#text(style: "italic")[#title]]
      ]
    ],
    [
      #block(width: 100%, height: 100%)[
        #align(center + horizon)[#graph]
      ]
    ],
    [
      #block(width: 100%, height: 100%, inset: (x: 0pt, y: 10pt))[#body]
    ],
  )
}

#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 15pt,
  [
    #let graph = {
      canvas(length: 35%, {
        chart.piechart(
          (
            {{ report.citation_summary.type_a_count }}, // Type A
            {{ report.citation_summary.type_b_count }}  // Type B
          ),
          radius: 1,
          slice-style: (PALETTE.at(0), PALETTE.at(1)),
          outer-label: (content: "%", radius: 115%),
        )
      })
    }

    #works_metrics_card(title: "Citation metrics", graph)[
      #grid(
        rows: auto, row-gutter: 10pt,
        columns: (1fr, 1fr),

        grid.cell(colspan: 2)[
          *Count:* {{ report.citation_summary.type_a_count + report.citation_summary.type_b_count }}
        ],
        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(0)) *Type A:* {{ report.citation_summary.type_a_count }}],
        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(1)) *Type B:* {{ report.citation_summary.type_b_count }}],
      )
    ]
  ],
  [
    #let graph = {
      canvas(length: 35%, {
        chart.columnchart(
          size: (2.45, 2.0),
          y-grid: false,
          bar-style: palette.new(
            base: (stroke: none, fill: none),
            colors: PALETTE
          ),
          (
            {% for work_type in report.works_type_summary[:4] %}
            ("{{ work_type.type_name[:2]|capitalize }}", {{ work_type.count }}),
            {% endfor %}
          )
        )
      })
    }
    #works_metrics_card(title: "Work Type", graph)[
      #grid(
        rows: auto, row-gutter: 10pt,
        columns: (1fr, 1fr),
        column-gutter: 5pt,

        grid.cell(colspan: 2)[
          *Count:* {{ report.open_access_summary.model_dump().items()|sum(attribute="1") }}
        ],

        {% for work_type in report.works_type_summary[:4] %}
        [
          #box(height: 7pt, width: 7pt, fill: PALETTE.at({{ loop.index0 }})) *{{ work_type.type_name|capitalize }}:* {{ work_type.count }}
        ],
        {% endfor %}
      )
    ]
  ],
  [
    #let graph = {
      canvas(length: 35%, {
        chart.piechart(
          (
            {{report.open_access_summary.diamond}},   // diamond
            {{report.open_access_summary.gold}},      // Gold
            {{report.open_access_summary.green}},     // Green
            {{report.open_access_summary.hybrid}},    // Hybrid
            {{report.open_access_summary.bronze}},    // Bronze
            {{report.open_access_summary.closed}},    // Closed
          ),
          radius: 1,
          inner-radius: .4,
          slice-style: (PALETTE.at(0), PALETTE.at(3), PALETTE.at(1), PALETTE.at(4), PALETTE.at(5), PALETTE.at(2)),
          outer-label: (content: "%", radius: 115%),
        )
      })
    }
    #works_metrics_card(title: "Open Access", graph)[
      #grid(
        rows: auto, row-gutter: 10pt,
        columns: (1fr, 1fr, 1fr),
        column-gutter: 5pt,

        grid.cell(colspan: 3)[
          *Count:* {{ report.open_access_summary.model_dump().items()|sum(attribute="1") }}
        ],

        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(0)) *Diamond:* {{report.open_access_summary.diamond}}],
        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(3)) *Gold:* {{report.open_access_summary.gold}}],
        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(1)) *Green:* {{report.open_access_summary.green}}],
        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(5)) *Bronze:* {{report.open_access_summary.bronze}}],
        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(2)) *Closed:* {{report.open_access_summary.closed}}],
        [#box(height: 7pt, width: 7pt, fill: PALETTE.at(4)) *Hybrid:* {{report.open_access_summary.hybrid}}],
      )
    ]
  ],
)

#align(center, text(11pt)[Works from {{ report.works[0].work.publication_year }} to {{ report.works[-1].work.publication_year }}])
#table(
  columns: (auto, 3fr, auto, auto, auto, auto, auto, auto, auto),
  inset: 8pt,
  align: horizon,
  // Headers
  [], [*Title*], [*Type*], [*DOI*], [*Publication Date*], [*Cited by count*], [*Type A*], [*Type B*], [*OA*],

  // Content
  {% for work in report.works %}
  [#underline([#link(label("work_{{ loop.index }}"))[@work_{{ loop.index }}]])],
  [#"{{ work.work.title.replace('"', '\\"') }}"],
  [{{ work.work.type }}],
  [{% if work.work.ids.doi %}#underline([#link("{{ work.work.ids.doi }}")[DOI]]){% else %}-{% endif %}],
  [{{ work.work.publication_date }}],
  [{{ work.citation_summary.type_a_count + work.citation_summary.type_b_count }}],
  [{{ work.citation_summary.type_a_count }}],
  [{{ work.citation_summary.type_b_count }}],
  [{{ work.work.open_access.oa_status.value }}],

  {% endfor %}
)
#pagebreak()
