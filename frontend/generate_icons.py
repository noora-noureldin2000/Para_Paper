import os
import sys

def generate_icons():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[WARNING] Pillow is not installed. Installing Pillow now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageDraw, ImageFont

    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    sizes = [16, 32, 80]
    for size in sizes:
        # Create a purple gradient image
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw a rounded purple rectangle
        padding = max(1, int(size * 0.05))
        draw.rounded_rectangle(
            [padding, padding, size - padding, size - padding],
            radius=max(2, int(size * 0.2)),
            fill=(109, 40, 217, 255),  # Violet 700
            outline=(139, 92, 246, 255),  # Violet 500
            width=max(1, int(size * 0.05))
        )

        # Draw the letter "A" in the center in white
        # Choose a size proportional to the image
        font_size = int(size * 0.6)
        try:
            # Try to load a default font
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Draw simple text overlay
        # For simplicity in simple icon, draw lines representing an 'A' or use text
        # If default font is used, draw it. Otherwise draw lines.
        text = "A"
        
        # Draw text at the center
        # Since default font might not scale, we can draw lines representing a clean geometric 'A'
        # which looks even more professional!
        cx = size / 2
        cy = size / 2
        r = size * 0.25
        
        # Coordinates for geometric 'A'
        # Peak: (cx, cy - r)
        # Bottom Left: (cx - r, cy + r)
        # Bottom Right: (cx + r, cy + r)
        # Crossbar: (cx - r*0.5, cy + r*0.2) to (cx + r*0.5, cy + r*0.2)
        line_width = max(1, int(size * 0.08))
        draw.line([(cx, cy - r), (cx - r, cy + r)], fill=(255, 255, 255, 255), width=line_width)
        draw.line([(cx, cy - r), (cx + r, cy + r)], fill=(255, 255, 255, 255), width=line_width)
        draw.line([(cx - r * 0.5, cy + r * 0.2), (cx + r * 0.5, cy + r * 0.2)], fill=(255, 255, 255, 255), width=line_width)

        icon_path = os.path.join(assets_dir, f"icon-{size}.png")
        image.save(icon_path, "PNG")
        print(f"Generated icon: {icon_path}")

if __name__ == "__main__":
    generate_icons()
