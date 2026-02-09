import { NextRequest, NextResponse } from 'next/server';
import { Client } from '@notionhq/client';
import { z } from 'zod';

const notion = new Client({
  auth: process.env.NOTION_API_KEY,
});

const databaseId = process.env.NOTION_DATABASE_ID;

// Define schema for incoming data (matches Gemini Zod output)
const RequestSchema = z.object({
  title: z.string(),
  detailedReport: z.string(),
  agentInstructions: z.string(),
  tags: z.array(z.string()),
  priority: z.enum(['High', 'Medium', 'Low'])
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const data = RequestSchema.parse(body);

    if (!databaseId) {
      throw new Error("NOTION_DATABASE_ID is not configured");
    }

    // 1. Convert Markdown Report to Notion Blocks (Simplified)
    // For a robust implementation, we would need a full AST parser like remark -> notion-blocks.
    // Here we implement a basic parser for headings, lists, and paragraphs.
    const reportBlocks = parseMarkdownToBlocks(data.detailedReport);

    // 2. Add Agent Instructions section
    const instructionBlocks = [
      {
        object: 'block',
        type: 'heading_2',
        heading_2: {
          rich_text: [{ type: 'text', text: { content: 'Agent Instructions (Manus)' } }],
        },
      },
      {
        object: 'block',
        type: 'code',
        code: {
          rich_text: [{ type: 'text', text: { content: data.agentInstructions } }],
          language: 'plain text'
        },
      }
    ];

    const allChildren = [...reportBlocks, ...instructionBlocks];

    // Notion allows max 100 blocks per request. We must chunk it.
    // Actually, creating a page accepts children.
    // If children > 100, we create page first with 100, then append.

    const first100 = allChildren.slice(0, 100);
    const remaining = allChildren.slice(100);

    // Create Page
    const response = await notion.pages.create({
      parent: { database_id: databaseId },
      properties: {
        Name: {
          title: [
            {
              text: {
                content: data.title,
              },
            },
          ],
        },
        Priority: {
          select: {
            name: data.priority,
          },
        },
        Tags: {
          multi_select: data.tags.map(tag => ({ name: tag })),
        },
        Status: {
           status: {
               name: "Not Started"
           }
        }
      },
      children: first100 as any[], // Typing for Notion SDK blocks is complex
    });

    // Append remaining blocks if any
    if (remaining.length > 0) {
      // Chunk remaining into 100s
      for (let i = 0; i < remaining.length; i += 100) {
         const chunk = remaining.slice(i, i + 100);
         await notion.blocks.children.append({
             block_id: response.id,
             children: chunk as any[]
         });
      }
    }

    return NextResponse.json({
        success: true,
        url: (response as any).url,
        id: response.id
    });

  } catch (error: any) {
    console.error("Notion API Error:", error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}

// --- Helper: Basic Markdown Parser ---
// This is a simplified parser. In production, use a library.
function parseMarkdownToBlocks(markdown: string): any[] {
  const lines = markdown.split('\n');
  const blocks: any[] = [];

  let currentListType: 'bulleted_list_item' | 'numbered_list_item' | null = null;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Headings
    if (trimmed.startsWith('# ')) {
      blocks.push({
        object: 'block',
        type: 'heading_1',
        heading_1: { rich_text: [{ type: 'text', text: { content: trimmed.substring(2) } }] }
      });
      currentListType = null;
    } else if (trimmed.startsWith('## ')) {
      blocks.push({
        object: 'block',
        type: 'heading_2',
        heading_2: { rich_text: [{ type: 'text', text: { content: trimmed.substring(3) } }] }
      });
      currentListType = null;
    } else if (trimmed.startsWith('### ')) {
      blocks.push({
        object: 'block',
        type: 'heading_3',
        heading_3: { rich_text: [{ type: 'text', text: { content: trimmed.substring(4) } }] }
      });
      currentListType = null;
    }
    // Lists
    else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      blocks.push({
        object: 'block',
        type: 'bulleted_list_item',
        bulleted_list_item: { rich_text: parseRichText(trimmed.substring(2)) }
      });
    }
    // Tables (Very basic detection, converting to code block for preservation)
    else if (trimmed.startsWith('|')) {
        blocks.push({
            object: 'block',
            type: 'code',
            code: {
                rich_text: [{ type: 'text', text: { content: trimmed } }],
                language: 'markdown' // Use markdown syntax highlighting for table rows
            }
        });
    }
    // Paragraphs
    else {
      blocks.push({
        object: 'block',
        type: 'paragraph',
        paragraph: { rich_text: parseRichText(trimmed) }
      });
    }
  }

  return blocks;
}

function parseRichText(text: string): any[] {
    // Very basic bold handling: **text**
    const parts = text.split(/(\*\*.*?\*\*)/);
    return parts.map(part => {
        if (part.startsWith('**') && part.endsWith('**')) {
            return {
                type: 'text',
                text: { content: part.slice(2, -2) },
                annotations: { bold: true }
            };
        }
        return {
            type: 'text',
            text: { content: part }
        };
    }).filter(p => p.text.content.length > 0);
}
