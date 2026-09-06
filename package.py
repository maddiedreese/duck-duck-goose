"""Create a reviewable source ZIP from an explicit allowlist."""
from pathlib import Path
import hashlib
import json
import zipfile

root=Path(__file__).parent
files=[root/p for p in ('README.md','NOTICE.md','LICENSE','CAPTION.txt','GOAL.md','SUBMISSION.md','.gitignore',
                       'requirements.txt','run.sh','policy.py','simulation.py','flock.py','costumes.py','full_game.py',
                       'render.py','full_render.py','main.py','test_game.py','package.py')]
files+=sorted(p for p in (root/'assets').rglob('*') if p.is_file())
archive=root.parent/'duck-duck-goose-source.zip'
inventory=[]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in files:
        data=path.read_bytes()
        relative=path.relative_to(root).as_posix()
        z.write(path,relative)
        inventory.append({'path':relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)
manifest={'zip':archive.name,'bytes':archive.stat().st_size,
          'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':inventory}
(root.parent/'duck-duck-goose-zip-inventory.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'zip':str(archive),'bytes':archive.stat().st_size,'files':len(files)},indent=2))
