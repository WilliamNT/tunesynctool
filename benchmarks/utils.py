from typing import Any, List, Optional, Tuple
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunesynctool.models import Track

import httpx
import tarfile
import shutil

async def get(url: str) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response

async def get_json(url: str) -> dict:
    response = await get(url)
    return dict(response.json())

async def get_txt(url: str) -> str:
    response = await get(url)
    return response.text.strip()

async def download(url: str, path: Path) -> None:
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()

            with open(str(path.absolute()), "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

def ensure_path_exists(p: Path) -> Path:
    p = p.absolute()

    if not p.exists():
        p.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    return p

def rm_dir(path: Path) -> None:
    if not path.exists():
        return
    
    if not path.is_dir():
        raise ValueError(f"{str(path)} is not a directory and won't be deleted.")

    shutil.rmtree(str(path.absolute()))

def extract_tar_xz(path: Path, output: Path) -> None:
    with tarfile.open(path, "r:xz") as tar:
        tar.extractall(output)

class Report:
    def __init__(self):
        self.title: Optional[str] = None
        self.metadata: List[Tuple[str, str]] = []
        self.lines: List[str] = []

    def add(self, text: str) -> None:
        self.lines.append(text)

    def add_meta(self, field: str, value: Any) -> None:
        self.metadata.append(
            (field.strip(), str(value).strip())
        )

    def set_title(self, text: str) -> None:
        self.title = text.strip()

    def print(self) -> None:
        print(self)

    def save(self, path: Path) -> None:
        path = ensure_path_exists(path)

        with open(str(path), "w") as f:
            f.write(self.__str__())

    def __str__(self):
        report = ""

        if self.title:
            report += f"# {self.title}\n\n"

        if len(self.metadata) > 0:
            for field, value in self.metadata:
                report += f"- {field}: `{value}`\n"

            report += "---\n\n"

        report += "\n".join(self.lines).strip()

        return report

def map_dataset_recording_to_domain_model(line: str) -> Track:
    data: dict = json.loads(line)

    credits = data.get("artist-credit") or []
    primary_artist = credits[0].get("name") if credits else None
    additional_artists = [c.get("name") for c in credits[1:] if c.get("name")]

    for relation in data.get("relations", []):
        if relation.get("target-type") != "artist":
            continue

        if relation.get("type") not in ("remixer", "performer", "vocal", "instrument"):
            continue

        name = (relation.get("artist") or {}).get("name")
        
        if name and name != primary_artist and name not in additional_artists:
            additional_artists.append(name)

    length = data.get("length")
    isrcs = data.get("isrcs", [])

    return Track(
        title=data.get("title"),
        primary_artist=primary_artist,
        additional_artists=additional_artists,
        duration_seconds=int(length // 1000) if length else None,
        isrc=isrcs[0] if isrcs else None,
        musicbrainz_id=data.get("id"),
        service_id=data.get("id"),
        service_name="musicbrainz",
        service_data=data,
    )