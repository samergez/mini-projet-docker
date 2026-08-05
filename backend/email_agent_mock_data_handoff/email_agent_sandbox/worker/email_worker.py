#!/usr/bin/env python3
"""Static Email Dataset Worker - no runtime LLM."""
from __future__ import annotations
import argparse, base64, json, mimetypes, os, smtplib, time
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path
from typing import Any, Dict
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def now(): return datetime.now(timezone.utc)
def load_json(p: Path, default=None):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def save_json(p: Path, data: Any):
    p.parent.mkdir(parents=True, exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8'); tmp.replace(p)
def fmt(person: Dict[str,str]):
    return f"{person.get('name','')} <{person.get('email','')}>".strip()
def att_path(root: Path, att: Dict[str,Any]):
    p=Path(att['path']); return p if p.is_absolute() else root/p

def build_email(root: Path, m: Dict[str,Any], state: Dict[str,Any], mode: str):
    em=EmailMessage(); original_from=fmt(m['from']); original_to=', '.join(fmt(x) for x in m.get('to',[]))
    if mode=='smtp':
        smtp_user=os.getenv('SMTP_USERNAME','').strip(); sandbox_to=os.getenv('SANDBOX_TO_EMAIL','').strip(); from_name=os.getenv('MAIL_FROM_NAME','Sandbox Mail Worker')
        if not smtp_user or not sandbox_to: raise RuntimeError('SMTP_USERNAME and SANDBOX_TO_EMAIL are required in smtp mode')
        em['From']=f'{from_name} <{smtp_user}>'; em['To']=sandbox_to; em['X-Sandbox-Original-From']=original_from; em['X-Sandbox-Original-To']=original_to
    else:
        em['From']=original_from; em['To']=original_to
    em['Subject']=m['subject']; em['Date']=format_datetime(now())
    state.setdefault('message_rfc_ids',{})
    em['Message-ID']=state['message_rfc_ids'].get(m['message_id']) or make_msgid(idstring=m['message_id'], domain='email-sandbox.local')
    state['message_rfc_ids'][m['message_id']]=em['Message-ID']
    em['X-Sandbox-Message-Id']=m['message_id']; em['X-Sandbox-Thread-Id']=m['thread_id']; em['X-Sandbox-Priority']=m.get('priority','normal')
    if m.get('reply_to_message_id') and state['message_rfc_ids'].get(m['reply_to_message_id']):
        em['In-Reply-To']=state['message_rfc_ids'][m['reply_to_message_id']]; em['References']=state['message_rfc_ids'][m['reply_to_message_id']]
    body=m.get('body_text','')
    if mode=='smtp':
        body=f"SANDBOX ORIGINAL FROM: {original_from}\nSANDBOX ORIGINAL TO: {original_to}\nTHREAD: {m['thread_id']}\nCATEGORY: {m.get('ground_truth',{}).get('category','')}\n\n--- EMAIL BODY ---\n\n"+body
    em.set_content(body)
    for a in m.get('attachments',[]):
        p=att_path(root,a)
        if not p.exists(): raise FileNotFoundError(p)
        ctype=a.get('mime_type') or mimetypes.guess_type(str(p))[0] or 'application/octet-stream'; maintype, subtype=ctype.split('/',1)
        em.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=a.get('filename') or p.name)
    return em

def send_smtp(root,m,state):
    user=os.getenv('SMTP_USERNAME','').strip(); pwd=os.getenv('SMTP_APP_PASSWORD','').strip(); host=os.getenv('SMTP_HOST','smtp.gmail.com'); port=int(os.getenv('SMTP_PORT','465'))
    if not user or not pwd: raise RuntimeError('SMTP_USERNAME and SMTP_APP_PASSWORD are required')
    em=build_email(root,m,state,'smtp')
    with smtplib.SMTP_SSL(host,port) as smtp: smtp.login(user,pwd); smtp.send_message(em)
    return {'transport':'smtp','rfc_message_id':em['Message-ID']}

