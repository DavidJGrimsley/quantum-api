const fs = require("node:fs");
const path = require("node:path");

const outputDir = path.resolve(__dirname, "..", "dist-cjs");
const packageJsonPath = path.join(outputDir, "package.json");

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(packageJsonPath, '{\n  "type": "commonjs"\n}\n');