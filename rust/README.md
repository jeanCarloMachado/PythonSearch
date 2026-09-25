# ps_ui — native launcher for PythonSearch

A Spotlight-style macOS launcher for PythonSearch entries. One self-contained binary: no runtime
dependencies, no terminal emulator, no Python on the search path.

## Why

The terminal UI (`term_ui`) boots two Python interpreters per launch, repaints the whole screen on
every keystroke, and scores a 10k-entry BM25 corpus in Python as you type. This replaces the UI
half of that. Python remains the source of truth for entries and the executor for every action, so
interpreter semantics (`call_before`, `call_after`, `app_mode`, `focus_match`, `callable`) are
unchanged.

## Architecture

```
Caps Lock ──karabiner──> `ps_ui show`  (~8 ms, all process startup)
                             │ unix socket ~/.python_search/ps.sock
                             ▼
                   ps_ui daemon (LaunchAgent, always resident)
                       ├─ 10,751 entries in RAM, nucleo fuzzy matcher
                       ├─ eframe/egui window, pre-created, hidden
                       └─ file watcher → background `dump_entries`
                             │
   Enter ────────────────────┴──> `run_key "<key>"`   (unchanged Python)
```

### Source layout

```
rust/
├── Cargo.toml                    workspace
├── install.sh                    build → ~/.local/bin/ps_ui → LaunchAgent
├── com.jeanmachado.pythonsearch.plist
├── assets/                       Inter fonts, embedded into the binary
│
├── ps-core/                      no UI, no macOS. Fully testable.
│   ├── src/index.rs              ranking, two-phase search, default listing
│   ├── src/usage.rs              run history, recency ordering, boost
│   ├── src/actions.rs            shells out to run_key / entries_editor / share_entry
│   ├── src/entry.rs              entry model and display rules
│   ├── src/paths.rs              on-disk locations, binary resolution
│   ├── tests/ranking.rs          ranking behaviour
│   └── benches/search.rs         criterion, against the real 10k dump
│
├── ps-mac/
│   └── src/imp.rs                AppKit: panel chrome, vibrancy backdrop,
│                                 focus/activation, placement, local hour
│
└── ps-ui/                        the `ps_ui` binary
    ├── src/main.rs               daemon, show/hide, reload, focus tracking
    ├── src/app.rs                layout, input handling, rendering
    ├── src/theme.rs              palettes, metrics, fonts, time-of-day switch
    ├── src/daemon.rs             unix socket protocol
    └── src/watcher.rs            entries file watcher
```

| Crate | Role |
|---|---|
| `ps-core` | entry model, dump loading, ranking, usage boost, action dispatch |
| `ps-mac` | the `objc2` layer — everything that makes it behave like a system panel |
| `ps-ui` | the binary: daemon, socket client, window, and a headless `search` |

`ps-core` knows nothing about macOS or egui, which is why the ranking is testable without a
window. `ps-mac` is the only crate that touches AppKit.

### Touched outside this directory

| File | Change |
|---|---|
| `python_search/search/entries_loader.py` | `dump_entries()` — the rich JSON export this reads |
| `python_search/shortcut/mac_karabiner_elements.py` | expands `__PS_UI__` to the installed binary |
| `karabiner_base.json` | Caps Lock opens the launcher |
| `DESIGN.md` | describes both front ends |

`terminal_ui.py`, `QueryLogic.py`, `bm25_search.py`, `kitty_for_search_ui.py` and every interpreter
are untouched — `term_ui` remains a working fallback.

## Install

```sh
./install.sh
ps_ui show       # confirm the panel appears
```

`install.sh` builds, installs to `~/.local/bin/ps_ui`, generates the entries dump, and registers the
LaunchAgent so the daemon starts at login and restarts if it crashes. It deliberately does **not**
rebind Caps Lock — see below.

### The Caps Lock binding

Caps Lock opens the native launcher. `karabiner_base.json` holds the placeholder
`__PS_UI__ show`, which `python_search/shortcut/mac_karabiner_elements.py` expands to the absolute
path of the installed binary when generating `~/.config/karabiner/karabiner.json` — Karabiner runs
shell commands with a minimal PATH, so the full path is required.

Regenerate after changing anything with `python_search shortcuts`.

To roll back to the terminal UI, set that `shell_command` back to
`python_search search focus_or_open` and regenerate. `term_ui` is untouched and still works.

## Commands

| Command | What it does |
|---|---|
| `ps_ui daemon` | run the resident daemon (what the LaunchAgent invokes) |
| `ps_ui show` / `hide` / `toggle` | poke the running daemon |
| `ps_ui reload` | force a re-dump and reindex |
| `ps_ui quit` | stop the daemon |
| `ps_ui ui` | run the window directly, without a daemon — useful when iterating on the UI |
| `ps_ui search <query>` | headless ranking with timings, for debugging relevance |
| `ps_ui screenshot` | write the panel's framebuffer to `~/.python_search/screenshot.png` |
| `register_new_rust` | standalone form to register a new entry (key/value/type), prefilled from the clipboard |

## Keys

| Key | Action |
|---|---|
| type / Backspace | edit the query — every printable character is query text |
| ⌘A | select the whole query, so the next keystroke replaces it |
| ↑ ↓, Ctrl+P / Ctrl+N | move the selection; ↑ on the first row walks the previous queries |
| Enter | run the selected entry |
| ⌘1–⌘9 | run row N |
| ⌘C | copy the entry's value |
| Tab | open the entry's definition in the editor |
| ⌘⌫ | delete the entry (LLM-assisted, as in `term_ui`) |
| Ctrl+G | google the query — the equivalent of `?` in the terminal UI |
| ⌘R / Ctrl+R | re-dump and reindex, with a spinner and a confirmation |
| Ctrl+U / Ctrl+W | clear the query / drop the trailing word |
| Esc / Ctrl+C | hide (the daemon stays resident) |

