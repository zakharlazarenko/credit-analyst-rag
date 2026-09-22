from pydantic import BaseModel, Field


class PageDocument(BaseModel):
    doc_id: str
    company: str
    year: int
    doc_type: str
    page: int = Field(ge=1)
    text: str

class ManifestEntry(BaseModel):
    doc_id: str
    company: str
    year: int
    doc_type: str
    url: str
    sha256: str
    pages: int = Field(ge=1)

class ChunkDocument(BaseModel):
    chunk_id: str
    doc_id: str
    company: str
    year: int
    doc_type: str
    page: int = Field(ge=1)
    chunk_index: int = Field(ge=1)
    text: str = Field(min_length=1)

if __name__ == "__main__":
    page = PageDocument(
        doc_id="lukoil_ar_2024",
        company="LUKOIL",
        year=2024,
        doc_type="annual_report",
        page=28,
        text="ЛУКОЙЛ признает важность мероприятий по предотвращению изменения климата.",
    )

    print(page)
    print()
    print(page.model_dump())