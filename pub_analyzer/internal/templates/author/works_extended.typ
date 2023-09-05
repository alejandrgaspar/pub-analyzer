== Extended info.
{% for work in report.works %}

{% if not loop.first %}
#pagebreak()
{% endif %}

=== #text()[#"{{ work.work.title.replace('"', '\\"') }}"] <work_{{ loop.index }}>

#linebreak()

{% if work.work.abstract %}
#text()[#"{{ work.work.abstract.replace('"', '\\"') }}"]

#linebreak()

{% endif %}

// Cards
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 30pt,
  [
    #align(center)[_Authorships_]
    #parbreak()
    {% for authorship in work.work.authorships[:10] %}
    - *{{ authorship.author_position }}:* #underline([#link("{{ authorship.author.orcid or authorship.author.id }}")[#text({% if authorship.author.display_name == report.author.display_name %}rgb("909d63"){% endif %})[{{ authorship.author.display_name }}]]])
    {% endfor %}
    {% if work.work.authorships|length > 10 %}
    - *...*
    {% endif %}
  ],
  [
    #align(center)[_Open Access_]
    #parbreak()
    - *Status:* {{ work.work.open_access.oa_status.value }}
    {% if work.work.open_access.oa_url %}- *URL:* #underline([#link("{{ work.work.open_access.oa_url }}")[{{ work.work.open_access.oa_url }}]]){% endif %}
  ],
  [
    #align(center)[_Citation_]
    #parbreak()
    - *Count:* {{ work.citation_resume.type_a_count + work.citation_resume.type_b_count }}
    - *Type A:* {{ work.citation_resume.type_a_count }}
    - *Type B:* {{ work.citation_resume.type_b_count }}
  ],
)

#linebreak()

// Cited by Table
{% if work.cited_by %}
#align(center, text(11pt)[_Cited by_])
#table(
  columns: (auto, 3fr, auto, auto, auto, auto, auto),
  inset: 8pt,
  align: horizon,
  // Headers
  [], [*Title*], [*Type*], [*DOI*], [*Cite Type*], [*Publication Date*], [*Cited by count*],

  // Content
  {% for cited_by_work in work.cited_by %}
  [{{ loop.index }}],
  [#"{{ cited_by_work.work.title.replace('"', '\\"') }}"],
  [{{ cited_by_work.work.type }}],
  [{% if cited_by_work.work.ids.doi %}#underline([#link("{{ cited_by_work.work.ids.doi }}")[DOI]]){% else %}-{% endif %}],
  [{% if cited_by_work.citation_type.value == 0 %}#text(rgb("909d63"))[Type A]{% else %}#text(rgb("bc5653"))[Type B]{% endif %}],
  [{{ cited_by_work.work.publication_date }}],
  [{{ cited_by_work.work.cited_by_count }}],
  {% endfor %}
)
{% endif %}

// Sources Table
{% if work.work.locations %}
#align(center, text(11pt)[_Sources_])
#table(
  columns: (auto, 3fr, 2fr, auto, auto, auto, auto, auto),
  inset: 8pt,
  align: horizon,
  // Headers
  [], [*Name*], [*Publisher or institution*], [*Type*], [*ISSN-L*], [*Is OA*], [*License*], [*Version*],

  // Content
  {% for location in work.work.locations %}
  {% if location.source %}
  [{{ loop.index }}],
  [#underline([#link("{{ location.landing_page_url }}")[#"{{ location.source.display_name }}"]])],
  [{{ location.source.host_organization_name or "-" }}],
  [{{ location.source.type }}],
  [{{ location.source.issn_l or "-" }}],
  [{% if location.is_oa %}#text(rgb("909d63"))[True]{% else %}#text(rgb("bc5653"))[False]{% endif %}],
  [{{ location.license or "-" }}],
  [{{ location.version.name or "-" }}],
  {% else %}
  [{{ loop.index }}],
  [#underline([#link("{{ location.landing_page_url }}")[#"{{ location.landing_page_url }}"]])],
  [-],
  [-],
  [-],
  [{% if location.is_oa %}#text(rgb("909d63"))[True]{% else %}#text(rgb("bc5653"))[False]{% endif %}],
  [{{ location.license or "-" }}],
  [{{ location.version.name or "-" }}],
  {% endif %}
  {% endfor %}
)
{% endif %}

{% endfor %}

#pagebreak()
