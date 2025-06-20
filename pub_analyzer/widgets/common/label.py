"""Label widget but with reactivity enable."""

from rich.console import RenderableType
from rich.text import Text
from textual.app import RenderResult
from textual.reactive import reactive
from textual.widget import Widget


class ReactiveLabel(Widget):
    """A Label widget but with reactivity enable."""

    renderable: reactive[RenderableType] = reactive[RenderableType]("", layout=True)

    def __init__(
        self,
        renderable: RenderableType = "",
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.markup = markup
        self.renderable = renderable

    def render(self) -> RenderResult:
        """Render widget."""
        if isinstance(self.renderable, str):
            if self.markup:
                return Text.from_markup(self.renderable)
            else:
                return Text(self.renderable)
        else:
            return self.renderable
