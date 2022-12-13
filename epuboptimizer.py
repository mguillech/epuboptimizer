import sys
from pathlib import Path

IMAGE_ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.svg']
TEXTFILES_ALLOWED_EXTENSIONS = ['.opf', '.html', '.xhtml', '.css']
FONT_EXTENSIONS = ['.otf', '.ttf']
ENCRYPTION_FILES = ['encryption.xml']
EXCLUDE_FILES = ['mimetype', 'mimetype.jpg', 'mimetype.jpeg']
MIMETYPES = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.bmp': 'image/bmp',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml'
}


def get_files_in_directory(directory):
    images, textfiles = {}, []
    has_fonts, has_encryption = False, False
    for file_path in Path(directory).iterdir():
        file_extension = file_path.suffix.lower()
        if file_path.name in EXCLUDE_FILES:
            # print("Excluding file: {}...".format(file_path.name))
            continue
        if file_path.is_dir():
            recursive_images, recursive_textfiles = get_files_in_directory(file_path)
            images.update(recursive_images)
            textfiles.extend(recursive_textfiles)
        else:
            if file_extension in IMAGE_ALLOWED_EXTENSIONS:
                images[file_path.stem] = file_path
            elif file_extension in TEXTFILES_ALLOWED_EXTENSIONS:
                textfiles.append(file_path)
            elif file_extension in FONT_EXTENSIONS:
                has_fonts = True
            elif file_path.name in ENCRYPTION_FILES:
                has_encryption = True
    if has_fonts:
        print("WARNING: this ePub has fonts included.")
    if has_encryption:
        print("WARNING: this ePub has encryption.")
    return images, textfiles


def update_textfiles(directory_textfiles, files_to_update):
    # print("Directory textfiles: {}".format(directory_textfiles))
    # print("Files to update: {}".format(files_to_update))
    for textfile_path in directory_textfiles:
        overwrite_textfile = False
        with textfile_path.open() as textfile_fd:
            content = textfile_fd.readlines()
        for file_to_update in files_to_update:
            for line_no, line_content in enumerate(content):
                old_path, new_path = file_to_update
                if old_path.name in line_content:
                    overwrite_textfile = True
                    content[line_no] = content[line_no].replace(old_path.name, new_path.name)
                    if 'media-type' in line_content:
                        content[line_no] = content[line_no].replace(MIMETYPES[old_path.suffix.lower()],
                                                                    MIMETYPES[new_path.suffix.lower()])
        if overwrite_textfile:
            with textfile_path.open('w') as textfile_fd:
                textfile_fd.write('\n'.join(content))


def move_images(source_directory_images, target_directory_images, keep_source_image=False, keep_target_image=True):
    files_to_update = []
    for source_image_filename, source_image_path in source_directory_images.items():
        try:
            target_image_path = target_directory_images[source_image_filename]
        except KeyError:
            continue
        # Only replace source images with smaller or equal sized target images (except for zero-sized target images)
        if source_image_path.stat().st_size <= target_image_path.stat().st_size or target_image_path.stat().st_size == 0:
            # print("Skipping source image: {}".format(source_image_path))
            if not keep_target_image:
                # print("Removing target image: {}".format(target_image_path))
                target_image_path.unlink()
            continue
        if not keep_source_image:
            # print("Removing source image: {}".format(source_image_path))
            source_image_path.unlink()
        if source_image_path.suffix != target_image_path.suffix:
            old_source_image_path = source_image_path
            source_image_path = source_image_path.with_suffix(target_image_path.suffix)
            files_to_update.append((old_source_image_path, source_image_path))
        # print("Renaming target image: {} to source image: {}".format(target_image_path, source_image_path))
        target_image_path.rename(source_image_path)
    return files_to_update


def main(source_directory, target_directory):
    source_directory_images, source_directory_textfiles = get_files_in_directory(source_directory)
    target_directory_images, _ = get_files_in_directory(target_directory)
    files_to_update = move_images(source_directory_images, target_directory_images)
    update_textfiles(source_directory_textfiles, files_to_update)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: {} source-directory target-directory".format(sys.argv[0]))
    else:
        main(sys.argv[1], sys.argv[2])
