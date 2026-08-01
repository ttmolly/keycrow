class BaseApp:
    """
    Minimal base class for every KeyCrow application.
    Grow only when every app genuinely needs something new.
    """

    name = "Unnamed"

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle_input(self, button: str):
        """Return None to stay, or 'back' to request navigation back."""
        return None

    def update(self):
        pass

    def draw(self, device):
        raise NotImplementedError("Applications must implement draw().")
