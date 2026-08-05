#!/usr/bin/env python3
import json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'dataset/emails_dataset.json').read_text(encoding='utf-8'))
errors=[]; seen=set(); by_thread={}
for m in data.get('messages',[]):
    mid=m.get('message_id')
    if not mid: errors.append('message without id'); continue
    if mid in seen: errors.append(f'duplicate message_id {mid}')
    seen.add(mid); by_thread.setdefault(m.get('thread_id'),set()).add(mid)
    if not m.get('subject'): errors.append(f'{mid}: missing subject')
    if not m.get('body_text'): errors.append(f'{mid}: missing body_text')
    if not isinstance(m.get('send_after_minutes'),(int,float)): errors.append(f'{mid}: send_after_minutes must be numeric')
    rep=m.get('reply_to_message_id')
    if rep and rep not in seen: errors.append(f'{mid}: reply_to_message_id is missing or later than this message: {rep}')
    for a in m.get('attachments',[]):
        p=root/a.get('path','')
        if not p.exists(): errors.append(f'{mid}: missing attachment {p}')
if errors:
    print('Dataset validation failed:'); [print(' -',e) for e in errors]; sys.exit(1)
print(f"Dataset OK: {len(data.get('messages',[]))} messages, {len(data.get('threads',[]))} threads")
