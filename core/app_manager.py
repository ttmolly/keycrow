class AppManager:
    """
    Owns registered apps and the active screen.
    Public API only — no direct _apps access from outside.
    """

    def __init__(self):
        self._apps = {}
        self._current = None

    def register(self, app):
        self._apps[app.name] = app

    def get(self, name: str):
        """Return an app by name, or None."""
        return self._apps.get(name)

    def open(self, name: str):
        """
        Switch to an app by name.
        Calls on_exit on the previous app and on_enter on the new one.
        """
        app = self._apps.get(name)
        if app is None:
            return None

        if self._current is not None and self._current is not app:
            self._current.on_exit()

        self._current = app
        app.on_enter()
        return app

    def current(self):
        """Return the active app, or None."""
        return self._current

    def current_name(self):
        if self._current is None:
            return None
        return self._current.name
