import os
import subprocess
import tempfile
import shutil
import numpy as np
import utils
from PIL import Image

try:
    import PyOpenColorIO as OCIO
    import OpenImageIO as OIIO
except ImportError:
    print("FATAL ERROR: PyOpenColorIO or OpenImageIO not found.")
    print("Please ensure these libraries are installed in the portable python environment.")
    OCIO = None
    OIIO = None

FFMPEG_EXE = r"C:\Users\nhb\AppData\Local\Programs\TS_Toolbox\ffmpeg\bin\ffmpeg.exe"

def convert_mp4_to_png_sequence(video_path):
    print(f"DEBUG: FFMPEG_EXE resolved to: {FFMPEG_EXE}")
    if not os.path.exists(FFMPEG_EXE):
        print(f"ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed and accessible at this path.")
        return False
    print(f"Using FFmpeg executable: {FFMPEG_EXE}")

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False

    video_dir = os.path.dirname(video_path)
    video_filename = os.path.basename(video_path)
    base_name, _ = os.path.splitext(video_filename)

    output_dir = os.path.join(video_dir, base_name)
    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, f"{base_name}_%04d.png")

    print(f"Starting conversion of {video_filename} to PNG sequence...")
    command = [
        FFMPEG_EXE,
        '-i', video_path,
        output_pattern
    ]

    print(f"FFmpeg Command: {' '.join(command)}")
    
    try:
        subprocess.run(command, executable=FFMPEG_EXE, check=True, capture_output=False, text=True) 
        print(f"Successfully converted video to PNG sequence in {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(command)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False


def convert_mp4_to_jpg_sequence(video_path, quality=90):
    print(f"DEBUG: FFMPEG_EXE resolved to: {FFMPEG_EXE}")
    if not os.path.exists(FFMPEG_EXE):
        print(f"ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed and accessible at this path.")
        return False
    print(f"Using FFmpeg executable: {FFMPEG_EXE}")

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False

    video_dir = os.path.dirname(video_path)
    video_filename = os.path.basename(video_path)
    base_name, _ = os.path.splitext(video_filename)

    output_dir = os.path.join(video_dir, base_name)
    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, f"{base_name}_%04d.jpg")

    print(f"Starting conversion of {video_filename} to JPG sequence...")
    ffmpeg_q_value = 2 + (100 - quality) * 29 // 99
    ffmpeg_q_value = max(2, min(31, ffmpeg_q_value))
    print(f"DEBUG: Using FFmpeg -q:v quality: {ffmpeg_q_value} (from input quality {quality})")

    command = [
        FFMPEG_EXE,
        '-i', video_path,
        '-q:v', str(ffmpeg_q_value),
        output_pattern
    ]

    print(f"FFmpeg Command: {' '.join(command)}")
    
    try:
        subprocess.run(command, executable=FFMPEG_EXE, check=True, capture_output=False, text=True) 
        print(f"Successfully converted video to JPG sequence in {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(command)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False


def convert_sequence_to_mp4(first_file_path, framerate=25, output_path=None):
    print(f"DEBUG: FFMPEG_EXE resolved to: {FFMPEG_EXE}")
    if not os.path.exists(FFMPEG_EXE):
        print(f"ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed and accessible at this path.")
        return False
    print(f"Using FFmpeg executable: {FFMPEG_EXE}")
    files, start_frame, sequence_pattern = utils.find_sequence_files(first_file_path)

    if not files:
        print("Error: Could not find sequence.")
        return False

    if not output_path:
        output_dir = os.path.dirname(first_file_path)
        base_name = os.path.basename(sequence_pattern).split('%')[0].rstrip('._-')
        if not base_name:
            base_name = "output"
        output_path = os.path.join(output_dir, f"{base_name}.mp4")

    print(f"Starting conversion of sequence {os.path.basename(sequence_pattern)} to MP4...")

    command = [
        FFMPEG_EXE,
        '-framerate', str(framerate),
        '-start_number', str(start_frame),
        '-i', sequence_pattern,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-y',
        output_path
    ]

    print(f"FFmpeg Command: {' '.join(command)}")
    try:
        subprocess.run(command, executable=FFMPEG_EXE, check=True, capture_output=True, text=True)
        print(f"Successfully created video: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(command)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False

def convert_exr_to_srgb_mp4(first_file_path, framerate=25):
    if not OCIO or not OIIO:
        return False

    exr_files, start_frame, sequence_pattern = utils.find_sequence_files(first_file_path)

    if not exr_files:
        print("Error: Could not find EXR sequence.")
        return False
        
    output_dir = os.path.dirname(first_file_path)
    base_name = os.path.basename(sequence_pattern).split('%')[0].rstrip('._-')
    final_output_path = os.path.join(output_dir, f"{base_name}_sRGB.mp4")

    ocio_config_path = os.path.join(os.path.dirname(__file__), 'config', 'aces_1.2', 'config.ocio')
    if not os.path.exists(ocio_config_path):
        print(f"CRITICAL ERROR: OCIO config not found at {ocio_config_path}")
        return False

    try:
        config = OCIO.Config.CreateFromFile(ocio_config_path)
        processor = config.getProcessor("ACEScg", "Output - sRGB")
    except Exception as e:
        print(f"OCIO Error: Could not set up color processor. {e}")
        return False

    first_img_buf = OIIO.ImageBuf(exr_files[0])
    output_width = first_img_buf.spec().width
    output_height = first_img_buf.spec().height

    ffmpeg_pixel_format = "rgb48le"

    ffmpeg_cmd = [
        FFMPEG_EXE,
        "-hide_banner", "-loglevel", "info", "-y",
        "-f", "rawvideo",
        "-pixel_format", ffmpeg_pixel_format,
        "-video_size", f"{output_width}x{output_height}",
        "-framerate", str(framerate),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        final_output_path
    ]

    print(f"DEBUG: FFmpeg command: {' '.join(ffmpeg_cmd)}")

    try:
        ffproc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, executable=FFMPEG_EXE)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed.")
        return False
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start FFmpeg subprocess: {e}")
        return False

    print("Starting color conversion and piping to FFmpeg...")
    try:
        for i, exr_path in enumerate(exr_files):
            print(f"  Processing frame {start_frame + i} ({i+1}/{len(exr_files)}): {os.path.basename(exr_path)}")
            
            img_buf = OIIO.ImageBuf(exr_path)

            OIIO.ImageBufAlgo.channels(img_buf, img_buf, (0,1,2))
            
            success_ocio = OIIO.ImageBufAlgo.colorconvert(img_buf, img_buf, "ACEScg", "Output - sRGB", colorconfig=ocio_config_path)
            if not success_ocio:
                print(f"OCIO Color Convert failed for frame {start_frame + i}. Check OCIO config and colorspace names.")
                return False

            if img_buf.spec().width != output_width or img_buf.spec().height != output_height:
                print(f"DEBUG: Resizing frame {start_frame + i} from {img_buf.spec().width}x{img_buf.spec().height} to {output_width}x{output_height}")
                img_buf = OIIO.ImageBufAlgo.resize(img_buf, "box", roi=OIIO.ROI(0, output_width, 0, output_height))

            pixels_raw = img_buf.get_pixels(OIIO.UINT16)

            print(f"DEBUG: Frame {start_frame + i} - Pixels raw shape: {pixels_raw.shape}, dtype: {pixels_raw.dtype}")
            expected_bytes = output_width * output_height * 3 * 2
            actual_bytes = len(pixels_raw.tobytes())
            print(f"DEBUG: Frame {start_frame + i} - Pixels raw byte length: {actual_bytes}, Expected: {expected_bytes}")
            if actual_bytes != expected_bytes:
                print("CRITICAL ERROR: Mismatch in pixel data byte length!")
                return False

            ffproc.stdin.write(pixels_raw.tobytes())

        print("Color conversion and piping complete. Waiting for FFmpeg to finish...")
        ffproc.stdin.close()
        stdout, stderr = ffproc.communicate()

        if ffproc.returncode != 0:
            print(f"ERROR: FFmpeg exited with error code {ffproc.returncode}")
            print("FFmpeg stdout:\n", stdout.decode())
            print("FFmpeg stderr:\n", stderr.stderr.decode())
            return False
        else:
            print("FFmpeg encoding finished successfully!")
            return True

    except Exception as e:
        print(f"An error occurred during the conversion process: {e}")
        import traceback
        traceback.print_exc()
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