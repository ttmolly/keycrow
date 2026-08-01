# KeyCrow Architecture

KeyCrow is a modular handheld Linux platform.
Linux is the operating system. KeyCrow is the experience on top of it.

## Layers

Hardware / Platform → Services → Applications → UI → User

- **Core** – BaseApp, AppManager, configuration, input
- **UI** – drawing, menus, status bar, splash renderer, widgets
- **Apps** – user workflows
- **Services** – reusable operations (created only when needed)
- **Assets** – icons, fonts, splashes, animations

## Rules

- One-way dependencies
- Applications never depend on each other
- UI never contains business logic
- Services never draw
- Hardware details stay isolated

## Navigation

AppManager owns a navigation stack. Apps request “back”; they never switch to other apps directly.
