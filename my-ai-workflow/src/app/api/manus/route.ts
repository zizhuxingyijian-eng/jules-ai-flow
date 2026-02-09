import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { notionUrl, notionId } = await req.json();

    if (!notionUrl || !notionId) {
      return NextResponse.json({ error: 'Missing notionUrl or notionId' }, { status: 400 });
    }

    const apiKey = process.env.MANUS_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Missing MANUS_API_KEY' }, { status: 500 });
    }

    // Manus API Payload
    // According to whitepaper: needs prompt, agentProfile="manus-1.6", connectors with specific Notion UUID
    const payload = {
      prompt: `Please access the Notion page at ${notionUrl}. Read the content, specifically the 'Agent Instructions' section, and execute the tasks listed there sequentially. The context is an enterprise workflow execution.`,
      agentProfile: "manus-1.6",
      connectors: [
        {
          id: "9c27c684-2f4f-4d33-8fcf-51664ea15c00", // Fixed UUID for Notion Connector
          config: {}
        }
      ],
      interactiveMode: false
    };

    const response = await fetch('https://api.manus.ai/v1/tasks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json({ error: `Manus API error: ${response.status} - ${errorText}` }, { status: response.status });
    }

    const data = await response.json();

    // Return the task details
    return NextResponse.json(data);

  } catch (error: any) {
    console.error("Manus API Route Error:", error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
