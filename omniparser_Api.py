import pyautogui
import os
import json
import shutil

# Grab the entire screen
screenshot = pyautogui.screenshot()

# Save to a local file
screenshot_path = "desktop_screenshot.png"
screenshot.save(screenshot_path)
print(f"Screenshot saved to: {screenshot_path}")

from gradio_client import Client, handle_file

try:
    # 1️⃣ Create a client for the Space
    print("Connecting to OmniParser-v2 space...")
    client = Client("microsoft/OmniParser-v2")
    
    # 2️⃣ Invoke the `/process` endpoint, passing your screenshot
    print("Processing screenshot...")
    result = client.predict(
        image_input=handle_file(screenshot_path),
        box_threshold=0.05,     # tweak as needed
        iou_threshold=0.1,      # tweak as needed
        use_paddleocr=True,     # or False
        imgsz=640,              # max dimension for icon detection
        api_name="/process"
    )
    
    # 3️⃣ Inspect the parsed output
    print("✅ Processing completed successfully!")
    print("\n" + "="*50)
    print("RESULT:")
    print("="*50)
    
    # Handle different result formats
    if isinstance(result, (list, tuple)):
        for i, item in enumerate(result):
            print(f"Output {i+1}: {item}")
            
        # Extract the processed image (first element of the tuple)
        if len(result) >= 1 and result[0]:
            processed_image_path = result[0]
            
            # Copy the processed image to current directory
            if os.path.exists(processed_image_path):
                output_filename = "omniparser_result.webp"
                shutil.copy2(processed_image_path, output_filename)
                print(f"\n🎉 Processed image saved to: {output_filename}")
                
                # Also try to get the file size
                file_size = os.path.getsize(output_filename)
                print(f"📁 File size: {file_size} bytes")
            else:
                print(f"⚠️ Processed image file not found at: {processed_image_path}")
                
        # If there's a second element (likely metadata or text results)
        if len(result) >= 2 and result[1]:
            print(f"\n📝 Additional output (metadata/text): {result[1]}")
            
            # Save text results to a file if it's text
            if isinstance(result[1], str):
                with open("omniparser_text_result.txt", "w", encoding="utf-8") as f:
                    f.write(result[1])
                print("📄 Text results saved to: omniparser_text_result.txt")
                
    elif isinstance(result, dict):
        print(json.dumps(result, indent=2))
    else:
        print(result)
    
    # Clean up the original screenshot file (optional)
    # os.remove(screenshot_path)
    
except Exception as e:
    print(f"❌ Error occurred: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    
    # Additional debugging info
    if hasattr(e, 'response'):
        print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
    
    # Keep the screenshot file for debugging
    print(f"Screenshot file kept at: {screenshot_path}")
