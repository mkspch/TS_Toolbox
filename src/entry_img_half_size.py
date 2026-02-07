import sys
import os

sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for the image half size conversion.
    """
    if len(sys.argv) < 2:
        print("Error: No file path provided.")
        print("Press Enter to exit.")
        input()
        return

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"Error: The file '{image_path}' does not exist.")
        print("Press Enter to exit.")
        input()
        return
        
    print(f"Image to half size: {image_path}")
    success = converter.convert_img_half_size(image_path)

    if success:
        print("\nConversion finished successfully!")
    else:
        print("\nConversion failed. Please check the errors above.")
    print("Press Enter to exit.")
    input()


if __name__ == '__main__':
    main()
