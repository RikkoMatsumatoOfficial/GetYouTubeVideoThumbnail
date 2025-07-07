import dearpygui.dearpygui as dpg
import webbrowser
import re
import requests
from io import BytesIO
from PIL import Image
import numpy as np

# Initialize Dear PyGui
dpg.create_context()

# Validate YouTube URL
def is_valid_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

# Extract video ID from URL
def extract_video_id(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    match = re.match(youtube_regex, url)
    return match.group(6) if match else None

# Generate thumbnail URL with fallback
def get_thumbnail_url(video_id):
    qualities = ["maxresdefault", "hqdefault", "mqdefault", "sddefault", "default"]
    for quality in qualities:
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                return url
        except:
            continue
    return f"https://img.youtube.com/vi/{video_id}/default.jpg"

# Callback for the fetch button
def fetch_thumbnail_callback(sender, app_data):
    url = dpg.get_value("url_input")
    if not url:
        dpg.set_value("status", "Please enter a YouTube URL")
        return
    
    if not is_valid_youtube_url(url):
        dpg.set_value("status", "Invalid YouTube URL")
        return
    
    try:
        video_id = extract_video_id(url)
        if not video_id:
            dpg.set_value("status", "Could not extract video ID")
            return
        
        thumbnail_url = get_thumbnail_url(video_id)
        dpg.set_value("status", f"Found thumbnail: {thumbnail_url}")
        dpg.set_value("thumbnail_url", thumbnail_url)
        
        dpg.configure_item("show_thumbnail", enabled=True)
        dpg.configure_item("open_in_browser", enabled=True)
        
    except Exception as e:
        dpg.set_value("status", f"Error fetching thumbnail: {str(e)}")

# Global texture registry management
texture_registry_created = False

# Callback to show thumbnail in the app
def show_thumbnail_callback(sender, app_data):
    global texture_registry_created
    
    thumbnail_url = dpg.get_value("thumbnail_url")
    
    # Clear previous items
    if dpg.does_item_exist("thumbnail_texture"):
        dpg.delete_item("thumbnail_texture")
    if dpg.does_item_exist("thumbnail_image"):
        dpg.delete_item("thumbnail_image")
    
    try:
        # Fetch the image
        response = requests.get(thumbnail_url, timeout=10)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB format
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert image to numpy array and normalize
        img_array = np.array(img, dtype=np.float32) / 255.0
        img_data = img_array.ravel()
        
        width, height = img.size
        
        # Create texture registry once
        if not texture_registry_created:
            dpg.add_texture_registry(tag="texture_registry")
            texture_registry_created = True
        
        # Add texture to registry
        dpg.add_raw_texture(
            width=width,
            height=height,
            default_value=img_data,
            format=dpg.mvFormat_Float_rgb,
            parent="texture_registry",
            tag="thumbnail_texture"
        )
        
        # Add image to display
        dpg.add_image(
            "thumbnail_texture",
            parent="thumbnail_group",
            tag="thumbnail_image"
        )
        
        dpg.set_value("status", f"Successfully displayed thumbnail ({width}x{height})")
        
    except requests.exceptions.RequestException as e:
        dpg.set_value("status", f"Network error: {str(e)}")
    except Exception as e:
        dpg.set_value("status", f"Image processing error: {str(e)}")

# Callback to open thumbnail in browser
def open_in_browser_callback(sender, app_data):
    thumbnail_url = dpg.get_value("thumbnail_url")
    webbrowser.open(thumbnail_url)

# Create the UI
with dpg.window(tag="main_window", label="YouTube Thumbnail Fetcher", width=800, height=600):
    dpg.add_text("YouTube Video Thumbnail Fetcher")
    dpg.add_spacer(height=10)
    
    with dpg.group(horizontal=True):
        dpg.add_input_text(tag="url_input", hint="Enter YouTube URL...", width=400)
        dpg.add_button(label="Fetch Thumbnail", callback=fetch_thumbnail_callback)
    
    dpg.add_spacer(height=10)
    dpg.add_text(tag="status", default_value="Enter a YouTube URL and click Fetch Thumbnail")
    dpg.add_text(tag="thumbnail_url", show=False)
    
    dpg.add_spacer(height=20)
    with dpg.group(horizontal=True, tag="button_group"):
        dpg.add_button(label="Show Thumbnail", tag="show_thumbnail", callback=show_thumbnail_callback, enabled=False)
        dpg.add_button(label="Open in Browser", tag="open_in_browser", callback=open_in_browser_callback, enabled=False)
    
    dpg.add_spacer(height=20)
    with dpg.group(tag="thumbnail_group"):
        pass  # Thumbnail will be displayed here

# Set primary window and start
dpg.create_viewport(title='YouTube Thumbnail Fetcher', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("main_window", True)
dpg.start_dearpygui()
dpg.destroy_context()