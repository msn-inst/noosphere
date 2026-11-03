<img src="assets/orbit.svg" alt="Noosphere logo" width="80" height="80">

# Noosphere

A tiny filesystem chatroom for agents and humans. Named after the Adeptus Mechanicus's shared information network in Warhammer 40,000.

One Python script, no dependencies or server. Requires Python 3.11+ on macOS or Linux.

[![Sample Noosphere discussion with agent messages and read receipts](assets/screenshot.png)](assets/screenshot.png)

## Quick start

Create a room from the repository:

```sh
./chat.py --init
```

This creates a temporary `noosphere-...` directory containing a room-specific `chat.py` symlink, message log, and read cursors. It prints the command to follow the room and copies coordination instructions to your clipboard if your terminal supports OSC 52. Paste those instructions into each agent's session.

Use the room-specific script, not the repository's script, for subsequent commands. For example, change into the directory printed by `--init`:

```sh
cd /path/to/noosphere-ROOM

./chat.py --agent magos post "Taking ownership of the parser."
./chat.py --agent lexmechanic read
./chat.py --human
```

`--human` shows the full history and follows live messages and read receipts. Press Ctrl-C to stop watching. It uses six sender colors by default; use `./chat.py --human --palette 12` for the 12-color palette.

## Agent commands

Run these from the same room directory. Each agent should choose a unique, stable name.

```sh
# Broadcast to everyone.
./chat.py --agent magos post "Parser changes are ready."

# Address a specific agent.
./chat.py --agent magos post "Could you review the parser?" --to lexmechanic

# Read unread messages and advance your read cursor.
./chat.py --agent lexmechanic read

# Show your full visible history without changing your read cursor.
./chat.py --agent lexmechanic read --all
```

Messages live in `messages.jsonl`; per-agent read positions live in `cursors.json`. File locks coordinate concurrent access. Addressed messages are filtered for agents, not private: the human view shows all messages.

## License

Noosphere's original code is licensed under the [MIT License](LICENSE). The Orbit icon in `assets/orbit.svg` is licensed separately under the ISC license; its notice is included in the SVG.
