// Works
= Works.
#linebreak()

#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 30pt,
  [
    #align(center)[_Citation metrics_]
    #parbreak()
    - *Count:* {{ report.citation_resume.type_a_count + report.citation_resume.type_b_count }}
    - *Type A:* {{ report.citation_resume.type_a_count }}
    - *Type B:* {{ report.citation_resume.type_b_count }}
  ],
  [
    #align(center)[_Work Type_]
    #parbreak()
    {% for work_type in report.works_type_resume %}
    - *{{ work_type.type_name }}:* {{ work_type.count }}
    {% endfor %}
  ],
  [
    #align(center)[_Open Access_]
    #parbreak()
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 15pt,
      [
        - *gold:* {{report.open_access_resume.gold}}
        - *green:* {{report.open_access_resume.green}}
        - *hybrid:* {{report.open_access_resume.hybrid}}
      ],
      [
        - *bronze:* {{report.open_access_resume.bronze}}
        - *closed:* {{report.open_access_resume.closed}}
      ],
    )
  ],
)

#linebreak()

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
  [{{ work.citation_resume.type_a_count + work.citation_resume.type_b_count }}],
  [{{ work.citation_resume.type_a_count }}],
  [{{ work.citation_resume.type_b_count }}],
  [{{ work.work.open_access.oa_status.value }}],
  {% endfor %}
)
#pagebreak()
