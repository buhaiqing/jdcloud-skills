#!/usr/bin/env node
/**
 * mermaid-lint — Mermaid syntax linter for topology reports.
 *
 * Extracts ```mermaid blocks from Markdown files and validates each
 * using the official mermaid.parse() API.
 *
 * Usage:
 *   node lint.mjs "reports/*.md"
 *   node lint.mjs "reports/*.mermaid.md"
 *
 * Exit codes:
 *   0 — all blocks valid (or no mermaid blocks found)
 *   1 — one or more blocks have syntax errors
 *   2 — fatal error (missing deps, file I/O)
 */
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// ── Bootstrap DOM environment (required by mermaid.parse) ──
const jsdom = require('jsdom');
const dompurify = require('dompurify');

const window = new jsdom.JSDOM('').window;
globalThis.window = window;
globalThis.document = window.document;
globalThis.location = window.location;

const purify = dompurify(window);
globalThis.DOMPurify = purify;

// mermaid is ESM-only; use dynamic import
const mermaid = await import('mermaid');
const M = mermaid.default || mermaid;
M.initialize({ startOnLoad: false, maxTextSize: 100000 });

// ── I/O ──
const { readFileSync } = require('fs');
const { globSync } = require('glob');

// ── Helpers ──

function extractMermaidBlocks(content) {
    const blocks = [];
    const regex = /```mermaid\n([\s\S]*?)```/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
        const startOffset = match.index;
        const lineNumber = content.substring(0, startOffset).split('\n').length;
        blocks.push({ code: match[1].trim(), line: lineNumber });
    }
    return blocks;
}

async function lintFile(filePath) {
    const content = readFileSync(filePath, 'utf-8');
    const blocks = extractMermaidBlocks(content);
    if (blocks.length === 0) return { file: filePath, blocks: 0, errors: [] };

    const errors = [];
    for (const block of blocks) {
        try {
            await M.parse(block.code);
        } catch (e) {
            errors.push({
                line: block.line,
                error: (e.message || 'Unknown parse error').substring(0, 300),
            });
        }
    }
    return { file: filePath, blocks: blocks.length, errors };
}

// ── Main ──

async function main() {
    const patterns = process.argv.slice(2);
    if (patterns.length === 0) {
        console.error('Usage: node lint.mjs <glob-pattern> [glob-pattern...]');
        process.exit(2);
    }

    let totalErrors = 0;
    let totalFiles = 0;
    let totalBlocks = 0;

    for (const pattern of patterns) {
        const files = globSync(pattern);
        for (const file of files) {
            totalFiles++;
            const result = await lintFile(file);
            totalBlocks += result.blocks;

            if (result.errors.length > 0) {
                totalErrors += result.errors.length;
                console.error(`\n❌ ${file}: ${result.errors.length} error(s)`);
                for (const err of result.errors) {
                    console.error(`   Line ${err.line}: ${err.error.substring(0, 200)}`);
                }
            } else if (result.blocks > 0) {
                console.log(`✅ ${file}: ${result.blocks} block(s) valid`);
            }
        }
    }

    console.log(`\n📊 Summary: ${totalFiles} files, ${totalBlocks} mermaid blocks, ${totalErrors} error(s)`);
    process.exit(totalErrors > 0 ? 1 : 0);
}

main().catch((e) => {
    console.error('Fatal:', e.message);
    process.exit(2);
});
