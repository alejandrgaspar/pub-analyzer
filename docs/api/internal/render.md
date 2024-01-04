# Render

Pub Analyzer provides the option to generate reports in PDF format, that summarizes all the available information. This process utilizes [typst](https://typst.app/){target=_blank}, the new markup-based typesetting system for the sciences. Let's see how to render a scientific production report for an author.

```python
import asyncio

from pub_analyzer.internal.render import render_report
from pub_analyzer.models.report import AuthorReport

report = AuthorReport(**kwargs) # (1)!
pdf_bytes = asyncio.run(render_report(report=report, file_path='demo.typ'))

with open('demo.pdf', mode="wb") as file:
    file.write(pdf_bytes)
```

1. Use real information instead of `**kwargs` placeholder.


!!! Warning
    Currently, I have not discovered an efficient approach to generate a complete PDF summary for institutions, covering the huge volume of data in the reports. I am open to new ideas and suggestions about it.

::: pub_analyzer.internal.render
    options:
        show_source: false
