import os

def delete_files_and_directory(path):
    items = None
    # Traverse all files and subdirectories in the specified directory
    try:
        items = os.listdir(path)
    except OSError as e:
        print("Failed to listdir %s: %s" % (path, e))
        return

    for item in items:
        # Construct the full path of the item
        item_path = path + '/' + item
        try:
            # Get the status information of the file or directory
            # print(os.stat(item_path))
            if os.stat(item_path)[6] == 0:
                delete_files_and_directory(item_path)  # Recursively delete empty subdirectories
                # If the size is 0, it is considered an empty directory
                os.rmdir(item_path)  # Remove the empty directory
                print("Removed empty directory: %s" % item_path)
            else:
                # If the size is not 0, it is considered a file
                os.remove(item_path)  # Remove the file
                print("Removed file: %s" % item_path)
        except OSError as e:
            print("Failed to remove %s: %s" % (item_path, e))

    # Finally, remove the root directory
    try:
        os.rmdir(path)
        print("Removed root directory: %s" % path)
    except OSError as e:
        print("Failed to remove root directory %s: %s" % (path, e))

# Call the function
delete_files_and_directory('/sd')
