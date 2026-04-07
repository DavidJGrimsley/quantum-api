#!/usr/bin/env node
// Wrapper that temporarily adds src/package.json {"type":"commonjs"} so that
// tsc with module:NodeNext emits CJS instead of ESM (the root package.json
// uses "type":"module").  The marker file is removed even on failure.

const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const srcPkg = path.join(root, "src", "package.json");
const tsc = require.resolve("typescript/bin/tsc");

fs.writeFileSync(srcPkg, '{\n  "type": "commonjs"\n}\n');
try {
  execFileSync(tsc, ["-p", "tsconfig.build.cjs.json"], { cwd: root, stdio: "inherit" });
} finally {
  fs.rmSync(srcPkg, { force: true });
}
