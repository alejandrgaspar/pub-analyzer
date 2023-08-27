// Sources
= Sources.

#table(
  columns: (auto, 3fr, 2fr, auto, auto, auto),
  inset: 8pt,
  align: horizon,
  // Headers
  [], [*Name*], [*Publisher or institution*], [*Type*], [*ISSN-L*], [*Is Open Access*],

  // Content
  {% for source in report.sources_resume.sources %}
  [{{ loop.index }}],
  [#underline([#link("{{ source.id }}")[#"{{ source.display_name }}"]])],
  [{{ source.host_organization_name or "-" }}],
  [{{source.type }}],
  [{{ source.issn_l or "-" }}],
  [{% if source.is_oa %}#text(rgb("909d63"))[True]{% else %}#text(rgb("bc5653"))[False]{% endif %}],
  {% endfor %}
)
