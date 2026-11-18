# Contributing to Countdown Video Skill

Thanks for helping make list videos easier for every creator! 🎬

## Ways to help

- **Bug reports:** a card that overflows, a clip that won't lay in, audio out of sync. Include your OS, Python and ffmpeg versions, the command and the error output, and your `items.json` (without private paths).
- **Themes and layouts:** new colour themes, card layouts, a vertical (9:16) layout, new stat or rating widgets.
- **Example `items.json` files** under `examples/<topic>/`, with every number sourced in `sources`.
- **Docs and translations:** improvements to `README.md`, `README.hi.md` or `SKILL.md`.

## Ground rules

- **No copyrighted media.** Don't commit posters, trailers, stills, logos or music you don't own. Examples point to files users add themselves.
- **No invented data.** Every number in an example must have a source URL.
- **Deterministic frames.** Everything in `seek(t)` must come from `t` alone: no timers, CSS animations or `Math.random`.
- **Check before you send.** Run `build_countdown.py` (no JS errors), look at a few frames, and for pipeline changes render a short test video end to end.
- **No generated files.** `_work/`, MP4s, WAVs and QA sheets are ignored by `.gitignore`.

## Pull requests

1. Fork the repo and create a branch: `feat/<short-name>` or `fix/<short-name>`.
2. Keep the change focused, and describe what it does and how you tested it.
3. Add a screenshot for visual changes.
4. Be kind in reviews. Beginners are welcome here.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).

Made by [Smiling Buddha](https://github.com/i-smiling-buddha) · [DESITechnology](https://desitechnology.com).
