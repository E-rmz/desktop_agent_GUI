import tempfile, re, ast
from gradio_client import Client, handle_file
from PIL import Image

def process_screenshot(screenshot_bytes: bytes):
    """
    → screenshot_bytes: raw PNG bytes (exactly what page.screenshot() gives)
    ← returns (annotated_png: bytes, icons: List[dict])
    """
    # dump the input bytes to disk so gradio_client can use it
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(screenshot_bytes)
        tmp_path = tmp.name

    # call the Space
    client = Client("microsoft/OmniParser-v2")
    annotated_path, raw_text = client.predict(
        image_input=handle_file(tmp_path),
        box_threshold=0.1,
        iou_threshold=0.1,
        use_paddleocr=True,
        imgsz=640,
        api_name="/process"
    )

    # read back the annotated image as raw PNG bytes
    with open(annotated_path, "rb") as f:
        annotated_png = f.read()

    # parse the icons out of the text
    img = Image.open(annotated_path)
    w, h = img.size
    icons = []
    for raw in re.findall(r"icon \d+: (\{.*?\})", raw_text):
        d = ast.literal_eval(raw)
        x1, y1, x2, y2 = d["bbox"]
        icons.append({
            "x": int((x1 + x2)/2 * w),
            "y": int((y1 + y2)/2 * h),
            "interactivity": str(d["interactivity"]).lower(),
            "content": d["content"]
        })

    return annotated_png, icons
