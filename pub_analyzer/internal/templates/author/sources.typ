// Sources
= Sources.

#table(
  columns: (auto, 3fr, 2fr, auto, auto, auto, auto, auto),
  inset: 8pt,
  align: horizon,
  // Headers
  [], [*Name*], [*Publisher or institution*], [*Type*], [*ISSN-L*], [*Impact factor*], [*h-index*], [*Is OA*],

  // Content
  {% for source in report.sources_summary.sources %}
  [3.{{ loop.index }}. #label("source_{{ source.id.path.rpartition("/")[2] }}")],
  [#underline([#link("{{ source.homepage_url }}")[#"{{ source.display_name }}"]])],
  [{{ source.host_organization_name or "-" }}],
  [{{source.type }}],
  [{{ source.issn_l or "-" }}],
  [{{ source.summary_stats.two_yr_mean_citedness|round(3) }}],
  [{{ source.summary_stats.h_index }}],
  [{% if source.is_oa %}#text(rgb(SUCCESS))[True]{% else %}#text(rgb(ERROR))[False]{% endif %}],
  {% endfor %}
)
