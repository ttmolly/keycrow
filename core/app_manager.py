class AppManager:
    """
    Skeleton only. Not used by the main loop yet.
    Will own registration, navigation stack, and the main loop later.
    """

    def __init__(self):
        self._apps = {}
        self._stack = []

    def register(self, app):
        self._apps[app.name] = app

    def push(self, name: str):
        app = self._apps.get(name)
        if app is None:
            return
        if self._stack:
            self._stack[-1].on_exit()
        self._stack.append(app)
        app.on_enter()

    def pop(self):
        if not self._stack:
            return
        self._stack[-1].on_exit()
        self._stack.pop()
        if self._stack:
            self._stack[-1].on_enter()

    def current_app(self):
        if self._stack:
            return self._stack[-1]
        return None
