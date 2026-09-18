"""Publish an exact non-cache mini snapshot; never persist authentication tokens."""
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

from huggingface_hub import HfApi, CommitOperationAdd, CommitOperationDelete, hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / 'data/mini_data'
REPO = 'DAPlab11/mini_batch_multi_agent_bench'
sys.path.insert(0, str(ROOT))
from scripts.audit_mini_dependency_hashes import audit


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    assert not audit(), 'Mini dependency drift; verify before publishing'
    verification = json.loads((MINI / 'verification.json').read_text())
    assert verification['passed'] and verification['all_jobs_environment_ready']
    assert verification['paid_model_calls'] == 0 and not verification['asset_errors']
    selection = json.loads((MINI / 'selection_manifest.json').read_text())
    index = json.loads((MINI / 'benchmarks/index.json').read_text())
    assert len(index['olympiads']) == 39
    for track in index['olympiads']:
        rows = json.loads((ROOT / track['benchmark_path']).read_text())
        selected = next(t for t in selection['tracks'] if t['competition_id'] == track['id'])
        assert sorted(r['problem_id'] for r in rows) == sorted(selected['selected_record_ids'])
    dependencies = json.loads((MINI / 'dependency_manifest.json').read_text())['files']
    excluded = {'.cache', '.git'}
    files = {}
    for path in sorted(MINI.rglob('*')):
        relative = path.relative_to(MINI)
        if not path.is_file() or any(p in excluded for p in relative.parts):
            continue
        if '__pycache__' in relative.parts and relative.as_posix() not in dependencies:
            continue
        assert not path.is_symlink()
        assert path.resolve().is_relative_to(MINI.resolve())
        # Detect real HF/API credential shapes without printing their values.
        if path.stat().st_size < 2_000_000 and path.suffix.lower() in {'.json','.md','.txt','.py','.html','.sh','.yaml','.yml'}:
            raw = path.read_bytes()
            assert not re.search(rb'(?<![A-Za-z0-9_])(?:hf_[A-Za-z0-9]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{35,})', raw), f'Credential-shaped content; manual review required: {relative}'
        files[relative.as_posix()] = dict(sha256=digest(path), bytes=path.stat().st_size)
    assert set(dependencies) <= set(files), 'Publishing must preserve all declared dependency files'
    token = getpass.getpass('HF token (hidden): ')
    api = HfApi(token=token)
    identity = api.whoami()
    info = api.repo_info(REPO, repo_type='dataset', files_metadata=True)
    assert info.id == REPO and info.private, 'Do not change publication visibility'
    remote = {s.rfilename for s in info.siblings}
    obsolete = sorted(remote - set(files) - {'.gitattributes'})
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    folder = ROOT / 'output/huggingface_publish' / stamp
    folder.mkdir(parents=True)
    manifest = dict(repo=REPO, account=identity['name'], private=info.private,
        previous_revision=info.sha, files=files, deleted_remote_files=obsolete,
        cache_excluded=True, dependency_files_preserved=len(dependencies))
    (folder / 'manifest_before_publish.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Publishing {len(files)} files; {len(obsolete)} stale remote files removed; private repo preserved.', flush=True)
    # Preupload/additions and removals become visible in one atomic commit.
    operations = [CommitOperationAdd(path_in_repo=name, path_or_fileobj=MINI / name) for name in files]
    operations += [CommitOperationDelete(path_in_repo=name) for name in obsolete]
    commit = api.create_commit(REPO, repo_type='dataset', operations=operations,
        commit_message='Replace mini snapshot: verified 39 tracks, 109 records, isolated PDF delivery',
        parent_commit=info.sha, num_threads=5)
    revision = commit.oid
    after = api.repo_info(REPO, repo_type='dataset', revision=revision, files_metadata=True)
    remote_files = {s.rfilename:s for s in after.siblings}
    assert set(remote_files) - {'.gitattributes'} == set(files)
    assert after.private == info.private
    checked = 0
    for name, meta in files.items():
        sibling = remote_files[name]
        if sibling.lfs:
            actual = sibling.lfs.sha256
            assert actual == meta['sha256'], f'Remote LFS hash mismatch: {name}'
        else:
            # Git blob identity verifies all ordinary files without re-downloading.
            raw = (MINI / name).read_bytes()
            actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            assert actual == sibling.blob_id, f'Remote Git blob mismatch: {name}'
        assert digest(MINI / name) == meta['sha256'], f'Local data changed during upload: {name}'
        checked += 1
    # Read back critical published metadata from this exact revision.
    for name in ['benchmarks/index.json','selection_manifest.json','problem_pdf_allowlist.json','verification.json']:
        downloaded = Path(hf_hub_download(REPO, name, repo_type='dataset', revision=revision, token=token))
        assert digest(downloaded) == files[name]['sha256']
    report = dict(repo=REPO, revision=revision, previous_revision=info.sha, private=after.private,
        files_verified=checked, remote_deleted=obsolete, critical_readbacks=4, tracks=39, records=109,
        timestamp_utc=datetime.now(timezone.utc).isoformat(), token_persisted=False)
    (folder / 'verified_publish.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
