// This document was generated using Pub Analyzer.
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

#import "@preview/cetz:0.3.4"
#import "@preview/cetz-plot:0.1.1": plot, chart

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

// Get data
#let report = json(bytes(sys.inputs.report))
#let version = str(bytes(sys.inputs.version))
#let author = report.at("author")
#let works = report.at("works")
#let citation_summary = report.at("citation_summary")
#let open_access_summary = report.at("open_access_summary")
#let works_type_summary = report.at("works_type_summary")
#let sources_summary = report.at("sources_summary")

// Set document metadata.
#let description = "This document was generated using Pub Analyzer version " + version + "."
#set document(
  title: "Pub Analyzer",
  description: description,
)

// Page Layout
#set page("us-letter")
#set page(flipped: true)

#set page(footer: grid(
    columns: (1fr, 1fr),
    align(left)[Made with #link("https://pub-analyzer.com")[_pub-analyzer_] version #version],
    align(right)[#context counter(page).display("1")],
  )
)

// Text config
#set heading(numbering: "1.")
#set text(size: 10.5pt)
#set par(linebreaks: "simple", justify: true)
#set text(lang: "en", overhang: true, font: "New Computer Modern")

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

// Shortcuts
#let capitalize(input) = {
  return upper(input.first()) + input.slice(1)
}


// Header
#grid(
  columns: (1fr),
  row-gutter: 11pt,
  align: center,

  [
    #text(size: 17pt, weight: "bold")[#author.at("display_name")]
  ],
  if author.at("last_known_institutions") != none and author.at("last_known_institutions").len() >= 1 [
    #let last_known_institution = author.at("last_known_institutions").first()
    #text(size: 15pt, weight: "thin")[#last_known_institution.at("display_name")]
  ]
)

// Author Summary
= Author.

#let summary-card(title: "Title", body) = {
  return block(
    width: 100%, height: 150pt,
    stroke: 1pt, radius: 2pt,
    inset: (top: 20pt),
    fill: rgb("e5e7eb"),
  )[
    #align(center)[#text(size: 12pt)[#title]]
    #v(5pt)
    #block(width: 100%, inset: (x: 20pt))[#body]
  ]
}

// Cards
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 15pt,

  // Last institution.
  [
    #summary-card(title:"Last institution:")[
      #if author.at("last_known_institutions") != none and author.at("last_known_institutions").len() >= 1 [
        #let last_known_institution = author.at("last_known_institutions").first()
        #let institution_type_name = capitalize(last_known_institution.at("type"))

        #grid(
          rows: auto, row-gutter: 10pt,

          [*Name:* #last_known_institution.at("display_name")],
          [*Country:* #last_known_institution.at("country_code")],
          [*Type:* #institution_type_name],
        )
      ] else [
        #text(size: 9pt, fill: luma(50%))[No associated institutions were found.]
      ]
    ]
  ],

  // Author identifiers.
  [
    #summary-card(title:"Identifiers:")[
      #grid(
        rows: auto, row-gutter: 10pt,
        ..(
          author.at("ids").pairs().filter(id => id.last() != none).map(
            ((k, v)) => grid.cell[
              - #underline( [#link(v)[#k]] )
            ]
          ).flatten()
        )
      )
    ]
  ],

  // Citation metrics.
  [
    #summary-card(title: "Citation metrics:")[
      #let summary_stats = author.at("summary_stats")

      #grid(
        rows: auto, row-gutter: 10pt,

        [*2-year mean:* #calc.round(summary_stats.at("2yr_mean_citedness"), digits: 5)],
        [*h-index:* #summary_stats.at("h_index")],
        [*i10 index:* #summary_stats.at("i10_index")],
      )
    ]
  ]
)

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
      ..author.at("counts_by_year").rev().slice(0, calc.min(author.at("counts_by_year").len(), 8)).map(
        ((year, works_count, cited_by_count)) => (
          table.cell([#year]),
          table.cell([#works_count]),
          table.cell([#cited_by_count]),
        )
      ).flatten()
    )
  ],
  grid.cell(
    inset: (x: 10pt, bottom: 10pt, top: 2.5pt),
    stroke: 1pt
  )[
    #align(center, text(10pt)[Cites by year])
    #v(5pt)
    #cetz.canvas(length: 100%, {
      plot.plot(
        size: (0.90, 0.48),
        axis-style: "scientific-auto",
        plot-style: (stroke: (1pt + PALETTE.at(0)),),
        x-min: auto, x-max: auto,
        x-tick-step: 1, y-tick-step: auto,
        x-label: none, y-label: none,
        {
          plot.add((
            ..author.at("counts_by_year").rev().slice(0, calc.min(author.at("counts_by_year").len(), 8)).map(
              ((year, works_count, cited_by_count)) => (
                (year, cited_by_count)
              )
            )
          ))
      })
    })
  ]
)

// Works
#pagebreak()
= Works.

#let works_metrics_card(title: "Title", graph, body) = {
  grid(
    rows: (18pt, 175pt, 60pt),
    columns: (100%),

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
      #set text(size: 9.5pt)
      #block(width: 100%, height: 100%, inset: (x: 0pt, y: 10pt))[#body]
    ],
  )
}

