#!/usr/bin/env python3
"""
Download the images used by LOADER_GUIDE.md.

Fetches product photos from littlebuckloader.com and video
thumbnails from the Little Buck Loader YouTube channel, and
saves them into the local "images" directory.

Files that are already present are skipped, so the script
is safe to re-run. Use --force to re-download everything.

Run s2_clean_images.py afterwards to bring the downloaded
files to the standard format.

Usage:
    python3 s1_download_images.py
    python3 s1_download_images.py --force

Created: 2026-09-04
Last updated: 2026-09-04
"""

import glob
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime

IMAGES_DIR = "images"
TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

CDN = ("https://images.squarespace-cdn.com/content/v1/"
       "56e7619f07eaa0d16966e42f")

# Product photos: (local name, full source URL)
PHOTOS = [
    ("little-buck-loader",
     f"{CDN}/64d69195-e0a7-4daa-b033-b09f0d235d5e/"
     "shop-buck-842155.jpg"),
    ("little-bull-loader",
     f"{CDN}/1585746191684-X92WBERMHUQ36JU8RIMY/"
     "shop-bull.jpg"),
    ("quiksystem-side-view",
     f"{CDN}/330020fe-2a69-4502-afa2-00c1e0c52a3a/"
     "little-bull-quiksystem-side-view.JPG"),
    ("quiksystem-front-view",
     f"{CDN}/ec3db1e1-08f9-4bb4-a241-441348acb5ad/"
     "little-bull-quiksystem-front-view.JPG"),
    ("quikbucket",
     f"{CDN}/34322e9d-d26b-4c26-a3e0-48287b4ca925/"
     "little-bull-quikbucket.JPG"),
    ("quikforks",
     f"{CDN}/cf34e55d-4959-4995-94ce-103fa11a63c0/"
     "little-bull-quikforks.jpeg"),
    ("quikgrapple",
     f"{CDN}/d12bc7c7-7a82-4104-b4d1-104e766008dd/"
     "little-bull-quikgrapple.jpeg"),
    ("quikpush-snow-pusher",
     f"{CDN}/352f82e3-5c90-4ca2-a873-d0eb9702c056/"
     "quik-snow-pusher.JPG"),
    ("z-buck",
     f"{CDN}/379aa95a-d9c0-451d-9b61-408211e05da1/"
     "hpp_-4-resized-330112.jpg"),
    ("caster-kit",
     f"{CDN}/c8317396-9174-408d-b9a1-9e31a61b05e1/"
     "roll-off-casters.png"),
    # Valve parts. Deere has no photo for MIA885144, so the
    # relief valve shot comes from a dealer listing for the
    # same valve family.
    ("valve-flow-control",
     "https://johndeere.widen.net/content/o23abfwmr5/"
     "webp/AM134625_iso1.webp"),
    ("valve-neutral-rod",
     "https://johndeere.widen.net/content/xzv7worvr4/"
     "webp/M146148_iso1.webp"),
    ("valve-pressure-relief",
     "https://www.greenpartstore.com/assets/images/"
     "jdturfparts/2018/am121248.jpg"),
]

# Video thumbnails: (local name, YouTube video id)
THUMBNAILS = [
    ("video-buck-attach-detach", "XtKedyOh9pk"),
    ("video-buck-attach", "ZFawwq8FRek"),
    ("video-bull-attach-updated", "kixGRO86FYc"),
    ("video-bull-step1-hood", "rSjgo0KZZdc"),
    ("video-bull-step2-supports", "KC_WQg4jeYQ"),
    ("video-bull-detach", "47YNdqzS61o"),
    ("video-bull-grappler", "pmSc1ZKGFqg"),
    ("video-relief-valve-install", "5ubyJVu5mPw"),
    ("video-caster-kit-install", "OhScUK2UUvk"),
    ("video-caster-kit-reattach", "7BRYCFL8UMA"),
    ("video-z-buck", "pD0BeGkJiVM"),
]

# Best first: YouTube serves 404 for sizes it does not have
THUMB_SIZES = ["maxresdefault", "sddefault", "hqdefault"]


# --------------------------------------------------------------
def log_message(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# --------------------------------------------------------------
def existing_file(name):
    """Return existing image path for name, or None."""
    matches = glob.glob(os.path.join(IMAGES_DIR, f"{name}.*"))
    return matches[0] if matches else None


# --------------------------------------------------------------
def target_path(name, url):
    """Build local path for name using the URL extension."""
    ext = os.path.splitext(url)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
        ext = '.jpg'
    return os.path.join(IMAGES_DIR, f"{name}{ext}")


# --------------------------------------------------------------
def fetch_bytes(url):
    """Download URL and return its bytes, or None."""
    request = urllib.request.Request(
        url,
        headers={'User-Agent': USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request,
                                    timeout=TIMEOUT) as resp:
            return resp.read()
    except (urllib.error.URLError, OSError) as exc:
        log_message(f"  failed: {exc}")
        return None


# --------------------------------------------------------------
def save_image(name, url, force):
    """Download one image unless it is already present."""
    present = existing_file(name)
    if present and not force:
        log_message(f"Skipping {name} - already have "
                    f"{os.path.basename(present)}")
        return False

    log_message(f"Downloading {name}")
    data = fetch_bytes(url)
    if not data:
        return False

    if present and force:
        os.remove(present)

    path = target_path(name, url)
    with open(path, 'wb') as handle:
        handle.write(data)

    size_kb = len(data) // 1024
    log_message(f"  saved {path} ({size_kb} KB)")
    return True


# --------------------------------------------------------------
def thumbnail_url(video_id):
    """Return the best available thumbnail URL, or None."""
    base = "https://img.youtube.com/vi"
    for size in THUMB_SIZES:
        url = f"{base}/{video_id}/{size}.jpg"
        request = urllib.request.Request(
            url,
            method='HEAD',
            headers={'User-Agent': USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request,
                                        timeout=TIMEOUT):
                return url
        except (urllib.error.URLError, OSError):
            continue
    log_message(f"  no thumbnail found for {video_id}")
    return None


# --------------------------------------------------------------
def download_photos(force):
    """Download all product photos."""
    count = 0
    for name, url in PHOTOS:
        if save_image(name, url, force):
            count += 1
    return count


# --------------------------------------------------------------
def download_thumbnails(force):
    """Download all video thumbnails."""
    count = 0
    for name, video_id in THUMBNAILS:
        if existing_file(name) and not force:
            log_message(f"Skipping {name} - already present")
            continue
        url = thumbnail_url(video_id)
        if url and save_image(name, url, force):
            count += 1
    return count


# --------------------------------------------------------------
def main():
    """Download every image needed by LOADER_GUIDE.md."""
    force = '--force' in sys.argv

    log_message("Starting image download")
    os.makedirs(IMAGES_DIR, exist_ok=True)

    photos = download_photos(force)
    thumbs = download_thumbnails(force)

    log_message("=" * 50)
    log_message(f"Product photos downloaded: {photos}")
    log_message(f"Video thumbnails downloaded: {thumbs}")
    log_message(f"Files now in {IMAGES_DIR}: "
                f"{len(os.listdir(IMAGES_DIR))}")
    log_message("Next: python3 s2_clean_images.py")


# --------------------------------------------------------------
if __name__ == "__main__":
    main()
