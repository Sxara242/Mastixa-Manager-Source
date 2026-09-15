"""Isolated protocol server and repository double; never contacts a real account."""
import copy
from app.gis.sync_contract import validate,fingerprint,RemoteConflict


class MemoryTransport:
    def __init__(self):self.rows={};self.sequence=0;self.offline=False;self.lose_ack=False;self.uploads=0
    def pull(self,cursor):
        if self.offline:raise ConnectionError('Offline fixture')
        return self.sequence,copy.deepcopy([r for r in self.rows.values() if r['sequence']>cursor])
    def push(self,record,expected):
        if self.offline:raise ConnectionError('Offline fixture')
        record=validate(record);old=self.rows.get(record['id'])
        if old and old['record']==record:return copy.deepcopy(old)
        if expected!=(old['version'] if old else 0):raise RemoteConflict(copy.deepcopy(old))
        self.sequence+=1;self.uploads+=1;row=dict(record=record,version=expected+1,sequence=self.sequence);self.rows[record['id']]=row
        if self.lose_ack:self.lose_ack=False;raise ConnectionError('Committed upload but acknowledgement lost')
        return copy.deepcopy(row)


class MemoryRepository:
    def __init__(self):self.rows={};self.states={};self.conflicts=[];self.position=0
    def cursor(self):return self.position
    def set_cursor(self,value):self.position=value
    def document(self,identity):return copy.deepcopy(self.rows.get(identity))
    def documents(self):return copy.deepcopy(list(self.rows.values()))
    def state(self,identity):return self.states.get(identity)
    def acknowledge(self,identity,digest,version):self.states[identity]=dict(local_hash=digest,remote_version=version)
    def blocked(self,identity):return any(c['remote']['record']['id']==identity for c in self.conflicts)
    def dirty_dependents(self,identity):return any(r['id']!=identity and r['parcel_id']==identity and (r['id'] not in self.states or fingerprint(r)!=self.states[r['id']]['local_hash']) for r in self.rows.values())
    def conflict(self,local,remote,reason):
        entry=copy.deepcopy(dict(local=local,remote=remote,reason=reason))
        if entry not in self.conflicts:self.conflicts.append(entry)
    def apply(self,remote,expected_hash):
        record=validate(remote['record']);old=self.rows.get(record['id'])
        if (fingerprint(old) if old else None)!=expected_hash:raise ValueError('Local edit during sync')
        if record['kind']!='parcel' and record['parcel_id'] not in self.rows:raise ValueError('Missing parent')
        self.rows[record['id']]=copy.deepcopy(record);self.acknowledge(record['id'],fingerprint(record),remote['version'])
    def resolve(self,index,choice):
        conflict=self.conflicts[index];remote=conflict['remote'];identity=remote['record']['id'];current=self.rows.get(identity)
        if current!=conflict['local']:raise ValueError('Local record changed since conflict preview')
        if choice=='remote':self.apply(remote,fingerprint(current) if current else None)
        elif choice=='local':self.acknowledge(identity,fingerprint(remote['record']),remote['version'])
        else:raise ValueError('Explicit resolution required')
        self.conflicts.pop(index)
