import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { notionUrl, notionId } = await req.json();

    if (!process.env.MANUS_API_KEY) {
        return NextResponse.json({ error: 'Missing MANUS_API_KEY' }, { status: 500 });
    }

    const response = await fetch('https://api.manus.ai/v1/tasks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.MANUS_API_KEY}`,
      },
      body: JSON.stringify({
        prompt: `Please access the Notion page at ${notionUrl} (ID: ${notionId}). Read the 'Agent Instructions' section and execute the tasks listed there. Report back when done.`,
        agentProfile: 'manus-1.6',
        connectors: ['9c27c684-2f4f-4d33-8fcf-51664ea15c00'],
        interactiveMode: false,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || `Manus API error: ${response.statusText}`);
    }

    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Manus API Error:", error);
    return NextResponse.json({ error: error.message || "Failed to trigger Manus agent" }, { status: 500 });
  }
}
