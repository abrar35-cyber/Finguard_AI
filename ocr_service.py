def extract_text_from_image(
    uploaded_file
):

    try:

        import pytesseract
        from PIL import Image

        image = Image.open(
            uploaded_file
        )

        text = pytesseract.image_to_string(
            image
        )

        return text

    except Exception:

        return ""
