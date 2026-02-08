import { google } from '@ai-sdk/google';
import { streamObject } from 'ai';
import { z } from 'zod';

// Using 'gemini-flash-latest' as it has valid free tier access
const model = google('gemini-flash-latest');

export const maxDuration = 60;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamObject({
    model,
    schema: z.object({
      title: z.string().describe("The concise title of the task for the Notion page."),
      detailedReport: z.string().describe("A comprehensive Markdown report with headers, lists, and tables explaining the plan."),
      agentInstructions: z.string().describe("A set of concise, actionable instructions for the Manus agent to execute, without background noise."),
      tags: z.array(z.string()).describe("A list of tags for categorization (e.g., 'Research', 'Dev', 'Marketing')."),
      priority: z.enum(['High', 'Medium', 'Low']).describe("The priority level of the task.")
    }),
    system: `You are an advanced strategic advisor (Think Tank). Your goal is not to execute directly, but to generate a detailed, structured execution plan for a user request.
    This plan will be stored in Notion and executed by the Manus agent.

    Guidelines:
    1. Analyze the user's intent.
    2. Create a 'Detailed Report' in Markdown. This is for human reading. Include background, steps, and expected outcome.
    3. Create 'Agent Instructions' specifically for the Manus agent. These should be imperative, clear actions (e.g., 'Go to url...', 'Search for...', 'Download file...').
    4. Do not include steps that require physical interaction or internal network access unless specified.
    5. Output must be valid JSON matching the schema.
    6. **Language:** Output primarily in the language of the user's request. If the user asks in Chinese, the 'Detailed Report' and 'Title' MUST be in Chinese. The 'Agent Instructions' can be in English or Chinese (Manus understands both), but English is preferred for tool precision if possible, otherwise Chinese is fine.`,
    messages,
  });

  return result.toTextStreamResponse();
}
