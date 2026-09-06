"""Shared local video typography and colors; no simulation state mutation."""
from functools import lru_cache
from pathlib import Path
from PIL import ImageFont

PAPER='#f7f4eb'
INK='#243a32'
MUTED='#748177'

@lru_cache(maxsize=32)
def font(size,bold=False):
    candidates=['/System/Library/Fonts/Avenir Next.ttc',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:/Windows/Fonts/arial.ttf']
    for path in candidates:
        if Path(path).is_file():
            index=(0 if bold else 7) if 'Avenir' in path else 0
            return ImageFont.truetype(path,size,index=index)
    return ImageFont.load_default(size=size)
