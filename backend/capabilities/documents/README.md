# Documents Capability
## Purpose
Document parsing, text extraction, local OCR, and summarization.

## Architecture
- `pdf.py`: PDF layout and text parsing.
- `office.py`: Microsoft Office documents parsing.
- `reader.py`: Plain text and markdown readers.
- `summarize.py`: Generates summaries and action items.
- `translate.py`: Local language translation.

## Relationships
- **Core:** Summarizes active PDFs or documents.
- **Memory:** Commits chunk embeddings to the vector database.
- **OS Layer:** Reads files using the File System Port.
