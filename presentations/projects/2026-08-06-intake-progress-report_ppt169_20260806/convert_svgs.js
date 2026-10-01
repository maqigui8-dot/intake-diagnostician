const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const svgDir = path.join(__dirname, 'svg_output');
const pngDir = path.join(__dirname, 'png_output');
const files = fs.readdirSync(svgDir).filter(f => f.endsWith('.svg')).sort();

fs.mkdirSync(pngDir, { recursive: true });

async function convertAll() {
  for (const file of files) {
    const svgPath = path.join(svgDir, file);
    const pngPath = path.join(pngDir, file.replace('.svg', '.png'));
    console.log(`Converting ${file}...`);
    await sharp(svgPath).png().toFile(pngPath);
    console.log(`  -> ${pngPath}`);
  }
  console.log(`\nDone! ${files.length} SVGs converted.`);
}

convertAll().catch(e => { console.error(e); process.exit(1); });