def gmail_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    scopes=['https://www.googleapis.com/auth/gmail.modify']; secret=Path(os.getenv('GOOGLE_OAUTH_CLIENT_SECRET','credentials/client_secret.json')); token=Path(os.getenv('GOOGLE_TOKEN_PATH','credentials/token.json'))
    creds=Credentials.from_authorized_user_file(str(token),scopes) if token.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            if not secret.exists(): raise RuntimeError(f'Missing OAuth secret: {secret}')
            creds=InstalledAppFlow.from_client_secrets_file(str(secret),scopes).run_local_server(port=0)
        token.parent.mkdir(parents=True,exist_ok=True); token.write_text(creds.to_json(),encoding='utf-8')
    return build('gmail','v1',credentials=creds)

def send_import(root,m,state):
    service=gmail_service(); em=build_email(root,m,state,'gmail-api-import'); raw=base64.urlsafe_b64encode(em.as_bytes()).decode('ascii')
    labels=['INBOX','UNREAD'] if m.get('mailbox_side','incoming')=='incoming' else ['SENT']; body={'raw':raw,'labelIds':labels}
    tid=state.setdefault('gmail_threads',{}).get(m['thread_id'])
    if tid: body['threadId']=tid
    res=service.users().messages().import_(userId='me', body=body, internalDateSource='dateHeader').execute()
    if res.get('threadId'): state['gmail_threads'][m['thread_id']]=res['threadId']
    return {'transport':'gmail-api-import','gmail_message_id':res.get('id'),'gmail_thread_id':res.get('threadId'),'rfc_message_id':em['Message-ID']}

def due(dataset,state,speed,batch):
    state.setdefault('simulation_start_utc', now().isoformat()); start=datetime.fromisoformat(state['simulation_start_utc']); start=start if start.tzinfo else start.replace(tzinfo=timezone.utc)
    sent=set(state.get('sent_message_ids',[])); out=[]
    for m in sorted(dataset['messages'], key=lambda x:(x['send_after_minutes'],x['message_id'])):
        if m['message_id'] in sent: continue
        due_at=start+timedelta(seconds=float(m.get('send_after_minutes',0))*60.0/speed)
        if now()>=due_at: out.append(m)
        if len(out)>=batch: break
    return out

def process_once(root,dataset_path,state_path,mode,speed,batch,mark_dry):
    dataset=load_json(dataset_path); state=load_json(state_path,{}) or {}; state.setdefault('sent_message_ids',[]); state.setdefault('send_log',[])
    items=due(dataset,state,speed,batch)
    if not items: print(f'[{now().isoformat()}] No due messages.'); save_json(state_path,state); return 0
    for m in items:
        print(f'[{now().isoformat()}] Due: {m["message_id"]} | {m["subject"]}')
        if mode=='dry-run':
            result={'transport':'dry-run'}
            if not mark_dry: continue
        elif mode=='smtp': result=send_smtp(root,m,state)
        elif mode=='gmail-api-import': result=send_import(root,m,state)
        else: raise ValueError(mode)
        state['sent_message_ids'].append(m['message_id']); state['send_log'].append({'message_id':m['message_id'],'thread_id':m['thread_id'],'sent_at_utc':now().isoformat(),'mode':mode,'result':result}); save_json(state_path,state)
    return len(items)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',default=str(Path(__file__).resolve().parents[1])); ap.add_argument('--dataset',default='dataset/emails_dataset.json'); ap.add_argument('--state',default='state/sent_state.json'); ap.add_argument('--mode',default=os.getenv('WORKER_MODE','dry-run'),choices=['dry-run','smtp','gmail-api-import']); ap.add_argument('--interval-seconds',type=int,default=int(os.getenv('WORKER_INTERVAL_SECONDS','60'))); ap.add_argument('--batch-size',type=int,default=int(os.getenv('WORKER_BATCH_SIZE','1'))); ap.add_argument('--speed-multiplier',type=float,default=float(os.getenv('WORKER_SPEED_MULTIPLIER','60'))); ap.add_argument('--once',action='store_true'); ap.add_argument('--mark-dry-run-sent',action='store_true')
    a=ap.parse_args(); root=Path(a.project_root).resolve(); dataset=(root/a.dataset).resolve(); state=(root/a.state).resolve()
    print(f'Mode: {a.mode}\nDataset: {dataset}\nState: {state}\nSpeed multiplier: {a.speed_multiplier}')
    while True:
        process_once(root,dataset,state,a.mode,a.speed_multiplier,a.batch_size,a.mark_dry_run_sent)
        if a.once: break
        time.sleep(a.interval_seconds)
if __name__=='__main__': main()
