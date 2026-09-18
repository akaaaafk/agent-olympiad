"""Host-bound artifact documents for the existing contestant page reader.

Prepared task assets and current rendered candidates are trusted capabilities,
not arbitrary file paths supplied by a model or a benchmark row.
"""
from hashlib import sha256
from pathlib import Path


class ArtifactPdfRow(dict):
    def __init__(self, documents):
        super().__init__(problem_id='deliverable', assets=[])
        self.documents = documents


def asset_document(asset, *, label='Official task'):
    return dict(path=str(asset.path.resolve()), sha256=asset.sha256,
                pages=list(range(asset.page_start, asset.page_end + 1)), label=label)


def verified_documents(row):
    from problem_pdf import ProblemPdfError
    entries = []
    for doc in row.documents:
        path = Path(doc['path'])
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != doc['sha256']:
            raise ProblemPdfError('Artifact PDF changed since run preparation or rendering.')
        entries.append({**doc, 'resolved_path': path})
    return entries


def row_for(manifest, session):
    documents = [manifest.metadata['artifact_task_pdf']]
    current = getattr(session, 'artifact_review_document', None)
    if current is not None:
        review = current()
        if review is not None:
            documents.append(review)
    return ArtifactPdfRow(documents)
