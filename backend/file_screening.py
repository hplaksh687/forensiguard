import magic


def detect_multi_extension(filename):

    parts = filename.split(".")

    if len(parts) > 2:
        return True

    return False


def verify_file_type(file_path):

    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)

    return file_type