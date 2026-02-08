import { Client } from '@notionhq/client';
import { NextRequest, NextResponse } from 'next/server';

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const databaseId = process.env.NOTION_DATABASE_ID;

// Helper to parse simple markdown to Notion RichText
function parseRichText(text: string): any[] {
  const parts = [];
  let currentText = '';
  let i = 0;

  while (i < text.length) {
    if (text.startsWith('**', i)) {
      if (currentText) parts.push({ text: { content: currentText } });
      currentText = '';
      i += 2;
      const end = text.indexOf('**', i);
      if (end !== -1) {
        parts.push({ text: { content: text.substring(i, end) }, annotations: { bold: true } });
        i = end + 2;
      } else {
        currentText += '**';
        i += 2;
      }
    } else if (text.startsWith('*', i)) { // Simple italic check, might conflict with bullet but we handle bullets outside
      if (currentText) parts.push({ text: { content: currentText } });
      currentText = '';
      i += 1;
      const end = text.indexOf('*', i);
      if (end !== -1) {
        parts.push({ text: { content: text.substring(i, end) }, annotations: { italic: true } });
        i = end + 1;
      } else {
        currentText += '*';
        i += 1;
      }
    } else if (text.startsWith('`', i)) {
        if (currentText) parts.push({ text: { content: currentText } });
        currentText = '';
        i += 1;
        const end = text.indexOf('`', i);
        if (end !== -1) {
            parts.push({ text: { content: text.substring(i, end) }, annotations: { code: true } });
            i = end + 1;
        } else {
            currentText += '`';
            i += 1;
        }
    } else {
      currentText += text[i];
      i++;
    }
  }
  if (currentText) parts.push({ text: { content: currentText } });
  return parts.length > 0 ? parts : [{ text: { content: " " } }];
}

function markdownToBlocks(markdown: string) {
  const blocks: any[] = [];
  const lines = markdown.split('\n');
  let inCodeBlock = false;
  let codeContent = '';
  let codeLanguage = 'plain text';

  for (const line of lines) {
    // Code Block Handling
    if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
            // End of code block
            blocks.push({
                code: {
                    rich_text: [{ text: { content: codeContent.trim() || " " } }],
                    language: "plain text" // Notion strict on languages, defaulting to plain text is safer
                }
            });
            inCodeBlock = false;
            codeContent = '';
        } else {
            // Start of code block
            inCodeBlock = true;
            // Attempt to extract language but fallback to plain text if not supported
            codeLanguage = line.trim().replace('```', '').trim() || 'plain text';
        }
        continue;
    }

    if (inCodeBlock) {
        codeContent += line + '\n';
        continue;
    }

    const trimmed = line.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith('# ')) {
      blocks.push({
        heading_1: {
          rich_text: parseRichText(trimmed.replace('# ', '')),
        },
      });
    } else if (trimmed.startsWith('## ')) {
      blocks.push({
        heading_2: {
          rich_text: parseRichText(trimmed.replace('## ', '')),
        },
      });
    } else if (trimmed.startsWith('### ')) {
      blocks.push({
        heading_3: {
          rich_text: parseRichText(trimmed.replace('### ', '')),
        },
      });
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      blocks.push({
        bulleted_list_item: {
          rich_text: parseRichText(trimmed.replace(/^[-*] /, '')),
        },
      });
    } else if (trimmed.match(/^\d+\. /)) {
        blocks.push({
            numbered_list_item: {
                rich_text: parseRichText(trimmed.replace(/^\d+\. /, '')),
            },
        });
    } else {
      blocks.push({
        paragraph: {
          rich_text: parseRichText(trimmed),
        },
      });
    }
  }
  return blocks;
}

export async function POST(req: NextRequest) {
  try {
    const { title, detailedReport, agentInstructions, tags, priority } = await req.json();

    if (!databaseId) {
      return NextResponse.json({ error: 'Missing NOTION_DATABASE_ID' }, { status: 500 });
    }

    const blocks = markdownToBlocks(detailedReport);

    // Append Agent Instructions
    blocks.push({
      heading_2: {
        rich_text: [{ text: { content: "Agent Instructions" } }]
      }
    });
    blocks.push({
      paragraph: {
        rich_text: [{ text: { content: agentInstructions } }]
      }
    });

    // Append Metadata
    blocks.push({
        heading_3: {
            rich_text: [{ text: { content: "Metadata" } }]
        }
    });
    blocks.push({
        paragraph: {
            rich_text: [{ text: { content: `Tags: ${tags.join(', ')} | Priority: ${priority}` } }]
        }
    });

    // Chunking Logic (Max 100 blocks per request)
    const MAX_BLOCKS = 100;
    const initialBlocks = blocks.slice(0, MAX_BLOCKS);
    const remainingBlocks = blocks.slice(MAX_BLOCKS);

    const payload: any = {
        parent: { database_id: databaseId },
        properties: {
            "Name": {
                title: [
                    { text: { content: title } }
                ]
            }
        },
        children: initialBlocks
    };

    const response = await notion.pages.create(payload);

    // If there are remaining blocks, append them in batches
    if (remainingBlocks.length > 0) {
        let offset = 0;
        while (offset < remainingBlocks.length) {
            const batch = remainingBlocks.slice(offset, offset + MAX_BLOCKS);
            await notion.blocks.children.append({
                block_id: response.id,
                children: batch
            });
            offset += MAX_BLOCKS;
        }
    }

    return NextResponse.json({ url: (response as any).url, id: response.id });
  } catch (error: any) {
    console.error("Notion API Error:", error);
    return NextResponse.json({ error: error.message || "Failed to create Notion page" }, { status: 500 });
  }
}
