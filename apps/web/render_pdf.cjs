const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

async function generatePDF() {
  const htmlPath = path.resolve(__dirname, '../../docs/submission/submission.html');
  const outputPath = path.resolve(__dirname, '../../docs/submission/EcoSynapse_AI_Darukaa_Submission.pdf');

  console.log('Loading HTML from:', htmlPath);

  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  if (!fs.existsSync(chromePath)) {
    throw new Error(`Chrome not found at ${chromePath}`);
  }

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
  });

  const page = await browser.newPage();
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });

  await page.pdf({
    path: outputPath,
    format: 'A4',
    printBackground: true,
    margin: {
      top: '0mm',
      right: '0mm',
      bottom: '12mm',
      left: '0mm'
    },
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 8pt; color: #64748b; width: 100%; box-sizing: border-box; display: flex; justify-content: space-between; padding: 0 15mm;">
        <span>EcoSynapse AI — Official Submission Document</span>
        <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
      </div>
    `
  });

  await browser.close();
  console.log('PDF successfully generated at:', outputPath);
}

generatePDF().catch(err => {
  console.error('Error generating PDF:', err);
  process.exit(1);
});
