#!/usr/bin/env python3
import argparse
import base64
import fcntl
import json
import os
import shlex
import sys
import tempfile
import textwrap
import time
from datetime import UTC, datetime
from pathlib import Path

SENDER_COLORS = (203, 208, 220, 154, 46, 48, 51, 39, 69, 135, 201, 205)


def display_human(messages, cursors, previous_cursors, palette):
    receipts = [
        {"position": position, "reader": agent}
        for agent, position in cursors.items()
        if position > previous_cursors.get(agent, 0)
    ]
    terminal = sys.stdout.isatty()
    for message in sorted(messages + receipts, key=lambda message: message["position"]):
        if "reader" in message:
            receipt = f"  ✓ {message['reader']} read"
            if terminal:
                receipt = f"\033[2m{receipt}\033[0m"
            print(receipt, flush=True)
            continue
        timestamp = datetime.fromisoformat(message["at"]).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sender = message["agent"]
        recipient = message["to"]
        body = message["body"]
        if terminal:
            width = os.get_terminal_size().columns - 4
            body = "\n".join(textwrap.fill(line, width=width) for line in body.split("\n"))
            index = sum(sender.encode()) % palette
            color = str(91 + index) if palette == 6 else f"38;5;{SENDER_COLORS[index]}"
            sender = f"\033[1;{color}m{sender}\033[0m"
            timestamp = f"\033[2m{timestamp}\033[0m"
            recipient = f"\033[2m{recipient}\033[0m"
        body = body.replace("\n", "\n  │ ")
        print(f"  {timestamp}  {sender} → {recipient}\n  │ {body}\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Noosphere: a tiny filesystem chatroom for agents and humans.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--init", action="store_true", help="Create a room and copy its agent prompt")
    mode.add_argument("--human", action="store_true", help="Show history and follow live; Ctrl-C to stop")
    parser.add_argument("--agent", help="Your unique, stable name")
    parser.add_argument(
        "--palette", type=int, choices=(6, 12), default=6, help="Sender colors for --human (default: 6)"
    )
    commands = parser.add_subparsers(dest="command")
    post = commands.add_parser("post", help="Send a message")
    post.add_argument("message")
    post.add_argument("--to", default="all")
    read = commands.add_parser("read", help="Read your unread messages")
    read.add_argument("--all", action="store_true", help="Show history without changing your unread cursor")
    args = parser.parse_args()
    if (args.init or args.human) and args.command:
        parser.error("--init and --human do not take a command")
    root = Path(__file__).absolute().parent.resolve()
    if args.init:
        root = Path(tempfile.mkdtemp(prefix="noosphere-"))
        script = root / "chat.py"
        script.symlink_to(Path(__file__).resolve())
        command = shlex.quote(str(script))
        (root / "messages.jsonl").touch()
        (root / "cursors.json").write_text("{}")
        prompt = (
            f"Coordinate using: {command}\n"
            "Choose a unique NAME. Read: --agent NAME read. Send: --agent NAME post 'message' [--to NAME].\n"
            "Announce your scope, check messages regularly, agree before shared changes, "
            "and share blockers/handoffs. Respect user restrictions.\n"
        )
        print(f"\033]52;c;{base64.b64encode(prompt.encode()).decode()}\a", end="", flush=True)
        print(f"Follow messages: {command} --human")
        return
    if not args.human and not (args.command and args.agent):
        parser.error("use --init, --human, or --agent NAME read/post")
    if args.human:
        print(
            f"\n  NOOSPHERE · {root.name}\n  {root}\n  Following all messages · local time · Ctrl-C to stop\n",
            flush=True,
        )
    cursors_path = root / "cursors.json"
    cursors = {}
    previous_cursors = {}
    with (root / "messages.jsonl").open("r" if args.human else "r+", encoding="utf-8") as log:
        while True:
            fcntl.flock(log, fcntl.LOCK_SH if args.human else fcntl.LOCK_EX)
            if args.command == "post":
                message = {
                    "at": datetime.now(UTC).isoformat(timespec="seconds"),
                    "agent": args.agent,
                    "to": args.to,
                    "body": args.message,
                }
                log.seek(0, 2)
                log.write(json.dumps(message) + "\n")
                log.flush()
                messages = [message]
            else:
                if not args.human and not args.all:
                    cursors = json.loads(cursors_path.read_text())
                    log.seek(cursors.get(args.agent, 0))
                messages = []
                while line := log.readline():
                    message = json.loads(line)
                    if args.human:
                        message["position"] = log.tell()
                    messages.append(message)
                if not args.human and not args.all:
                    cursors[args.agent] = log.tell()
                    cursors_path.write_text(json.dumps(cursors))
            if args.human:
                cursors = json.loads(cursors_path.read_text())
            fcntl.flock(log, fcntl.LOCK_UN)
            if args.human:
                display_human(messages, cursors, previous_cursors, args.palette)
                previous_cursors = cursors
                time.sleep(0.2)
                continue
            visible_messages = [
                message
                for message in messages
                if message["to"] == "all" or args.agent in (message["agent"], message["to"])
            ]
            for message in visible_messages:
                print(f"[{message['at']}] {message['agent']} -> {message['to']}\n{message['body']}\n", flush=True)
            if not visible_messages:
                print("No messages." if args.all else "No unread messages.")
            return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
