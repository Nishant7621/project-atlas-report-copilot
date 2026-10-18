"""
Document Chunker for Project Atlas.
Parses reports with page boundaries and extracts structured chunks with full metadata:
report_id, sector, region, year, page.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

class ReportChunker:
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir

    def extract_metadata_from_text(self, text: str, default_sector: str) -> Dict[str, Any]:
        """Infers region and year from text content to attach rich chunk metadata"""
        # Detect year
        year_match = re.search(r'\b(202[4-9]|2030)\b', text)
        year = year_match.group(1) if year_match else "2024-2030"

        # Detect region
        if "Asia-Pacific" in text or "APAC" in text:
            region = "APAC"
        elif "North America" in text:
            region = "North America"
        elif "Europe" in text:
            region = "Europe"
        elif "Global" in text or "worldwide" in text.lower():
            region = "Global"
        else:
            region = "Global"

        return {
            "region": region,
            "year": year,
            "sector": default_sector
        }

    def chunk_file(self, file_path: Path) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by page marker comments
        page_pattern = re.compile(
            r'<!-- PAGE (\d+) START \| REPORT_ID: ([\w-]+) \| SECTOR: ([\w\s&]+) -->\s*(.*?)\s*<!-- PAGE \1 END -->',
            re.DOTALL
        )

        matches = page_pattern.findall(content)
        chunks = []

        if not matches:
            # Fallback if no page tags
            rep_id = file_path.stem
            chunks.append({
                "chunk_id": f"{rep_id}-p1-c1",
                "report_id": rep_id,
                "page": 1,
                "sector": "General",
                "region": "Global",
                "year": "2024",
                "text": content.strip()
            })
            return chunks

        for page_num_str, rep_id, sector, page_body in matches:
            page_num = int(page_num_str)
            # Split page body into paragraphs or sections
            paragraphs = [p.strip() for p in page_body.split("\n\n") if len(p.strip()) > 30]
            
            if not paragraphs:
                paragraphs = [page_body.strip()]

            for idx, p_text in enumerate(paragraphs, start=1):
                meta = self.extract_metadata_from_text(p_text, sector.strip())
                chunk_id = f"{rep_id}-p{page_num}-c{idx}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "report_id": rep_id,
                    "page": page_num,
                    "sector": meta["sector"],
                    "region": meta["region"],
                    "year": meta["year"],
                    "text": p_text
                })

        return chunks

    def chunk_all_reports(self) -> List[Dict[str, Any]]:
        all_chunks = []
        for file_path in sorted(self.reports_dir.glob("*.md")):
            file_chunks = self.chunk_file(file_path)
            all_chunks.extend(file_chunks)
        return all_chunks
