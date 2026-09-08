#!/usr/bin/env python3
"""
Download the images used by LOADER_GUIDE.md and by
LITTLE_BUCK_PRODUCTS.md.

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
Last updated: 2026-09-08
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
    # Catalog photos for LITTLE_BUCK_PRODUCTS.md
    ("antler-grappler",
     f"{CDN}/134e9403-f88c-480c-ae37-d54a9c2ad8de/"
     "grapple-logs-2-664532.jpg"),
    ("jd-talon",
     f"{CDN}/d7cefa44-ff48-43a7-ba60-2e2ff2c3ae54/"
     "jd-talon-2.png"),
    ("kbx-talon",
     f"{CDN}/0e6c8311-ab06-4eb6-bb27-db0fc2432cd3/"
     "2.jpg"),
    ("pallet-fork-kit",
     f"{CDN}/689cb193-c57a-4e38-b11f-8db0ec2f98fb/"
     "IMG_1356-945212.jpg"),
    ("boom-pole",
     f"{CDN}/6c7b4be4-a80a-4d46-a4e9-6dddfed784a9/"
     "boom-pole-3.jpg"),
    ("weight-bar",
     f"{CDN}/8c2aae25-32ba-460e-b48c-0674081fa69f/"
     "hpp_-29-b7a813d2c29ce49b0fdfa5d2ee2824e5.jpg"),
    ("weight-basket",
     f"{CDN}/af7850d7-8aa9-4cf8-b823-c1ba19d465d3/"
     "basket-web-162727.jpg"),
    ("bucket-extender",
     f"{CDN}/0eff0e1c-da73-444d-86a7-f298e2c673b6/"
     "extender-front.png"),
    ("top-plate",
     f"{CDN}/4c2e09aa-775f-4999-96b8-b0f1ff745daf/"
     "top-plate-2-972669.jpg"),
    ("build-kit",
     f"{CDN}/e559ea57-4715-4d51-919e-9773c611b601/"
     "IMG-3121-454368.jpg"),
    ("replacement-bucket",
     f"{CDN}/c06a7b45-dd64-4e13-b36d-af8359770f4a/"
     "replacement-bucket.jpg"),
    ("loader-conversion-kit",
     f"{CDN}/357c4389-db4f-48fd-8706-ae748bd02877/"
     "buck-conversion.png"),
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
