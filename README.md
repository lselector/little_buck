# little_buck

Notes and reference material for the Little Buck / Little Bull
front-end loaders for John Deere garden tractors.

Both loaders are made by the same company, Little Buck Loader, LLC
(Sycamore, Illinois). The Little Buck is the entry model, the Little
Bull is the heavy-lift model.

## Contents

- **[LOADER_GUIDE.md](LOADER_GUIDE.md)** - how to attach, detach,
  operate and maintain the loaders. Includes the hydraulic hose color
  map, ballast and greasing requirements, the three valves and the
  transaxle pressure relief upgrade for a 4WD X700, troubleshooting,
  and links to the manufacturer's videos and the operator's manual.
- `images/` - local copies of the pictures used by the guide.
- `s1_download_images.py` - fetch those pictures from the source.
- `s2_clean_images.py` - bring them to the standard format.
- `s3_make_pdf.py` - render the guide to `LOADER_GUIDE.pdf`.
- `styles.css` - print styling for the PDF.
- `myprompts.md` - working notes.

## Rebuilding the images

The guide uses local images so it reads offline. Two steps, run from
the repository root:

```sh
python3 s1_download_images.py     # add --force to refetch
python3 s2_clean_images.py
```

`s1` pulls product photos from littlebuckloader.com and video
thumbnails from YouTube into `images/`, skipping anything already
there. `s2` converts every image to **640x480 JPEG at 72 DPI**,
trimmed of stray border whitespace, scaled to fill a content box and
centered on a white canvas with a 16 px margin. Both are safe to
re-run: `s2` skips files it has already stamped, and backs the
directory up to `~/backups` before touching anything.

The guide uses plain Markdown image syntax rather than HTML `<img>`
tags, because many Markdown viewers do not render inline HTML. That
syntax has no width attribute, so the 640x480 canvas is the size a
reader actually sees. To display images larger or smaller, change
`CANVAS_W` / `CANVAS_H` and re-run `s2`.

`s2` needs ImageMagick:

```sh
brew install imagemagick
```

To change the output format, edit the constants at the top of
`s2_clean_images.py` (`CANVAS_W`, `CANVAS_H`, `MARGIN`, `QUALITY`).
Changing the canvas is picked up automatically, since the skip test
compares dimensions. Changing anything that does not alter the
dimensions, such as `MARGIN` or `QUALITY`, needs `STAMP` bumped as
well, or the already-processed files will simply be skipped.

You can also standardize single files:
`python3 s2_clean_images.py images/foo.png`.

The images belong to Little Buck Loader, LLC and are kept here only as
a personal reference copy.

## Making the PDF

```sh
python3 s3_make_pdf.py                    # LOADER_GUIDE.md -> .pdf
python3 s3_make_pdf.py README.md          # any other file
python3 s3_make_pdf.py README.md out.pdf  # explicit output
```

It converts the Markdown with the `markdown` library and lays out the
pages with WeasyPrint. Headings are slugified the way GitHub does it,
so the links in the Contents section stay clickable in the PDF, and
WeasyPrint turns the headings into PDF bookmarks for the sidebar.

All styling is in `styles.css`, so the page size, margins, fonts and
colors can be changed without touching Python. Images are resolved
relative to the Markdown file, so run `s1` and `s2` first.

Dependencies, both already present in the standard venv:

```sh
pip install markdown weasyprint
```

`LOADER_GUIDE.pdf` is a build artifact. It is regenerated in about a
second, so there is no need to commit it. Add it to `.gitignore` if
you would rather it stayed out of the repository.

## Quick links

- <https://www.littlebuckloader.com>
- <https://www.youtube.com/@LittleBuckLoader>
