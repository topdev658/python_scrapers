import os
import tempfile
from typing import List, Tuple
from zipfile import ZipFile, ZIP_DEFLATED

__version__ = '1.0.1'
__changelog__ = """
1.0.1
open in bin mode (to fix type checking)
"""


def _tmp_file_path(file_name: str) -> str:
    return os.path.join(tempfile.gettempdir(), file_name)


def save_zip_arch(
        zip_path: str,
        contents: List[Tuple[str, bytes]]) -> bool:
    """
    Must wrap into try/except in caller
    :param zip_path: zip arch path
    :param contents: [(archived_file_name, archived_file_content)
    :return: ok
    """
    try:
        # Only filenames or strings can feed to zip_file.write
        # in our case these are PDF bytes, so we'll:
        # Create temp files
        for archived_name, archived_content in contents:
            with open(_tmp_file_path(archived_name), 'wb') as f:
                f.write(archived_content)

        # Create zip arch
        with open(zip_path, 'wb') as f:
            f.write(b'')

        # Write zip
        with ZipFile(zip_path, 'w', compression=ZIP_DEFLATED) as zip_file:
            for archived_name, archived_content in contents:
                zip_file.write(_tmp_file_path(archived_name), archived_name)

        return True
    finally:
        # Delete temp files
        for archived_name, _ in contents:
            os.remove(_tmp_file_path(archived_name))
