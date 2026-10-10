'use strict';
// Encrypted, short-lived transfer authorization. No release/repository upload.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const ARCHIVE_SHA256 = '53f501abccf027777eee8cddc5ded5771903d1e8af5760b3420652492aceb184';
const ARCHIVE_SIZE = 223348759;
const service = 'github.actions.results.api.v1.ArtifactService';

async function rpc(session, method, body) {
  const response = await fetch(new URL('/twirp/' + service + '/' + method, session.resultsUrl), {
    method: 'POST', headers: {'Authorization': 'Bearer ' + session.token, 'Content-Type': 'application/json'},
    body: JSON.stringify(body), signal: AbortSignal.timeout(30000)
  });
  if (!response.ok) throw new Error(method + ': HTTP ' + response.status);
  return response.json();
}

module.exports = async ({core, mode, publicKey}) => {
  if (process.env.GITHUB_ACTIONS !== 'true' || process.env.RUNNER_ENVIRONMENT !== 'github-hosted' ||
      process.env.GITHUB_EVENT_NAME !== 'workflow_dispatch') throw new Error('Hosted manual job required');
  const folder = path.join(process.env.RUNNER_TEMP, 'rc2-ingress');
  const stateFile = path.join(folder, 'private-session.json');
  const token = process.env.ACTIONS_RUNTIME_TOKEN;
  core.setSecret(token);
  if (!token || !process.env.ACTIONS_RESULTS_URL) throw new Error('Missing artifact runtime context');
  if (mode === 'prepare') {
    fs.mkdirSync(folder, {recursive: false});
    const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
    const scope = claims.scp.split(' ').find(item => item.startsWith('Actions.Results:'))?.split(':');
    if (!scope || scope.length !== 3) throw new Error('Missing results scope');
    const session = {token, resultsUrl: process.env.ACTIONS_RESULTS_URL,
      workflowRunBackendId: scope[1], workflowJobRunBackendId: scope[2],
      name: 'rc2-candidate-' + process.env.GITHUB_RUN_ID, archiveSha256: ARCHIVE_SHA256,
      archiveSize: ARCHIVE_SIZE, runId: process.env.GITHUB_RUN_ID};
    const created = await rpc(session, 'CreateArtifact', {
      workflow_run_backend_id: session.workflowRunBackendId,
      workflow_job_run_backend_id: session.workflowJobRunBackendId,
      name: session.name, version: 4,
      expires_at: new Date(Date.now() + 86400000).toISOString()
    });
    if (!created.ok || !created.signed_upload_url) throw new Error('Artifact allocation failed');
    session.uploadUrl = created.signed_upload_url;
    core.setSecret(session.uploadUrl);
    const key = crypto.randomBytes(32), iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    const encrypted = Buffer.concat([cipher.update(JSON.stringify(session), 'utf8'), cipher.final()]);
    const sealed = {
      key: crypto.publicEncrypt({key: Buffer.from(publicKey, 'base64').toString('utf8'),
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256'}, key).toString('base64'),
      iv: iv.toString('base64'), tag: cipher.getAuthTag().toString('base64'),
      ciphertext: encrypted.toString('base64'), runId: session.runId
    };
    // The runner-local session never stores the bearer token and is never uploaded.
    const {token: omittedToken, uploadUrl: omittedUrl, ...publicState} = session;
    fs.writeFileSync(stateFile, JSON.stringify(publicState), {flag: 'wx'});
    fs.writeFileSync(path.join(folder, 'encrypted-upload.json'), JSON.stringify(sealed), {flag: 'wx'});
    core.info('Encrypted one-run candidate upload authorization prepared; no secret printed.');
    return;
  }
  if (mode !== 'wait') throw new Error('Unknown ingress mode');
  const session = {...JSON.parse(fs.readFileSync(stateFile)), token, resultsUrl: process.env.ACTIONS_RESULTS_URL};
  const deadline = Date.now() + 15 * 60000;
  let accepted;
  while (Date.now() < deadline) {
    const listed = await rpc(session, 'ListArtifacts', {
      workflow_run_backend_id: session.workflowRunBackendId,
      workflow_job_run_backend_id: session.workflowJobRunBackendId,
      name_filter: session.name
    });
    accepted = (listed.artifacts || []).find(item => item.name === session.name &&
      Number(item.size) === ARCHIVE_SIZE && String(item.digest || '').replace(/^sha256:/, '') === ARCHIVE_SHA256);
    if (accepted) break;
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
  if (!accepted) throw new Error('Timed out waiting for the exact retained candidate; no native test started');
  const signed = await rpc(session, 'GetSignedArtifactURL', {
    workflow_run_backend_id: session.workflowRunBackendId,
    workflow_job_run_backend_id: session.workflowJobRunBackendId,
    name: session.name
  });
  core.setSecret(signed.signed_url);
  const response = await fetch(signed.signed_url, {signal: AbortSignal.timeout(180000)});
  if (!response.ok) throw new Error('Candidate read-back failed: HTTP ' + response.status);
  const hash = crypto.createHash('sha256');
  let size = 0;
  for await (const chunk of response.body) {hash.update(chunk); size += chunk.length;}
  if (size !== ARCHIVE_SIZE || hash.digest('hex') !== ARCHIVE_SHA256) throw new Error('Candidate archive read-back mismatch');
  fs.writeFileSync(path.join(folder, 'verified-transfer.json'), JSON.stringify({
    status: 'PASS', runId: session.runId, artifactId: accepted.database_id,
    sha256: ARCHIVE_SHA256, size: ARCHIVE_SIZE
  }), {flag: 'wx'});
  core.info('Exact retained candidate archive uploaded and independently read-back verified.');
};
