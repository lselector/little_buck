#!/usr/bin/env python3
"""
Bring every image under "images" to one standard format.

Each file is converted to JPEG, trimmed of stray border
whitespace, scaled to fill the content box, then centered on
a fixed white canvas so that all images come out the same
size with even margins around them. Small sources are scaled
up so that every picture carries the same visual weight.

Standard output: 640x480 JPEG, 72 DPI, 16 px minimum
margin, white background. That size is chosen so the images
render at a sensible size in a Markdown viewer, which cannot
resize them.

Images are processed in place. A timestamped copy of the
directory is written to ~/backups first, and only the three
most recent backups are kept. Files that already match the
standard are skipped, so the script is safe to re-run.

Usage:
    python3 s2_clean_images.py
    python3 s2_clean_images.py images/quikforks.jpeg

Created: 2026-09-04
Last updated: 2026-09-04
"""

import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

IMAGES_DIR = "images"
SUPPORTED_EXTENSIONS = [
    '.avif', '.heic', '.jpeg', '.jpg',
    '.png', '.webp', '.gif', '.bmp'
]

# Standard output geometry. Markdown has no width
# attribute, so images display at their natural size and
# this canvas is what the reader actually sees.
CANVAS_W = 640
CANVAS_H = 480
MARGIN = 16
QUALITY = 85
TARGET_DPI = 72
BG_COLOR = "white"
TRIM_FUZZ = "2%"

# Stamped into every processed file. A source image can
# coincidentally match the canvas size without having been
# trimmed or margined, so size alone cannot detect our work.
STAMP = "lbl-standard-v1"

CONVERT_LOG = "/tmp/convert.log"
MAGICK = shutil.which('magick') or shutil.which('convert')
IDENTIFY = shutil.which('identify')


