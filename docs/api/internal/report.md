# Report

If you're using pub analyzer as an external library, you'll find pretty much everything you need here. This is where all the magic happens. :magic_wand:

Suppose you already have an author model. Let's see how to generate a scientific production report of that author.

```python
import asyncio

from pub_analyzer.internal.report import make_author_report
from pub_analyzer.models.author import Author

author = Author(**kwargs) # (1)!
report = asyncio.run(make_author_report(author=author)) # (2)!
```

1. Use real information instead of `**kwargs` placeholder.
2. Functions are defined as asynchronous since their primary use occurs within a TUI context. We apologize for any inconvenience this may cause.

And that's it! that's all. Well, maybe you want to export the report to a format like JSON, that's where pydantic does its magic.


```python
with open("report.json", mode="w") as file:
    file.write(report.model_dump_json(indent=2, by_alias=True)) # (1)!
```

1.  It is important that you use the `by_alias=True` parameter, otherwise you will not be able to import correctly using the pub analyzer models.

:sparkles: ta-da!


!!! Note "Early stages"
    In the early phases of the project, before Pub Analyzer existed as a TUI, the main goal was to emulate an Excel file. This file, based on input tables containing the works of an author and the works that reference them, categorized the types of citations. Later, the idea was expanded to encompass automating works retrieval. It was during this period that I stumbled across OpenAlex, and as they say, one thing led to another.

::: pub_analyzer.internal.report
    options:
      filters: []
