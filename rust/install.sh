#!/usr/bin/env bash
# Build the launcher, install the binary, and register the resident daemon.
#
# Does not touch Karabiner: switching the Caps Lock binding is a separate, deliberate step
# (see README.md), because it is the user's primary launcher hotkey.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${PS_INSTALL_DIR:-$HOME/.local/bin}"
LABEL="com.jeanmachado.pythonsearch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

echo "==> Building release binary"
cargo build --release --manifest-path "$HERE/Cargo.toml" -p ps-ui

echo "==> Installing to $INSTALL_DIR/ps_ui"
mkdir -p "$INSTALL_DIR"
install -m 0755 "$HERE/target/release/ps_ui" "$INSTALL_DIR/ps_ui"

# The PythonSearch console scripts live next to whichever python has the package installed.
BIN_DIR="$(dirname "$(command -v run_key)")"
echo "==> PythonSearch binaries: $BIN_DIR"

echo "==> Generating the entries dump"
"$BIN_DIR/python_search" _entries_loader dump_entries

echo "==> Writing $PLIST"
mkdir -p "$HOME/Library/LaunchAgents"
sed -e "s|__BINARY__|$INSTALL_DIR/ps_ui|g" \
    -e "s|__BIN_DIR__|$BIN_DIR|g" \
    -e "s|__HOME__|$HOME|g" \
    "$HERE/$LABEL.plist" > "$PLIST"

echo "==> (Re)starting the daemon"
launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$PLIST"
launchctl kickstart -k "gui/$UID/$LABEL"

echo
echo "Done. Try it with:   $INSTALL_DIR/ps_ui show"
echo "Logs:                $HOME/.python_search/daemon.log"