## Appearance

Dark or light is chosen by the **time of day**, not the system appearance: light from 07:00, dark
from 19:00, local time. It is re-evaluated every frame, so an open panel flips over on its own at
the boundary. `NSCalendar` supplies the hour, so daylight saving and time-zone changes are handled
by the system.

`PS_UI_THEME` overrides it:

| Value | Effect |
|---|---|
| `dark` / `light` | force that palette |
| `system` | follow the macOS appearance instead |
| unset | time of day (the default) |

The hours are `LIGHT_FROM_HOUR` / `DARK_FROM_HOUR` in `ps-ui/src/theme.rs`.

## Window behaviour

The panel floats above other windows **only while it holds focus**. Click another window and it
drops to the normal window level, falling behind what you switched to — it stays on screen, greyed
out, rather than obstructing the app you moved to. Showing it again raises it back, so it still
appears over fullscreen apps and on whichever Space is active.

## Ranking

With an empty query the panel lists the **most recently used** entries, mirroring
`RecentKeys.get_latest_used_keys` in `python_search/events/latest_used_entries.py` — unique keys,
most recent first — rather than inventing a different default order. It reads the whole history
rather than that method's last-30-events window. Entries never run follow in natural order, so the
list is never empty.

For an actual query, `nucleo-matcher` (the matcher behind Helix and fzf-class tools) runs over two
haystacks per entry: the key at full weight, the content at 0.35. The result is multiplied by a usage boost derived from
`~/.python_search/data/searches_performed/` — history PythonSearch has been collecting for years
but never used for ranking. The boost is multiplicative and capped so it reorders near-ties without
letting a frequently used entry outrank a clearly better match.

Content is only scanned when the key pass did not fill the result list, which is what keeps the
common case in the low hundreds of microseconds.

```
$ cargo bench -p ps-core
search/c            127 µs
search/clv          142 µs
search/clv model    1.9 ms     # worst case: few key hits, so the content pass runs
```

BM25Plus was deliberately not ported. nucleo already handles the initials matching that
`bm25_search.py::split_key` hand-rolled (`gsu` → `git status update`), without the 2.7 MB pickle or
the NLTK import that costs `term_ui` ~390 ms of its startup.

## Data flow

The entries database is executable Python — ~14 entry groups are produced by function calls and
`entries/dates/important_dates.py` is date-relative — so it cannot be parsed statically.
`EntriesLoader.dump_entries()` writes a rich JSON dump (the full attribute bag, not just type and
content) atomically to `~/.python_search/data/entries.json`. The daemon loads it once at startup and
re-dumps in the background when `entries_main.py` or `entries/**` change.

## macOS notes

Two things here are non-obvious and were both found the hard way:

**The blur is a separate child window, not a subview.** The natural approach — make an
`NSVisualEffectView` the window's content view and reparent winit's view into it — cannot be used.
winit's view *is* the Metal surface, and moving it makes AppKit recompute cursor rects
re-entrantly, which panics winit 0.30 with `RefCell already borrowed` (`view.rs:871`). A subview
does not work either, since a subview always draws above its parent's own layer content and would
cover the rendering entirely. So the backdrop is a borderless child window ordered below the panel.

**The first responder must be restored after `setStyleMask`.** Changing the style mask rebuilds
the window's frame view and can leave the first responder nil. The window still reports
`isKeyWindow == true` and looks focused, but key events have nowhere to go, so typing silently does
nothing. `apply_panel_chrome` points the responder back at the render view afterwards.

**Activation may be refused the first time.** macOS can deny an activation request from an app
that has not been active recently, which shows up as needing to press the hotkey twice.
`order_front` re-checks `isKeyWindow` and retries a few times at 40 ms intervals, stopping as soon
as focus lands so it never fights the user clicking elsewhere.

**Focus needs an activation policy of `Regular` while the panel is up.** On recent macOS,
`activateIgnoringOtherApps:` is ignored for an accessory-policy app, so the panel appears but never
becomes key and typing goes to the app behind it. `order_front` switches to the regular
policy and activates via `NSRunningApplication`; `order_out` switches back to accessory. Switching
back *immediately* after activating instead drops the activation.

Note that an `LSUIElement`-style accessory app is not reported as the frontmost process by System
Events even while it holds key focus, so "which app is frontmost" is a misleading way to test this.
`PS_DEBUG=1` logs key-window transitions, which is the signal that matters.

All AppKit calls are deferred onto the main queue (`on_main_queue`), because every one of them
arrives from inside an egui frame while winit holds a borrow on its view.

## Debugging

Hiding is driven from `logic`, not `ui`: eframe runs no egui pass while the window is hidden, so
anything that must happen *after* hiding cannot live in `ui` or it will never run.


`PS_DEBUG=1` on the daemon logs input events and window/focus state to
`~/.python_search/daemon.log`.

`ps_ui screenshot` writes the panel's own framebuffer to `~/.python_search/screenshot.png`. It
captures the render target rather than the display, so it needs no macOS Screen Recording
permission — useful when iterating on the look over SSH or from a tool that cannot see the screen.

## Development

```sh
cargo test -p ps-core       # ranking behaviour
cargo bench -p ps-core      # per-keystroke latency against the real dump
cargo run -p ps-ui -- ui    # window without the daemon
```
