import sys
import os

sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for creating an image contact sheet.
    Handles multiple selected image files.
    """
    if len(sys.argv) < 2:
        print("Error: No image file paths provided. Select multiple images to create a contact sheet.")
        print("Press Enter to exit.")
        input()
        return

    # sys.argv[0] is the script name, subsequent arguments are file paths
    image_paths = sys.argv[1:]

    # Filter out non-existent files
    valid_image_paths = [p for p in image_paths if os.path.exists(p)]

    if not valid_image_paths:
        print("Error: No valid image files found among the selections.")
        print("Press Enter to exit.")
        input()
        return
    
    print(f"Creating contact sheet for {len(valid_image_paths)} images...")
    for path in valid_image_paths:
        print(f"  - {os.path.basename(path)}")

    # The create_contact_sheet function will determine output path based on the first image's directory
    success = converter.create_contact_sheet(valid_image_paths)

    if success:
        print("\nContact sheet created successfully!")
    else:
        print("\nFailed to create contact sheet. Please check the errors above.")
    print("Press Enter to exit.")
    input()


if __name__ == '__main__':
    main()
