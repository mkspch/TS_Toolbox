import os
import subprocess
import sys
from PIL import Image

# This allows the script to find the 'utils' module.
sys.path.append(os.path.dirname(__file__))
import utils

# --- Configuration ---
# Path to the OCIO configuration file for color space transformations.
OCIO_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'aces_1.2', 'config.ocio')

def get_oiiotool_path():
    """Check common paths for oiiotool executable."""
    # You might need to adjust this to your system's OpenImageIO installation path
    possible_paths = [
        "C:/Program Files/OpenImageIO/bin/oiiotool.exe",
        "/usr/bin/oiiotool",
        "/usr/local/bin/oiiotool"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return "oiiotool" # Fallback to assuming it's in the system PATH

def convert_exr_to_srgb_mp4(image_path, framerate=25):
    """
    Converts a sequence of EXR files (assumed to be ACEScg) to an sRGB MP4 video.
    """
    print("Starting EXR to sRGB MP4 conversion...")
    sequence_files, start_frame, pattern = utils.find_sequence_files(image_path)

    if not sequence_files:
        print(f"Error: No image sequence found for '{image_path}'.")
        return False

    output_dir = os.path.join(os.path.dirname(image_path), "sRGB_conv")
    os.makedirs(output_dir, exist_ok=True)
    
    temp_pattern = os.path.join(output_dir, f"frame.%0{len(str(start_frame))}d.png")
    
    oiiotool_path = get_oiiotool_path()

    # OIIOtool command to convert ACEScg EXR to sRGB PNG
    oiiotool_cmd = [
        oiiotool_path,
        pattern,
        "--colorconfig", OCIO_CONFIG_PATH,
        "--colorconvert", "ACES - ACEScg", "Output - sRGB",
        "-o", temp_pattern
    ]

    print(f"Running OIIOtool command: {' '.join(oiiotool_cmd)}")
    try:
        subprocess.run(oiiotool_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during OIIOtool conversion: {e}")
        print(f"Stderr: {e.stderr}")
        return False

    # FFmpeg command to create MP4 from PNG sequence
    output_video_path = os.path.splitext(pattern)[0] + "_sRGB.mp4"
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',
        '-framerate', str(framerate),
        '-start_number', str(start_frame),
        '-i', temp_pattern,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        output_video_path
    ]
    
    print(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Successfully created video: {output_video_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during FFmpeg conversion: {e}")
        print(f"Stderr: {e.stderr}")
        return False
    finally:
        # Clean up temporary PNG files
        for f in os.listdir(output_dir):
            if f.startswith("frame.") and f.endswith(".png"):
                os.remove(os.path.join(output_dir, f))
        os.rmdir(output_dir)

    print(f"Output video created at: {output_video_path}")
    return True


def convert_sequence_to_mp4(image_path, framerate=25):
    """
    Converts a generic image sequence (e.g., PNG, JPG) to an MP4 video.
    """
    print("Starting image sequence to MP4 conversion...")
    sequence_files, start_frame, pattern = utils.find_sequence_files(image_path)
    
    if not sequence_files:
        print(f"Error: No image sequence found for '{image_path}'.")
        return False

    output_path = os.path.splitext(pattern.replace(f'%0{len(str(start_frame))}d', ''))[0] + ".mp4"

    ffmpeg_cmd = [
        'ffmpeg',
        '-y', # Overwrite output file if it exists
        '-framerate', str(framerate),
        '-start_number', str(start_frame),
        '-i', pattern,
        '-c:v', 'libx264',   # Use H.264 codec
        '-pix_fmt', 'yuv420p', # Pixel format for wide compatibility
        '-crf', '18',        # Constant Rate Factor (quality, lower is better)
        output_path
    ]

    print(f"Running command: {' '.join(ffmpeg_cmd)}")
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Successfully created video: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        return False

def convert_mp4_to_png_sequence(video_path):
    """
    Converts an MP4 video to a sequence of PNG images.
    """
    print(f"Starting MP4 to PNG conversion for '{os.path.basename(video_path)}'...")
    output_folder_name = os.path.splitext(os.path.basename(video_path))[0] + "_png_sequence"
    output_dir = os.path.join(os.path.dirname(video_path), output_folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    output_pattern = os.path.join(output_dir, "frame.%04d.png")

    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_path,
        output_pattern
    ]

    print(f"Running command: {' '.join(ffmpeg_cmd)}")
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Successfully exported PNG sequence to: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        return False

def convert_mp4_to_jpg_sequence(video_path, quality=90):
    """
    Converts an MP4 video to a sequence of JPG images.
    """
    print(f"Starting MP4 to JPG conversion for '{os.path.basename(video_path)}'...")
    output_folder_name = os.path.splitext(os.path.basename(video_path))[0] + "_jpg_sequence"
    output_dir = os.path.join(os.path.dirname(video_path), output_folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    output_pattern = os.path.join(output_dir, "frame.%04d.jpg")
    
    # JPEG quality in ffmpeg is -q:v, from 2 (best) to 31 (worst). Let's map 1-100 to that.
    # Simple linear mapping: 100 -> 2, 1 -> 31
    q_scale = int(2 + (100 - quality) * (29 / 99.0))

    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-q:v', str(q_scale),
        output_pattern
    ]

    print(f"Running command: {' '.join(ffmpeg_cmd)}")
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Successfully exported JPG sequence to: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        return False

def convert_img_half_size(image_path):
    """
    Scales down the selected image file to half its size, maintaining aspect ratio.

    Args:
        image_path (str): The full path to the input image file.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return False

    try:
        img = Image.open(image_path)
        original_width, original_height = img.size
        
        new_width = original_width // 2
        new_height = original_height // 2

        if new_width < 1: new_width = 1
        if new_height < 1: new_height = 1

        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_half{ext}"
        
        resized_img.save(output_path)
        print(f"Successfully scaled '{os.path.basename(image_path)}' to half size: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"Error converting image '{os.path.basename(image_path)}': {e}")
        return False

def convert_img_resize(image_path, new_width):
    """
    Resizes an image to a new width, maintaining aspect ratio.

    Args:
        image_path (str): The full path to the input image file.
        new_width (int): The desired new width for the image.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return False
    if new_width <= 0:
        print(f"Error: new_width must be a positive integer, got {new_width}")
        return False

    try:
        img = Image.open(image_path)
        original_width, original_height = img.size
        
        # Calculate new height maintaining aspect ratio
        aspect_ratio = original_width / original_height
        new_height = int(new_width / aspect_ratio)

        # Ensure minimum dimensions to avoid errors with very small images
        if new_height < 1: new_height = 1

        resized_img = img.resize((new_width, new_height), Image.LANCZOS) # LANCZOS is a high-quality downsampling filter

        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_resized_{new_width}px{ext}"
        
        resized_img.save(output_path)
        print(f"Successfully resized '{os.path.basename(image_path)}' to {new_width}px width: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"Error resizing image '{os.path.basename(image_path)}': {e}")
        return False

def create_contact_sheet(image_paths, output_filename="contact_sheet.jpg", columns=2, padding=10):
    """
    Creates a contact sheet from multiple images, arranged in columns.
    Images are scaled to match the height of the tallest image.
    Empty spaces are filled with black.

    Args:
        image_paths (list): A list of full paths to the input image files.
        output_filename (str): The desired filename for the output contact sheet.
        columns (int): The number of columns for the contact sheet.
        padding (int): Padding between images and around the border.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not image_paths:
        print("Error: No image paths provided for contact sheet.")
        return False

    images = []
    max_height = 0
    total_width_per_row = 0
    
    try:
        # Load images and find max height, and sum up widths for scaling reference
        for path in image_paths:
            if not os.path.exists(path):
                print(f"Warning: Image not found and skipped: {path}")
                continue
            img = Image.open(path)
            images.append(img)
            if img.height > max_height:
                max_height = img.height
            total_width_per_row += img.width

        if not images:
            print("Error: No valid images found to create contact sheet.")
            return False

        # Calculate average aspect ratio if needed, or target width per column
        # For simplicity, we'll make each column's images max_height tall.
        # Max width needed for a column will be max(img.width for img in images resized to max_height)
        
        resized_images = []
        max_resized_width = 0
        for img in images:
            if img.height != max_height:
                # Resize image maintaining aspect ratio
                aspect_ratio = img.width / img.height
                new_width = int(max_height * aspect_ratio)
                resized_img = img.resize((new_width, max_height), Image.LANCZOS)
            else:
                resized_img = img
            resized_images.append(resized_img)
            if resized_img.width > max_resized_width:
                max_resized_width = resized_img.width

        # Now, calculate the canvas size
        num_images = len(resized_images)
        rows = (num_images + columns - 1) // columns
        
        canvas_width = (max_resized_width * columns) + (padding * (columns + 1))
        canvas_height = (max_height * rows) + (padding * (rows + 1))

        contact_sheet = Image.new('RGB', (canvas_width, canvas_height), color = (0, 0, 0)) # Black background

        x_offset = padding
        y_offset = padding
        
        for i, img in enumerate(resized_images):
            # Calculate position for current image
            col = i % columns
            row = i // columns

            x_pos = (col * (max_resized_width + padding)) + padding
            y_pos = (row * (max_height + padding)) + padding

            # Center image vertically within its slot if it's smaller
            paste_x = x_pos
            paste_y = y_pos + (max_height - img.height) // 2

            contact_sheet.paste(img, (paste_x, paste_y))
            
        output_path = os.path.join(os.path.dirname(image_paths[0]), output_filename)
        contact_sheet.save(output_path)
        print(f"Successfully created contact sheet: {output_path}")
        return True

    except Exception as e:
        print(f"Error creating contact sheet: {e}")
        return False