import os
import io
import sys
import threading
import textwrap
import logging
import requests
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

# API Endpoints
# UNSPLASH_API_URL and ACCESS_KEY removed as we use public random sources now
QUOTE_API_URL = "https://dummyjson.com/quotes/random"  # More reliable alternative

# App Settings
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
UPDATE_INTERVAL_MS = 10000  # 10 seconds
SEARCH_KEYWORD = "nature"

# -----------------------------------------------------------------------------
# LOGGING SETUP
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inspiration Station")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        
        # Center the window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_c = int((screen_width/2) - (WINDOW_WIDTH/2))
        y_c = int((screen_height/2) - (WINDOW_HEIGHT/2))
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_c}+{y_c}")

        # UI Elements
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.current_image = None  # Prevent garbage collection of ImageTk
        self.running = True
        
        # Initial Load
        self.load_content()
        
        # Schedule first automatic update after interval
        self.schedule_next_update()

    def schedule_next_update(self):
        if self.running:
            self.root.after(UPDATE_INTERVAL_MS, self.trigger_update)

    def trigger_update(self):
        """Called by the scheduler to start a new fetch cycle in a thread."""
        threading.Thread(target=self.load_content, daemon=True).start()
        self.schedule_next_update()

    def load_content(self):
        """Fetches data and updates UI. Runs in a separate thread (mostly)."""
        try:
            # 1. Fetch Quote
            quote_text, quote_author = self.fetch_quote()
            
            # 2. Fetch Image
            image_data = self.fetch_image(SEARCH_KEYWORD)
            
            # 3. Process Image (Resize, Dim, Add Text)
            if image_data:
                final_image = self.process_image(image_data, quote_text, quote_author)
                
                # 4. Update UI on Main Thread
                self.root.after(0, self.update_ui, final_image)
            else:
                logging.error("Failed to fetch image data.")

        except Exception as e:
            logging.error(f"Error in load_content: {e}")

    def fetch_quote(self):
        """Fetches a random quote from the API."""
        try:
            response = requests.get(QUOTE_API_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Handle DummyJSON format: {"id": 1, "quote": "...", "author": "..."}
                # Also handle potential list if other API returns list
                if isinstance(data, list):
                    data = data[0]
                    
                content = data.get("quote", data.get("content", "Inspiration allows us to do great things."))
                author = data.get("author", "Unknown")
                return content, author
            else:
                logging.warning(f"Quote API Error: {response.status_code}")
                return "The beauty of the world lies in the details.", "Default"
        except Exception as e:
            logging.error(f"Quote Fetch Exception: {e}")
            return "Stay focused and never give up.", "Offline Mode"

    def fetch_image(self, keyword):
        """Fetches a random nature image from public APIs without needing an API key."""
        try:
            # Try LoremFlickr first as it supports keywords (nature)
            # Add a random parameter to prevent caching
            import random
            rand_id = random.randint(1, 10000)
            
            # Use 'nature' keyword
            img_url = f"https://loremflickr.com/{WINDOW_WIDTH}/{WINDOW_HEIGHT}/{keyword}?lock={rand_id}"
            logging.info(f"Fetching image from: {img_url}")
            
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                return response.content
            
            # Fallback to Picsum (High quality, but no keyword guarantee)
            logging.info("LoremFlickr failed, falling back to Picsum.")
            picsum_url = f"https://picsum.photos/{WINDOW_WIDTH}/{WINDOW_HEIGHT}?blur=1&random={rand_id}"
            response = requests.get(picsum_url, timeout=10)
            if response.status_code == 200:
                return response.content
                
        except Exception as e:
            logging.error(f"Image Fetch Exception: {e}")
            
        return None

    def process_image(self, image_data, text, author):
        """
        Resizes the image, adds a dark overlay, and draws the text using Pillow.
        Returns a Tkinter-compatible PhotoImage.
        """
        try:
            # Load image from bytes
            img = Image.open(io.BytesIO(image_data))
            
            # Resize / Crop to fit window exactly
            img_ratio = img.width / img.height
            window_ratio = WINDOW_WIDTH / WINDOW_HEIGHT
            
            if img_ratio > window_ratio:
                # Image is wider than window, crop width
                new_height = WINDOW_HEIGHT
                new_width = int(new_height * img_ratio)
            else:
                # Image is taller than window, crop height
                new_width = WINDOW_WIDTH
                new_height = int(new_width / img_ratio)
                
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            left = (new_width - WINDOW_WIDTH) / 2
            top = (new_height - WINDOW_HEIGHT) / 2
            right = (new_width + WINDOW_WIDTH) / 2
            bottom = (new_height + WINDOW_HEIGHT) / 2
            img = img.crop((left, top, right, bottom))
            
            # Add Dark Overlay for readability
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 100)) # Semi-transparent black
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            
            # Draw Text
            draw = ImageDraw.Draw(img)
            
            # Load Font with fallback mechanism
            font_large = None
            font_small = None
            
            # List of fonts to try in order
            font_candidates = [
                 # macOS
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/System/Library/Fonts/SFNS.ttf", # San Francisco on some versions
                "/Library/Fonts/Arial.ttf",
                # Windows
                "arial.ttf", 
                "segoeui.ttf",
                "calibri.ttf",
                # Linux
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]
            
            for font_path in font_candidates:
                try:
                    font_large = ImageFont.truetype(font_path, 36)
                    font_small = ImageFont.truetype(font_path, 24)
                    break # Success
                except (IOError, OSError):
                    continue
            
            # Absolute fallback if no system fonts found
            if font_large is None:
                logging.warning("No system fonts found, using default PIL font.")
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Text Wrapping Logic
            # Calculate char width approx to determine wrap width
            # A rough estimate for 36pt font is ~20px per char depending on font
            # Window 900px -> ~40 chars max line length
            
            avg_char_width = 18 
            max_chars = int((WINDOW_WIDTH - 100) / avg_char_width)
            
            wrapper = textwrap.TextWrapper(width=max_chars) 
            text_lines = wrapper.wrap(text)
            
            # --- Draw Text Logic ---
            # Calculate total height first to center vertically
            total_height = 0
            line_heights = []
            
            # Helper to get size
            def get_text_size(txt, font):
                if hasattr(draw, 'textbbox'):
                    bbox = draw.textbbox((0, 0), txt, font=font)
                    return bbox[2] - bbox[0], bbox[3] - bbox[1]
                else:
                    return draw.textsize(txt, font=font)

            for line in text_lines:
                w, h = get_text_size(line, font_large)
                line_heights.append(h + 10) # +10 padding
                total_height += h + 10
            
            # Author size
            aw, ah = get_text_size(author, font_small)
            total_height += ah + 30 # +30 padding before author
            
            current_y = (WINDOW_HEIGHT - total_height) / 2
            
            # Draw Quote
            for i, line in enumerate(text_lines):
                w, h = get_text_size(line, font_large)
                x_pos = (WINDOW_WIDTH - w) / 2
                
                # Shadow
                draw.text((x_pos+2, current_y+2), line, font=font_large, fill=(0,0,0,160))
                # Text
                draw.text((x_pos, current_y), line, font=font_large, fill=(255,255,255,255))
                
                current_y += line_heights[i]
            
            # Draw Author
            current_y += 20
            auth_str = f"- {author}"
            aw, ah = get_text_size(auth_str, font_small)
            ax_pos = (WINDOW_WIDTH - aw) / 2
            
            draw.text((ax_pos+1, current_y+1), auth_str, font=font_small, fill=(0,0,0,160))
            draw.text((ax_pos, current_y), auth_str, font=font_small, fill=(220,220,220,255))

            return ImageTk.PhotoImage(img)

        except Exception as e:
            logging.error(f"Image Processing Exception: {e}")
            return None

    def update_ui(self, photo_image):
        """Updates the canvas with the new image."""
        if photo_image:
            self.current_image = photo_image
            self.canvas.create_image(0, 0, anchor="nw", image=self.current_image)
            # Optional: fade-in handling would go here with alpha manipulation loop, 
            # but Tkinter doesn't support alpha on Canvas images smoothly without high CPU usage.

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DesktopApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit()
