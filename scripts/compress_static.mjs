import { promises as fs } from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const TARGET_DIRS = ['apps/admin/build', 'apps/pos/build'];
const EXTENSIONS_TO_COMPRESS = new Set([
	'.html',
	'.js',
	'.css',
	'.svg',
	'.json',
	'.txt',
]);
const MIN_SIZE_BYTES = 512;

async function getAllFiles(dirPath) {
	let entries;
	try {
		entries = await fs.readdir(dirPath, { withFileTypes: true });
	} catch {
		return [];
	}

	const files = [];
	for (const entry of entries) {
		const fullPath = path.join(dirPath, entry.name);
		if (entry.isDirectory()) {
			files.push(...(await getAllFiles(fullPath)));
		} else if (entry.isFile()) {
			const ext = path.extname(entry.name);
			if (
				EXTENSIONS_TO_COMPRESS.has(ext) &&
				!entry.name.endsWith('.br') &&
				!entry.name.endsWith('.gz')
			) {
				files.push(fullPath);
			}
		}
	}
	return files;
}

function formatBytes(bytes) {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

async function compressFile(filePath) {
	const content = await fs.readFile(filePath);
	if (content.length < MIN_SIZE_BYTES) {
		return null;
	}

	// Brotli Level 11 (Maximum compression quality for static pre-compression)
	const brotliBuffer = zlib.brotliCompressSync(content, {
		params: {
			[zlib.constants.BROTLI_PARAM_QUALITY]: 11,
		},
	});

	// Gzip Level 9 (Maximum compression quality)
	const gzipBuffer = zlib.gzipSync(content, {
		level: 9,
	});

	await Promise.all([
		fs.writeFile(`${filePath}.br`, brotliBuffer),
		fs.writeFile(`${filePath}.gz`, gzipBuffer),
	]);

	return {
		original: content.length,
		brotli: brotliBuffer.length,
		gzip: gzipBuffer.length,
	};
}

async function main() {
	console.log(
		'==> [Pre-compression] Compressing static SPA assets with Brotli & Gzip...',
	);
	let totalFiles = 0;
	let totalOriginal = 0;
	let totalBrotli = 0;
	let totalGzip = 0;

	for (const relDir of TARGET_DIRS) {
		const absDir = path.resolve(process.cwd(), relDir);
		const files = await getAllFiles(absDir);

		if (files.length === 0) {
			console.log(`    • ${relDir}: No built files found (run build first)`);
			continue;
		}

		let dirOriginal = 0;
		let dirBrotli = 0;
		let dirGzip = 0;
		let dirCount = 0;

		for (const file of files) {
			const res = await compressFile(file);
			if (res) {
				dirCount++;
				dirOriginal += res.original;
				dirBrotli += res.brotli;
				dirGzip += res.gzip;
			}
		}

		totalFiles += dirCount;
		totalOriginal += dirOriginal;
		totalBrotli += dirBrotli;
		totalGzip += dirGzip;

		const brSavings =
			dirOriginal > 0
				? (((dirOriginal - dirBrotli) / dirOriginal) * 100).toFixed(1)
				: 0;
		console.log(
			`    • ${relDir}: ${dirCount} files compressed | ${formatBytes(dirOriginal)} -> ${formatBytes(dirBrotli)} (Brotli -${brSavings}%)`,
		);
	}

	if (totalFiles > 0) {
		const totalSavings = (
			((totalOriginal - totalBrotli) / totalOriginal) *
			100
		).toFixed(1);
		console.log(
			`==> Pre-compression complete: ${totalFiles} assets | Total: ${formatBytes(totalOriginal)} -> Brotli ${formatBytes(totalBrotli)} (-${totalSavings}%) | Gzip ${formatBytes(totalGzip)}`,
		);
	}
}

main().catch((err) => {
	console.error('Pre-compression failed:', err);
	process.exit(1);
});
