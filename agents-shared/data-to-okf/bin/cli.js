#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const SKILL_ROOT = path.resolve(__dirname, "..");
const SKILL_NAME = require(path.join(SKILL_ROOT, "package.json")).name;

// Only these are the actual Agent Skill contents (SKILL.md + spec dirs).
// Everything else in the repo (.git, node_modules, package.json, bin/,
// .gitignore, lockfiles) is npm/git packaging, not part of the skill itself.
const INCLUDE = ["SKILL.md", "scripts", "references", "assets", "README.md", "LICENSE"];

function usage() {
  console.log(`
data-to-okf installer

Usage:
  npx github:rajivmehtaflex/data-to-okf install [options]

Options:
  --project        Install into <cwd>/.claude/skills/${SKILL_NAME}/ (this project only)
                    instead of the default personal ~/.claude/skills/${SKILL_NAME}/
  --target <path>   Install into an arbitrary directory (for clients other than
                    Claude Code — check https://agentskills.io/clients for the
                    skills directory your client expects)
  --help            Show this help

Examples:
  npx github:rajivmehtaflex/data-to-okf install
  npx github:rajivmehtaflex/data-to-okf install --project
  npx github:rajivmehtaflex/data-to-okf install --target ./.cursor/skills/${SKILL_NAME}
`);
}

function parseArgs(argv) {
  const args = { command: null, project: false, target: null, help: false };
  const rest = [...argv];
  if (rest[0] && !rest[0].startsWith("-")) {
    args.command = rest.shift();
  }
  while (rest.length) {
    const flag = rest.shift();
    if (flag === "--project") args.project = true;
    else if (flag === "--target") args.target = rest.shift();
    else if (flag === "--help" || flag === "-h") args.help = true;
    else {
      console.error(`Unknown option: ${flag}`);
      process.exitCode = 1;
      return args;
    }
  }
  return args;
}

function resolveTarget(args) {
  if (args.target) return path.resolve(args.target);
  if (args.project) return path.join(process.cwd(), ".claude", "skills", SKILL_NAME);
  return path.join(os.homedir(), ".claude", "skills", SKILL_NAME);
}

function install(args) {
  const target = resolveTarget(args);

  if (path.resolve(target) === path.resolve(SKILL_ROOT)) {
    console.log(`Already installed here: ${target} (nothing to copy).`);
    return;
  }

  fs.mkdirSync(target, { recursive: true });
  for (const entry of INCLUDE) {
    const src = path.join(SKILL_ROOT, entry);
    if (!fs.existsSync(src)) continue;
    const dest = path.join(target, entry);
    fs.cpSync(src, dest, { recursive: true });
  }

  console.log(`✓ Installed ${SKILL_NAME} to ${target}\n`);
  console.log('Now ask your agent something like: "Bundle ~/Desktop/ClientY into an OKF bundle."');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (process.exitCode) return;
  if (args.help || !args.command) {
    usage();
    return;
  }
  if (args.command !== "install") {
    console.error(`Unknown command: ${args.command}`);
    usage();
    process.exitCode = 1;
    return;
  }
  install(args);
}

main();