# --------------------------------------------------------------
def log_message(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# --------------------------------------------------------------
def check_imagemagick():
    """Check that ImageMagick tools are available."""
    if MAGICK and IDENTIFY:
        log_message(f"ImageMagick found: {MAGICK}")
        return True
    log_message(
        "ERROR: ImageMagick not found. "
        "Install: brew install imagemagick"
    )
    return False


# --------------------------------------------------------------
def create_backup(source_dir, backup_root):
    """Create backup of directory in timestamped root."""
    if not os.path.exists(source_dir):
        log_message(f"ERROR: {source_dir} not found")
        return None

    os.makedirs(backup_root, exist_ok=True)
    dir_name = os.path.basename(os.path.abspath(source_dir))
    backup_dir = os.path.join(backup_root, dir_name)

    log_message(f"Creating backup: {backup_dir}")
    try:
        shutil.copytree(source_dir, backup_dir)
        log_message(f"Backup created: {backup_dir}")
        return backup_dir
    except (OSError, shutil.Error) as exc:
        log_message(f"ERROR: Backup failed: {exc}")
        return None


# --------------------------------------------------------------
def find_images_for_ext(directory, ext):
    """Find images for single extension."""
    patterns = [f"**/*{ext}", f"**/*{ext.upper()}"]
    files = []
    for pattern in patterns:
        found = glob.glob(
            os.path.join(directory, pattern),
            recursive=True
        )
        files.extend(found)
    return files


# --------------------------------------------------------------
def find_image_files(directory):
    """Find all image files under a directory."""
    log_message(f"Searching in {directory}...")

    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        image_files.extend(find_images_for_ext(directory, ext))

    image_files = sorted(set(image_files))
    log_message(f"Found {len(image_files)} images")
    return image_files


# --------------------------------------------------------------
def parse_dpi_value(dpi_str):
    """Parse DPI value from an identify string."""
    try:
        if ' ' in dpi_str:
            return float(dpi_str.split()[0])
        return float(dpi_str)
    except (ValueError, IndexError):
        return TARGET_DPI


# --------------------------------------------------------------
def get_image_info(filepath):
    """Get image dimensions, format, and DPI."""
    try:
        result = subprocess.run(
            [IDENTIFY, '-format', '%w %h %m %x %c', filepath],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        log_message(f"WARNING: identify failed: {exc}")
        return None

    parts = result.stdout.strip().split()
    if len(parts) < 3:
        return None

    try:
        return {
            'width': int(parts[0]),
            'height': int(parts[1]),
            'format': parts[2],
            'dpi': parse_dpi_value(
                parts[3] if len(parts) > 3 else "72"
            ),
            'stamp': parts[4] if len(parts) > 4 else "",
        }
    except ValueError:
        return None


# --------------------------------------------------------------
def describe_deviations(info):
    """List the ways an image differs from the standard."""
    reasons = []

    if info.get('stamp') != STAMP:
        reasons.append("not stamped as standardized")

    if info['format'].upper() != 'JPEG':
        reasons.append(f"format is {info['format']}")

    if info['width'] != CANVAS_W or info['height'] != CANVAS_H:
        reasons.append(
            f"size {info['width']}x{info['height']} is not "
            f"{CANVAS_W}x{CANVAS_H}"
        )

    if abs(info['dpi'] - TARGET_DPI) > 1:
        reasons.append(f"DPI is {info['dpi']}")

    return reasons


# --------------------------------------------------------------
def needs_processing(filepath):
    """Check whether an image is not yet standardized."""
    info = get_image_info(filepath)
    if not info:
        log_message(f"Cannot read {filepath}, will process it")
        return True

    reasons = describe_deviations(info)
    if reasons:
        log_message(
            f"Needs processing: {filepath} - "
            f"{', '.join(reasons)}"
        )
        return True

    log_message(f"Skipping {filepath} - already standard")
    return False


# --------------------------------------------------------------
def build_standardize_cmd(src, dst):
    """Build the ImageMagick command for one image."""
    box_w = CANVAS_W - 2 * MARGIN
    box_h = CANVAS_H - 2 * MARGIN
    return [
        MAGICK, src,
        '-auto-orient',
        '-background', BG_COLOR,
        '-alpha', 'remove', '-alpha', 'off',
        '-colorspace', 'sRGB',
        '-fuzz', TRIM_FUZZ, '-trim', '+repage',
        '-resize', f'{box_w}x{box_h}',
        '-gravity', 'center',
        '-extent', f'{CANVAS_W}x{CANVAS_H}',
        '-strip',
        '-set', 'comment', STAMP,
        '-density', str(TARGET_DPI),
        '-units', 'PixelsPerInch',
        '-quality', str(QUALITY),
        dst
    ]


# --------------------------------------------------------------
def run_standardize(src, dst):
    """Run ImageMagick, returning True on success."""
    try:
        with open(CONVERT_LOG, 'a') as log_file:
            subprocess.run(
                build_standardize_cmd(src, dst),
                stdout=log_file,
                stderr=log_file,
                check=True
            )
        return True
    except (subprocess.CalledProcessError, OSError) as exc:
        log_message(f"ERROR: Convert failed for {src}: {exc}")
        return False


# --------------------------------------------------------------
def standardize_image(filepath):
    """Convert one image to the standard format in place."""
    path = Path(filepath)
    final_path = str(path.with_suffix('.jpg'))
    temp_path = f"{final_path}.tmp.jpg"

    log_message(
        f"Standardizing {filepath} -> "
        f"{CANVAS_W}x{CANVAS_H} JPEG"
    )

    if not run_standardize(filepath, temp_path):
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None

    os.replace(temp_path, final_path)

    if filepath != final_path and os.path.exists(filepath):
        os.remove(filepath)
        log_message(f"Replaced {filepath} with {final_path}")

    return final_path


# --------------------------------------------------------------
def process_image_file(filepath):
    """Process a single image, returning (path, changed)."""
    if not needs_processing(filepath):
        return filepath, False

    result = standardize_image(filepath)
    if result is None:
        raise RuntimeError(f"could not standardize {filepath}")

    return result, True


# --------------------------------------------------------------
def process_images_in_dir(image_files):
    """Process every image in a list of paths."""
    processed = 0
    errors = 0
    skipped = 0
    changed = 0

    for filepath in image_files:
        try:
            _, was_changed = process_image_file(filepath)
            processed += 1
            if was_changed:
                changed += 1
            else:
                skipped += 1
        except Exception as exc:
            log_message(f"ERROR processing {filepath}: {exc}")
            errors += 1

    return processed, errors, skipped, changed


# --------------------------------------------------------------
def init_conversion_log():
    """Initialize the ImageMagick output log file."""
    with open(CONVERT_LOG, 'w') as handle:
        handle.write(f"Conversion log - {datetime.now()}\n")
        handle.write("=" * 50 + "\n")


# --------------------------------------------------------------
def print_summary(processed, errors, skipped, changed):
    """Print processing summary."""
    log_message("=" * 50)
    log_message("Image cleaning completed")
    log_message(f"Standard: {CANVAS_W}x{CANVAS_H} JPEG, "
                f"{TARGET_DPI} DPI, {MARGIN} px margin")
    log_message(f"Total files processed: {processed}")
    log_message(f"Files skipped (already standard): {skipped}")
    log_message(f"Files changed: {changed}")
    log_message(f"Total errors: {errors}")
    log_message(f"Conversion log: {CONVERT_LOG}")

    if errors > 0:
        log_message(
            f"WARNING: {errors} files had errors. "
            f"Check log for details."
        )


# --------------------------------------------------------------
def cleanup_old_backups(backup_type, max_backups=3):
    """Keep only the most recent backups."""
    backups_dir = Path.home() / "backups"
    if not backups_dir.exists():
        return

    backup_dirs = sorted(
        [d for d in backups_dir.glob(f"*_{backup_type}")
         if d.is_dir()],
        key=lambda x: x.name,
        reverse=True
    )

    removed = 0
    for old_backup in backup_dirs[max_backups:]:
        try:
            shutil.rmtree(old_backup)
            log_message(f"Removed old backup: {old_backup.name}")
            removed += 1
        except OSError as exc:
            log_message(f"Failed to remove {old_backup}: {exc}")

    if removed > 0:
        log_message(f"Cleaned up {removed} old backup(s)")


# --------------------------------------------------------------
def backup_root_path():
    """Build a timestamped backup directory path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(
        str(Path.home()), "backups", f"{timestamp}_images"
    )


# --------------------------------------------------------------
def collect_targets():
    """Return image paths from argv, or the images dir."""
    if len(sys.argv) > 1:
        return [p for p in sys.argv[1:] if os.path.isfile(p)]

    if not os.path.isdir(IMAGES_DIR):
        log_message(f"ERROR: {IMAGES_DIR} not found. "
                    f"Run s1_download_images.py first.")
        sys.exit(1)

    return find_image_files(IMAGES_DIR)


# --------------------------------------------------------------
def main():
    """Standardize every image under the images directory."""
    log_message("Starting image cleaning process")

    if not check_imagemagick():
        sys.exit(1)

    image_files = collect_targets()
    if not image_files:
        log_message("No images to process")
        return

    backup_root = backup_root_path()
    log_message(f"Backup directory: {backup_root}")
    if not create_backup(IMAGES_DIR, backup_root):
        log_message("ERROR: refusing to run without a backup")
        sys.exit(1)

    init_conversion_log()
    print_summary(*process_images_in_dir(image_files))

    log_message("=" * 50)
    log_message("Cleaning up old backups...")
    cleanup_old_backups("images", max_backups=3)


# --------------------------------------------------------------
if __name__ == "__main__":
    main()
