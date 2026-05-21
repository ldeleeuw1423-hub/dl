import os
import re
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".xls", ".doc",
    ".dwg", ".dxf", ".shp", ".geojson", ".json",
    ".png", ".jpg", ".jpeg", ".tif", ".tiff",
    ".csv", ".txt",
}


class FileService:
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)

    def _get_project_dir(self, project_id: str) -> Path:
        project_dir = self.upload_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def _sanitize_filename(self, filename: str) -> str:
        # Remove path components and sanitize
        filename = os.path.basename(filename)
        filename = re.sub(r"[^\w\-_. ]", "_", filename)
        return filename[:255]

    async def save_file(self, project_id: str, filename: str, content: bytes) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {ext} not allowed")
        safe_filename = self._sanitize_filename(filename)
        project_dir = self._get_project_dir(project_id)
        file_path = project_dir / safe_filename

        # Handle duplicates by appending counter
        counter = 1
        stem = Path(safe_filename).stem
        while file_path.exists():
            safe_filename = f"{stem}_{counter}{ext}"
            file_path = project_dir / safe_filename
            counter += 1

        file_path.write_bytes(content)
        logger.info(f"Saved file {file_path}")
        return str(file_path.relative_to(self.upload_dir))

    def list_files(self, project_id: str) -> List[Dict[str, Any]]:
        project_dir = self._get_project_dir(project_id)
        files = []
        for f in sorted(project_dir.iterdir()):
            if f.is_file():
                stat = f.stat()
                files.append({
                    "filename": f.name,
                    "size_bytes": stat.st_size,
                    "modified_at": stat.st_mtime,
                    "url": f"/uploads/{project_id}/{f.name}",
                })
        return files

    def delete_file(self, project_id: str, filename: str) -> bool:
        safe_filename = self._sanitize_filename(filename)
        file_path = self._get_project_dir(project_id) / safe_filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False
