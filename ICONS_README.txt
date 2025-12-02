To create the extension icons, you have two options:

## Option 1: Quick (use any 16x16, 48x48, 128x128 PNG)
Just name them icon16.png, icon48.png, icon128.png

## Option 2: Generate from emoji
Run this Python script once:

```python
from PIL import Image, ImageDraw, ImageFont
import os

sizes = [16, 48, 128]
for size in sizes:
    img = Image.new('RGB', (size, size), '#2563eb')
    img.save(f'icon{size}.png')
    print(f'Created icon{size}.png')
```

Requires: pip install Pillow

## Option 3: Use these data URLs
Open each in browser, right-click save:

16x16 (blue square):
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAH0lEQVQ4T2NkYGD4z0AEYBxVMKpgVMGoAkrDgJGBBgDqRAIRKqpWXgAAAABJRU5ErkJggg==

Or just delete the icon references from manifest.json - extension works without custom icons.
