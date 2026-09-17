// Contract checks for the composite actions under actions/.
//
// These actions are consumed by other repositories, so a mistake here surfaces
// as a broken pipeline somewhere else. The checks are deliberately cheap and
// need no Azure credentials:
//
//   1. every action.yml parses and declares name/description/runs.using
//   2. every ${{ inputs.X }} reference names a declared input, and every
//      declared input is referenced -- drift in either direction fails, because
//      GitHub silently IGNORES an unknown key passed in `with:` rather than
//      erroring
//   3. no ${{ ... }} expression appears inside a script body: inputs reach the
//      script through env only, so an input is always data and never code
//   4. the module path each action imports exists in this repository
//   5. the embedded PowerShell parses, and every Azure.Iot.Sdk.Test cmdlet it
//      calls exists with the parameters it passes (delegated to
//      tests/Validate-ActionScripts.ps1)
//
// Usage: node tests/validate-actions.mjs
import { readFileSync, readdirSync, existsSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { load } from 'js-yaml';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const actionsRoot = join(repoRoot, 'actions');

const failures = [];
const fail = (action, message) => failures.push(`${action}: ${message}`);

// Non-greedy up to the first '}}', so an expression containing braces -- say
// ${{ format('{0}', inputs.x) }} -- is still matched. A [^}]* body would stop
// at the '}' of '{0}' and match nothing at all.
const expressions = (text) => [...String(text).matchAll(/\$\{\{([\s\S]*?)\}\}/g)].map((m) => m[1].trim());

// Expression OPENERS. The invariant for a script body is simply that it
// contains none, so count openers rather than trusting any expression grammar:
// a body whose expression this file cannot parse must fail, not pass.
const expressionOpeners = (text) => (String(text).match(/\$\{\{/g) ?? []).length;

// Every step body the action runs, with the key that carried it.
const scriptBodies = (step) => {
  const bodies = [];
  if (typeof step.run === 'string') bodies.push(['run', step.run]);
  if (step.with && typeof step.with.inlineScript === 'string') bodies.push(['with.inlineScript', step.with.inlineScript]);
  return bodies;
};

const actionDirs = existsSync(actionsRoot)
  ? readdirSync(actionsRoot, { withFileTypes: true }).filter((e) => e.isDirectory()).map((e) => e.name)
  : [];

if (actionDirs.length === 0) {
  console.error('No actions found under actions/.');
  process.exit(1);
}

const scriptsToParse = [];

for (const name of actionDirs) {
  const file = join(actionsRoot, name, 'action.yml');
  if (!existsSync(file)) {
    fail(name, 'has no action.yml (GitHub only recognises action.yml or action.yaml)');
    continue;
  }

  const text = readFileSync(file, 'utf8');
  let doc;
  try {
    doc = load(text);
  } catch (err) {
    fail(name, `action.yml is not valid YAML: ${err.message}`);
    continue;
  }

  for (const key of ['name', 'description', 'runs']) {
    if (!doc[key]) fail(name, `action.yml has no '${key}'`);
  }
  if (doc.runs && doc.runs.using !== 'composite') {
    fail(name, `runs.using is '${doc.runs?.using}', expected 'composite'`);
  }

  const declared = new Set(Object.keys(doc.inputs ?? {}));
  const referenced = new Set();

  for (const expr of expressions(text)) {
    // Anywhere in the expression, not just at its start: an input used inside a
    // call -- ${{ format('{0}', inputs.x) }} -- is still a reference, and
    // missing it would wrongly report the input as declared-but-unused.
    for (const m of expr.matchAll(/\binputs\.([A-Za-z0-9_-]+)/g)) {
      referenced.add(m[1]);
      if (!declared.has(m[1])) fail(name, `references undeclared input '${m[1]}'`);
    }
  }

  for (const input of declared) {
    if (!referenced.has(input)) {
      fail(name, `declares input '${input}' but never uses it -- callers passing it would be silently ignored`);
    }
  }

  for (const [index, step] of (doc.runs?.steps ?? []).entries()) {
    for (const [key, body] of scriptBodies(step)) {
      const openers = expressionOpeners(body);
      if (openers > 0) {
        const inlined = expressions(body);
        const detail = inlined.length > 0
          ? inlined.map((e) => `\${{ ${e} }}`).join(', ')
          : `${openers} expression opener(s)`;
        fail(name, `step ${index} (${key}) interpolates ${detail} into the script body; pass it through env: instead`);
      }
      if (key === 'run' && !step.shell) {
        fail(name, `step ${index} has 'run' without 'shell' (composite steps require an explicit shell)`);
      }
      scriptsToParse.push({ action: name, key, body, shell: step.shell ?? 'pwsh' });
    }

    for (const [envName, envValue] of Object.entries(step.env ?? {})) {
      if (!/MODULE$/.test(envName)) continue;
      const relative = String(envValue).replace(/\$\{\{[\s\S]*?\}\}\/?/, '');
      const modulePath = join(actionsRoot, name, relative);
      if (!existsSync(modulePath)) {
        fail(name, `${envName} points at '${relative}', which does not exist in this repository`);
      }
    }
  }
}

// PowerShell bodies: syntax + cmdlet/parameter drift against the module.
const pwshBodies = scriptsToParse.filter((s) => s.shell === 'pwsh' || s.key === 'with.inlineScript');
if (pwshBodies.length > 0) {
  const stage = mkdtempSync(join(tmpdir(), 'action-scripts-'));
  try {
    const written = pwshBodies.map((s, i) => {
      const path = join(stage, `${s.action}.${i}.ps1`);
      writeFileSync(path, s.body);
      return path;
    });
    const pwsh = spawnSync('pwsh', ['-NoProfile', '-File', join(repoRoot, 'tests', 'Validate-ActionScripts.ps1'), ...written], {
      encoding: 'utf8',
    });
    if (pwsh.error && pwsh.error.code === 'ENOENT') {
      failures.push('pwsh is not installed, so the embedded PowerShell was not validated');
    } else {
      process.stdout.write(pwsh.stdout ?? '');
      process.stderr.write(pwsh.stderr ?? '');
      if (pwsh.status !== 0) failures.push('embedded PowerShell validation failed (see above)');
    }
  } finally {
    rmSync(stage, { recursive: true, force: true });
  }
}

if (failures.length > 0) {
  console.error(`\n${failures.length} problem(s) found:`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

console.log(`OK: ${actionDirs.length} action(s) validated.`);
