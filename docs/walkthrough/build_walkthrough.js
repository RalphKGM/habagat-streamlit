// Build SolWind_Walkthrough_Script.docx: every part of the app as a screenshot, with a spoken script under it.
// Usage: node build_walkthrough.js parts_sized.json OUT.docx   (parts_sized.json adds px/css_w to parts.json)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, HeadingLevel, AlignmentType, PageBreak,
  Footer, PageNumber, TableOfContents,
} = require("docx");

const [, , partsFile, outFile] = process.argv;
const parts = JSON.parse(fs.readFileSync(partsFile, "utf8"));
const IMG = path.join(__dirname, "img");
const DPI = 96, MAX_W = 6.5 * DPI, MAX_H = 7.4 * DPI, MIN_W = 3.2 * DPI;

const body = [];
body.push(
  new Paragraph({ spacing: { before: 2400, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "SolWind", bold: true, size: 56 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 },
    children: [new TextRun({ text: "Walkthrough Script", size: 32 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Every part of the app, a screenshot, and what to say about it.", size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "https://habagat.streamlit.app", size: 22 })] }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: "Contents", bold: true, size: 32 })] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
);

let page = null, pageNo = 0, partNo = 0;
for (const p of parts) {
  if (p.page !== page) {
    page = p.page; pageNo += 1; partNo = 0;
    body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true,
      children: [new TextRun(`${pageNo}. ${page}`)] }));
  }
  partNo += 1;
  const [pw, ph] = p.px;
  let w = Math.min(MAX_W, Math.max(MIN_W, (p.css_w / 1300) * MAX_W));
  let h = (w * ph) / pw;
  if (h > MAX_H) { w = (w * MAX_H) / h; h = MAX_H; }
  body.push(
    new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true,
      children: [new TextRun(`${pageNo}.${partNo}  ${p.title}`)] }),
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { after: 160 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(IMG, p.file)),
        transformation: { width: Math.round(w), height: Math.round(h) },
        altText: { title: p.title, description: `${page}: ${p.title}`, name: p.file } })] }),
    ...p.script.map((t) => new Paragraph({ spacing: { after: 160, line: 300 }, children: [new TextRun(t)] })),
  );
}

const doc = new Document({
  creator: "SolWind", title: "SolWind Walkthrough Script",
  styles: {
    default: { document: { run: { font: "Calibri", size: 23 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true }, paragraph: { spacing: { before: 0, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true }, paragraph: { spacing: { before: 360, after: 140 }, outlineLevel: 1 } },
    ],
  },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outFile, buf); console.log(outFile, parts.length, "parts"); });
