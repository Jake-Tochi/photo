
"""Build photo gallery manifest and optional thumbnails."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Image = None  # type: ignore


@dataclass
class GalleryItem:
    src: str
    w: int
    h: int
    alt: str
    thumb: Optional[str] = None
    thumbWidth: Optional[int] = None
    thumbHeight: Optional[int] = None
    caption: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "src": self.src,
            "w": self.w,
            "h": self.h,
            "alt": self.alt,
        }
        if self.thumb:
            data["thumb"] = self.thumb
        if self.thumbWidth and self.thumbHeight:
            data["thumbWidth"] = self.thumbWidth
            data["thumbHeight"] = self.thumbHeight
        if self.caption:
            data["caption"] = self.caption
        return data


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_source = root
    default_logo = Path('E:/Download/rogo.webp') if os.name == 'nt' else root / 'assets' / 'rogo.webp'

    parser = argparse.ArgumentParser(description='Generate gallery.json and thumbnails for the photo site.')
    parser.add_argument('--source', type=Path, default=default_source, help='Directory to scan for original photos (default: repository root).')
    parser.add_argument('--logo', type=Path, default=default_logo, help='Path to the source logo file to copy into assets/rogo.webp.')
    parser.add_argument('--thumb-size', type=int, default=1200, help='Maximum edge length for generated thumbnails (requires Pillow).')
    parser.add_argument('--skip-copy', action='store_true', help='Skip copying source photos into ./photos (assumes they already exist).')
    parser.add_argument('--skip-thumbs', action='store_true', help='Skip thumbnail generation even if Pillow is available.')
    return parser.parse_args(argv)


def collect_source_images(source: Path, photos_dir: Path) -> Iterable[Path]:
    for path in sorted(source.rglob('*')):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.name.lower() == 'rogo.webp':
            continue
        try:
            path.relative_to(photos_dir)
        except ValueError:
            yield path


def ensure_directories(root: Path) -> Tuple[Path, Path, Path]:
    photos_dir = root / 'photos'
    thumbs_dir = photos_dir / 'thumbs'
    assets_dir = root / 'assets'
    photos_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return photos_dir, thumbs_dir, assets_dir


def copy_logo(logo_path: Path, assets_dir: Path) -> None:
    target = assets_dir / 'rogo.webp'
    if not logo_path.exists():
        print(f"[WARN] Logo not found at {logo_path}. Skipping copy.")
        return
    if target.exists() and target.resolve() == logo_path.resolve():
        return
    shutil.copy2(logo_path, target)
    print(f"[INFO] Copied logo -> {target.relative_to(assets_dir.parent).as_posix()}")


def copy_photos(sources: Iterable[Path], photos_dir: Path) -> None:
    copied = 0
    for path in sources:
        destination = photos_dir / path.name
        if destination.exists():
            src_stat = path.stat()
            dst_stat = destination.stat()
            if dst_stat.st_mtime >= src_stat.st_mtime and dst_stat.st_size == src_stat.st_size:
                continue
        shutil.copy2(path, destination)
        copied += 1
    if copied:
        print(f"[INFO] Copied {copied} photo(s) into {photos_dir.relative_to(photos_dir.parent).as_posix()}")


def describe_alt(path: Path) -> str:
    stem = path.stem.replace('_', ' ').replace('-', ' ')
    return stem


def read_uint16_be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], 'big')



JPEG_SOI = bytes.fromhex('FFD8')
JPEG_START_OF_FRAME_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
}
PNG_SIGNATURE = bytes.fromhex('89504E470D0A1A0A')


def read_image_size(path: Path) -> Tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix in {'.jpg', '.jpeg'}:
        with path.open('rb') as fp:
            if fp.read(2) != JPEG_SOI:
                raise ValueError('Not a JPEG file')
            while True:
                marker_prefix = fp.read(1)
                if not marker_prefix:
                    break
                if marker_prefix[0] != 0xFF:
                    continue
                marker = fp.read(1)
                while marker and marker[0] == 0xFF:
                    marker = fp.read(1)
                if not marker:
                    break
                marker_value = marker[0]
                if marker_value in JPEG_START_OF_FRAME_MARKERS:
                    length_bytes = fp.read(2)
                    if len(length_bytes) != 2:
                        break
                    length = int.from_bytes(length_bytes, 'big')
                    fp.read(1)  # precision
                    height = int.from_bytes(fp.read(2), 'big')
                    width = int.from_bytes(fp.read(2), 'big')
                    return width, height
                length_bytes = fp.read(2)
                if len(length_bytes) != 2:
                    break
                length = int.from_bytes(length_bytes, 'big')
                fp.seek(max(length - 2, 0), os.SEEK_CUR)
        raise ValueError('Could not determine JPEG dimensions')
    if suffix == '.png':
        with path.open('rb') as fp:
            header = fp.read(24)
            if header[:8] != PNG_SIGNATURE:
                raise ValueError('Not a PNG file')
            width = int.from_bytes(header[16:20], 'big')
            height = int.from_bytes(header[20:24], 'big')
            return width, height
    if suffix == '.webp':
        with path.open('rb') as fp:
            header = fp.read(12)
            if header[:4] != b'RIFF' or header[8:12] != b'WEBP':
                raise ValueError('Not a WebP file')
            while True:
                chunk_header = fp.read(8)
                if len(chunk_header) < 8:
                    break
                chunk_type = chunk_header[:4]
                chunk_size = int.from_bytes(chunk_header[4:], 'little')
                chunk_data = fp.read(chunk_size + (chunk_size % 2))
                if chunk_type == b'VP8X' and len(chunk_data) >= 10:
                    width = 1 + int.from_bytes(chunk_data[4:7], 'little')
                    height = 1 + int.from_bytes(chunk_data[7:10], 'little')
                    return width, height
                if chunk_type == b'VP8 ' and len(chunk_data) >= 10:
                    width = chunk_data[6] | (chunk_data[7] << 8)
                    height = chunk_data[8] | (chunk_data[9] << 8)
                    return width, height
                if chunk_type == b'VP8L' and len(chunk_data) >= 5:
                    bits = int.from_bytes(chunk_data[:4], 'little')
                    width = (bits & 0x3FFF) + 1
                    height = ((bits >> 14) & 0x3FFF) + 1
                    return width, height
        raise ValueError('Could not determine WebP dimensions')
    raise ValueError(f'Unsupported format: {suffix}')




def get_image_dimensions(path: Path) -> Tuple[int, int]:
    if Image is not None:
        try:
            with Image.open(path) as img:  # type: ignore[assignment]
                return img.width, img.height
        except Exception as exc:
            print(f"[WARN] Pillow failed to read {path}: {exc}. Falling back to manual parser.")
    return read_image_size(path)


def generate_thumbnail(source: Path, destination: Path, max_edge: int) -> Optional[Tuple[int, int]]:
    if Image is None:
        return None
    try:
        with Image.open(source) as img:  # type: ignore[assignment]
            image = img.convert('RGB') if img.mode in {'P', 'RGBA'} else img
            image.thumbnail((max_edge, max_edge), Image.LANCZOS)  # type: ignore[arg-type]
            destination.parent.mkdir(parents=True, exist_ok=True)
            image.save(destination, format=img.format or 'JPEG', optimize=True, quality=90)
            return image.width, image.height
    except Exception as exc:
        print(f"[WARN] Failed to create thumbnail for {source.name}: {exc}")
        return None


def build_gallery_items(photos_dir: Path, thumbs_dir: Path, max_edge: int, skip_thumbs: bool) -> Sequence[GalleryItem]:
    items: list[GalleryItem] = []
    for photo in sorted(photos_dir.iterdir()):
        if photo.parent == thumbs_dir:
            continue
        if not photo.is_file():
            continue
        if photo.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        width, height = get_image_dimensions(photo)
        alt_text = describe_alt(photo)
        caption = alt_text
        thumb_rel = None
        thumb_width = None
        thumb_height = None
        thumb_path = thumbs_dir / photo.name
        if Image is not None and not skip_thumbs:
            thumb_dims = generate_thumbnail(photo, thumb_path, max_edge)
            if thumb_dims:
                thumb_width, thumb_height = thumb_dims
                thumb_rel = thumb_path.relative_to(photos_dir.parent).as_posix()
        if thumb_rel is None and thumb_path.exists():
            thumb_rel = thumb_path.relative_to(photos_dir.parent).as_posix()
            try:
                thumb_width, thumb_height = get_image_dimensions(thumb_path)
            except Exception:
                thumb_width = thumb_height = None
        item = GalleryItem(
            src=photo.relative_to(photos_dir.parent).as_posix(),
            w=width,
            h=height,
            alt=alt_text,
            thumb=thumb_rel,
            thumbWidth=thumb_width,
            thumbHeight=thumb_height,
            caption=caption,
        )
        items.append(item)
    return items


def write_gallery_json(items: Sequence[GalleryItem], photos_dir: Path) -> str:
    output_path = photos_dir / 'gallery.json'
    data = [item.to_dict() for item in items]
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    output_path.write_text(json_text + '\n', encoding='utf-8')
    print(f"[INFO] Wrote metadata for {len(items)} photo(s) -> {output_path.relative_to(photos_dir.parent).as_posix()}")
    return json_text


def render_gallery_markup_lines(items: Sequence[GalleryItem]) -> list[str]:
    if not items:
        return ['        <p class="gallery-empty">表示できる写真がありません。</p>']
    lines: list[str] = []
    for index, item in enumerate(items):
        caption = item.caption or item.alt or Path(item.src).stem
        alt_text = item.alt or caption
        thumb_src = item.thumb or item.src
        width = item.thumbWidth or item.w
        height = item.thumbHeight or item.h
        img_attrs = [
            'class="gallery-item__image"',
            f'src="{escape(thumb_src)}"',
            f'alt="{escape(alt_text)}"',
            'loading="lazy"',
            'decoding="async"',
        ]
        if width:
            img_attrs.append(f'width="{width}"')
        if height:
            img_attrs.append(f'height="{height}"')
        label_text = escape(f'{caption}を拡大表示')
        lines.extend([
            '        <figure class="gallery-item" role="listitem">',
            f'          <button class="gallery-item__button" type="button" data-gallery-index="{index}" aria-label="{label_text}">',
            f'            <img {" ".join(img_attrs)} />',
            f'            <figcaption class="gallery-item__caption">{escape(caption)}</figcaption>',
            '          </button>',
            '        </figure>',
        ])
    return lines


def render_gallery_data_lines(json_text: str) -> list[str]:
    json_lines = json_text.splitlines() or ['[]']
    indented: list[str] = []
    for line in json_lines:
        if line:
            indented.append('      ' + line)
        else:
            indented.append('')
    return [
        '    <script id="gallery-data" type="application/json">',
        *indented,
        '    </script>',
    ]


def update_index_html(root: Path, items: Sequence[GalleryItem], json_text: str) -> None:
    index_path = root / 'index.html'
    if not index_path.exists():
        print('[WARN] index.html not found; skipping inline gallery update.')
        return
    lines = index_path.read_text(encoding='utf-8').splitlines()

    def locate(marker: str) -> int:
        for idx, line in enumerate(lines):
            if marker in line:
                return idx
        raise ValueError(marker)

    try:
        gallery_start = locate('<!-- gallery:start -->')
        gallery_end = locate('<!-- gallery:end -->')
        gallery_lines = render_gallery_markup_lines(items)
        lines[gallery_start + 1:gallery_end] = gallery_lines
    except ValueError:
        print('[WARN] Gallery markers not found; skipped inline gallery markup update.')

    try:
        data_start = locate('<!-- gallery-data:start -->')
        data_end = locate('<!-- gallery-data:end -->')
        data_lines = render_gallery_data_lines(json_text)
        lines[data_start + 1:data_end] = data_lines
    except ValueError:
        print('[WARN] Gallery data markers not found; skipped inline JSON update.')

    index_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('[INFO] Updated index.html with inline gallery content.')


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = Path(__file__).resolve().parents[1]
    photos_dir, thumbs_dir, assets_dir = ensure_directories(root)
    args = parse_args(argv)

    if not args.skip_copy:
        sources = list(collect_source_images(args.source, photos_dir))
        copy_photos(sources, photos_dir)
    copy_logo(args.logo, assets_dir)

    items = build_gallery_items(photos_dir, thumbs_dir, args.thumb_size, args.skip_thumbs)
    if not items:
        print('[WARN] No photos were found in ./photos to catalogue.')
    json_text = write_gallery_json(items, photos_dir)
    update_index_html(root, items, json_text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