#let leyend_box(color: rgb) = {
  box(height: 7pt, width: 7pt, fill: color)
}

#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 15pt,

  [
    #let graph = {
      let type_a = citation_summary.at("type_a_count")
      let type_b = citation_summary.at("type_b_count")
      let total = type_a + type_b

      if total == 0 {
        cetz.canvas(length: 35%, {
          cetz.draw.circle(
            (0,0),
            radius: 1,
            stroke: luma(90%),
            fill: luma(98%),
          )
          cetz.draw.content(
            (0, 0), text("No citations found", size: 9pt, fill: luma(50%))
          )
        })
      } else {
        cetz.canvas(length: 35%, {
          chart.piechart(
            (type_a, type_b),
            radius: 1,
            slice-style: (PALETTE.at(0), PALETTE.at(1)),
            outer-label: (content: "%", radius: 115%),
          )
        })
      }
    }

    #works_metrics_card(title: "Citation metrics", graph)[
      #grid(
        rows: auto, row-gutter: 10pt,
        columns: (1fr, 1fr),

        grid.cell(colspan: 2)[
          *Count:* #citation_summary.values().sum()
        ],
        [
          #leyend_box(color: PALETTE.at(0)) *Type A:* #citation_summary.at("type_a_count")
        ],
        [
          #leyend_box(color: PALETTE.at(1)) *Type B:* #citation_summary.at("type_b_count")
        ],
      )
    ]
  ],
  [
    #let graph = {
      cetz.canvas(length: 35%, {
        chart.columnchart(
          size: (2.45, 2.0),
          y-grid: false,
          bar-style: cetz.palette.new(
            base: (stroke: none, fill: none),
            colors: PALETTE
          ),
          (
            works_type_summary.slice(0, calc.min(4, works_type_summary.len())).map(
              ((type_name, count)) => (
                (capitalize(type_name.slice(0,2)), count)
              )
            )
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
          *Count:* #open_access_summary.values().sum()
        ],
        ..works_type_summary.slice(0, calc.min(4, works_type_summary.len())).enumerate().map(
          ((idx, work_type)) => (
            grid.cell([#leyend_box(color: PALETTE.at(idx)) *#capitalize(work_type.type_name):* #work_type.count])
          )
        )
      )
    ]
  ],
  [
    #let graph = {
      cetz.canvas(length: 35%, {
        chart.piechart(
          (
            open_access_summary.diamond,   // diamond
            open_access_summary.gold,      // Gold
            open_access_summary.green,     // Green
            open_access_summary.hybrid,    // Hybrid
            open_access_summary.bronze,    // Bronze
            open_access_summary.closed,    // Closed
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
        columns: (1.17fr, 1fr, 1fr),
        column-gutter: 5pt,

        grid.cell(colspan: 3)[
          *Count:* #open_access_summary.values().sum()
        ],

        [#leyend_box(color: PALETTE.at(0)) *Diamond:* #open_access_summary.diamond],
        [#leyend_box(color: PALETTE.at(3)) *Gold:* #open_access_summary.gold],
        [#leyend_box(color: PALETTE.at(1)) *Green:* #open_access_summary.green],
        [#leyend_box(color: PALETTE.at(5)) *Bronze:* #open_access_summary.bronze],
        [#leyend_box(color: PALETTE.at(2)) *Closed:* #open_access_summary.closed],
        [#leyend_box(color: PALETTE.at(4)) *Hybrid:* #open_access_summary.hybrid],
      )
    ]
  ]
)

#let first-pub-year(works, default: "-") = {
  for w in works {
    if w.work.publication_year != none {
      return w.work.publication_year
    }
  }
  default
}

#let last-pub-year(works, default: "-") = {
  for w in works.rev() {
    if w.work.publication_year != none {
      return w.work.publication_year
    }
  }
  default
}

#align(
  center,
  text(11pt)[
    Works from #first-pub-year(works) to #last-pub-year(works)
  ]
)

#{
  set text(size: 10pt)
  table(
    columns: (auto, 2fr, auto, auto, auto, auto, auto, auto, auto),
    inset: 8pt,
    align: horizon,
    // Headers
    [], [*Title*], [*Type*], [*DOI*], [*Publication Date*], [*Cited by count*], [*Type A*], [*Type B*], [*OA*],

    // Content
    ..works.enumerate().map(
      ((idx, work)) => (
        table.cell([#underline[#link(label("work_" + str(idx)))[#ref(label("work_" + str(idx)))]]]),
        table.cell([#work.work.title]),
        table.cell([#work.work.type]),
        table.cell([#if work.work.ids.doi != none [#underline[#link(work.work.ids.doi)[DOI]]] else [#align(center)[-]]]),
        table.cell([#work.work.publication_date]),
        table.cell([#work.citation_summary.values().sum()]),
        table.cell([#work.citation_summary.type_a_count]),
        table.cell([#work.citation_summary.type_b_count]),
        table.cell([#work.work.open_access.oa_status]),
      )
    ).flatten()
  )
}

// Works Extended
#let work_driven_version = (
  submittedVersion: "submitted",
  acceptedVersion: "accepted",
  publishedVersion: "published"
)
#for (idx, work_report) in works.enumerate() [
  #let work = work_report.work

  #pagebreak()
  #heading(level: 2)[#work.title] #label("work_" + str(idx))


  #if work.abstract != none [
    #v(5pt)
    #work.abstract
  ]

  // Cards
  #v(5pt)
  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 30pt,

    [
      #align(center)[_Authorships_]
      #block()[
        #for authorship in work.authorships.slice(0, calc.min(10, work.authorships.len())) [
          #let author_link = if authorship.author.at("orcid") != none {
            authorship.author.orcid
          } else {
            authorship.author.id
          }
          - *#authorship.author_position:* #underline[#link(author_link)[#if authorship.author.display_name == author.display_name [#text(rgb(SUCCESS))[#authorship.author.display_name]] else [#authorship.author.display_name]]]
        ]
        #if work.authorships.len() > 10 [- *...*]
      ]
    ],
    [
      #align(center)[_Open Access_]

      - *Status:* #capitalize(work.open_access.oa_status)
      #if work.open_access.oa_url != none [- *URL:* #underline[#link(work.open_access.oa_url)[#work.open_access.oa_url.find(regex("^(https?:\/\/[^\/]+\/)"))]]]
    ],
    [
      #align(center)[_Citation_]

      - *Count:* #work_report.citation_summary.values().sum()
      - *Type A:* #work_report.citation_summary.type_a_count
      - *Type B:* #work_report.citation_summary.type_b_count
    ]
  )

  // Cited by Table
  #if work_report.cited_by.len() >= 1 [
    #align(center, text(11pt)[_Cited by_])

    #table(
      columns: (auto, 3fr, 0.8fr, auto, auto, auto, auto),
      inset: 8pt,
      align: horizon,
      // Headers
      [], [*Title*], [*Type*], [*DOI*], [*Cite Type*], [*Publication Date*], [*Cited by count*],

      // Content
      ..work_report.cited_by.enumerate(start: 1).map(
        ((idx, cited_by)) => (
          table.cell([#idx]),
          table.cell([#cited_by.work.title]),
          table.cell([#cited_by.work.type]),
          table.cell([#if cited_by.work.ids.doi != none [#underline[#link(cited_by.work.ids.doi)[DOI]]] else [#align(center)[-]]]),
          table.cell([#if cited_by.citation_type == 0 [#text(rgb(SUCCESS))[Type A]] else [#text(rgb(ERROR))[Type B]]]),
          table.cell([#cited_by.work.publication_date]),
          table.cell([#cited_by.work.cited_by_count]),
        )
      ).flatten()
    )
  ]

  // Sources Table
  #if work.locations.len() >= 1 [
    #align(center, text(11pt)[_Sources_])
    #table(
      columns: (auto, 3fr, 2.5fr, 1fr, auto, auto, 1.2fr, auto),
      inset: 8pt,
      align: horizon,
      // Headers
      [], [*Name*], [*Publisher or institution*], [*Type*], [*ISSN-L*], [*Is OA*], [*License*], [*Version*],

      // Content
      ..work.locations.enumerate(start: 1).filter((location => location.last().source != none)).map(
          ((idx, location)) => (
            table.cell([#underline[#link(label("source_" + location.source.id.find(regex("S\d+$"))))[#idx]]]),
            table.cell([#location.source.display_name]),
            table.cell([#if location.source.host_organization_name != none [#location.source.host_organization_name] else [-]]),
            table.cell([#location.source.type]),
            table.cell([#if location.source.issn_l != none [#location.source.issn_l] else [-]]),
            table.cell([#if location.is_oa [#text(rgb(SUCCESS))[True]] else [#text(rgb(ERROR))[False]]]),
            table.cell([#if location.license != none [#location.license] else [-]]),
            table.cell([#if location.version != none [#work_driven_version.at(location.version)]]),
          )
        ).flatten(),
      ..work.locations.enumerate(start: 1).filter((location => location.last().source == none)).map(
          ((idx, location)) => (
            table.cell([#idx]),
            table.cell([#underline([#link(location.landing_page_url)[#location.landing_page_url]])]),
            table.cell([-]),
            table.cell([-]),
            table.cell([-]),
            table.cell([#if location.is_oa [#text(rgb(SUCCESS))[True]] else [#text(rgb(ERROR))[False]]]),
            table.cell([#if location.license != none [#location.license] else [-]]),
            table.cell([#if location.version != none [#work_driven_version.at(location.version)]]),
          )
        ).flatten()
    )
  ]
]


// Sources
#pagebreak()
= Sources.

#table(
  columns: (auto, 2.7fr, 2.56fr, 1.2fr, auto, auto, auto, auto),
  inset: 8pt,
  align: horizon,
  // Headers
  [], [*Name*], [*Publisher or institution*], [*Type*], [*ISSN-L*], [*Impact factor*], [*h-index*], [*Is OA*],

  // Content
  ..sources_summary.sources.enumerate(start: 1).map(
    ((idx, source)) => (
      table.cell([3.#idx. #label("source_" + source.id.find(regex("S\d+$")))]),
      table.cell([#if source.homepage_url != none [#underline[#link(source.homepage_url)[#source.display_name]]] else [#underline[#link(source.id)[#source.display_name]]]]),
      table.cell([#if source.host_organization_name != none [#source.host_organization_name] else [-]]),
      table.cell([#if source.type != none [#source.type] else [-]]),
      table.cell([#if source.issn_l != none [#source.issn_l] else [-]]),
      table.cell([#calc.round(source.summary_stats.at("2yr_mean_citedness"), digits: 3)]),
      table.cell([#source.summary_stats.h_index]),
      table.cell([#if source.is_oa [#text(rgb(SUCCESS))[True]] else [#text(rgb(ERROR))[False]]]),
    )
  ).flatten()
)


#pagebreak()
= Bibliography

Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. ArXiv. https://arxiv.org/abs/2205.01833
