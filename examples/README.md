# Examples

| Folder | Mode | What it shows |
|---|---|---|
| `stop-motion-top5/` | countdown | Top 5 highest-grossing stop-motion films: money stats with bars, "Nx its budget" pill, ratings, a fun fact |
| `laika-evolution/` | timeline | Year-by-year "evolution" video with a trailer clip after every card |

Images and trailers are **not** included (they belong to their studios). Put your own files where `items.json` points:

```
posters/<slug>.jpg        2:3 portrait images
clips/<slug>-trailer.mp4  trailers you have the right to use
logo.png                  optional intro logo
```

Missing images render as a clean title card and missing clips are skipped, so you can render a draft first:

```bash
bash ../skills/countdown-video/scripts/make_countdown.sh stop-motion-top5/items.json top5.mp4
```

Data note: Chicken Run's budget and worldwide gross are from Box Office Mojo; the other entries' figures were taken from an earlier Movies Ocean video. Re-check numbers before publishing.
