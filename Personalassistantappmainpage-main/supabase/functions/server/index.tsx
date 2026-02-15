import { Hono } from "npm:hono";
import { cors } from "npm:hono/cors";
import { logger } from "npm:hono/logger";
import * as kv from "./kv_store.tsx";

const app = new Hono();

// Enable logger
app.use('*', logger(console.log));

// Enable CORS for all routes and methods
app.use(
  "/*",
  cors({
    origin: "*",
    allowHeaders: ["Content-Type", "Authorization"],
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    exposeHeaders: ["Content-Length"],
    maxAge: 600,
  }),
);

// Helper function to call LLM based on provider
async function callLLM(provider: string, apiKey: string, systemPrompt: string, userPrompt: string) {
  switch (provider) {
    case 'openai':
      return await callOpenAI(apiKey, systemPrompt, userPrompt);
    case 'google':
      return await callGemini(apiKey, systemPrompt, userPrompt);
    case 'claude':
      return await callClaude(apiKey, systemPrompt, userPrompt);
    case 'other':
      // For 'other', default to OpenAI-compatible API
      return await callOpenAI(apiKey, systemPrompt, userPrompt);
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}

async function callOpenAI(apiKey: string, systemPrompt: string, userPrompt: string) {
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ]
    })
  });

  if (!response.ok) {
    const errorData = await response.text();
    throw new Error(`OpenAI API error: ${errorData}`);
  }

  const data = await response.json();
  return data.choices[0]?.message?.content || "No response available";
}

async function callGemini(apiKey: string, systemPrompt: string, userPrompt: string) {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: `${systemPrompt}\n\n${userPrompt}`
          }]
        }]
      })
    }
  );

  if (!response.ok) {
    const errorData = await response.text();
    throw new Error(`Gemini API error: ${errorData}`);
  }

  const data = await response.json();
  return data.candidates[0]?.content?.parts[0]?.text || "No response available";
}

async function callClaude(apiKey: string, systemPrompt: string, userPrompt: string) {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01"
    },
    body: JSON.stringify({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: 1024,
      system: systemPrompt,
      messages: [
        { role: "user", content: userPrompt }
      ]
    })
  });

  if (!response.ok) {
    const errorData = await response.text();
    throw new Error(`Claude API error: ${errorData}`);
  }

  const data = await response.json();
  return data.content[0]?.text || "No response available";
}

// Health check endpoint
app.get("/make-server-7ea82c69/health", (c) => {
  return c.json({ status: "ok" });
});

// Get all meetings
app.get("/make-server-7ea82c69/meetings", async (c) => {
  try {
    const meetings = await kv.getByPrefix("meeting:");
    // Sort by date descending
    const sorted = meetings.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    return c.json({ meetings: sorted });
  } catch (error) {
    console.error("Error fetching meetings:", error);
    return c.json({ error: "Failed to fetch meetings", details: String(error) }, 500);
  }
});

// Create a new meeting
app.post("/make-server-7ea82c69/meetings", async (c) => {
  try {
    const body = await c.req.json();
    const { title, speakers, transcript, nextSteps } = body;
    
    const meetingId = crypto.randomUUID();
    const meeting = {
      id: meetingId,
      title,
      date: new Date().toISOString(),
      speakers: speakers || [],
      transcript,
      nextSteps: nextSteps || "",
      duration: body.duration || 0
    };
    
    await kv.set(`meeting:${meetingId}`, meeting);
    return c.json({ meeting });
  } catch (error) {
    console.error("Error creating meeting:", error);
    return c.json({ error: "Failed to create meeting", details: String(error) }, 500);
  }
});

// Update meeting with AI analysis
app.put("/make-server-7ea82c69/meetings/:id/analyze", async (c) => {
  try {
    const meetingId = c.req.param("id");
    const meeting = await kv.get(`meeting:${meetingId}`);
    
    if (!meeting) {
      return c.json({ error: "Meeting not found" }, 404);
    }
    
    const provider = await kv.get("settings:llm_provider");
    if (!provider) {
      return c.json({ error: "LLM provider not configured" }, 400);
    }
    
    const apiKey = await kv.get(`settings:${provider}_api_key`);
    if (!apiKey) {
      return c.json({ error: "LLM API key not configured" }, 400);
    }
    
    // Call LLM API to analyze transcript
    const nextSteps = await callLLM(provider, apiKey, 
      "You are an AI assistant that analyzes meeting transcripts. Extract key action items, decisions, and next steps. Format your response as a clear, bulleted list.",
      `Analyze this meeting transcript and provide next steps:\n\n${meeting.transcript}`
    );
    
    meeting.nextSteps = nextSteps;
    await kv.set(`meeting:${meetingId}`, meeting);
    
    return c.json({ meeting });
  } catch (error) {
    console.error("Error analyzing meeting:", error);
    return c.json({ error: "Failed to analyze meeting", details: String(error) }, 500);
  }
});

// Get all journal entries
app.get("/make-server-7ea82c69/journal", async (c) => {
  try {
    const entries = await kv.getByPrefix("journal:");
    const sorted = entries.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    return c.json({ entries: sorted });
  } catch (error) {
    console.error("Error fetching journal entries:", error);
    return c.json({ error: "Failed to fetch journal entries", details: String(error) }, 500);
  }
});

// Create journal entry
app.post("/make-server-7ea82c69/journal", async (c) => {
  try {
    const body = await c.req.json();
    const { entry } = body;
    
    const entryId = crypto.randomUUID();
    const journalEntry = {
      id: entryId,
      date: new Date().toISOString(),
      entry,
      aiSuggestions: ""
    };
    
    await kv.set(`journal:${entryId}`, journalEntry);
    return c.json({ journalEntry });
  } catch (error) {
    console.error("Error creating journal entry:", error);
    return c.json({ error: "Failed to create journal entry", details: String(error) }, 500);
  }
});

// Get AI suggestions for journal entry
app.put("/make-server-7ea82c69/journal/:id/optimize", async (c) => {
  try {
    const entryId = c.req.param("id");
    const journalEntry = await kv.get(`journal:${entryId}`);
    
    if (!journalEntry) {
      return c.json({ error: "Journal entry not found" }, 404);
    }
    
    const provider = await kv.get("settings:llm_provider");
    if (!provider) {
      return c.json({ error: "LLM provider not configured" }, 400);
    }
    
    const apiKey = await kv.get(`settings:${provider}_api_key`);
    if (!apiKey) {
      return c.json({ error: "LLM API key not configured" }, 400);
    }
    
    // Call LLM API for optimization suggestions
    const suggestions = await callLLM(provider, apiKey, 
      "You are a personal productivity coach. Analyze journal entries and provide actionable, optimized steps to help the user achieve their goals. Be specific, encouraging, and practical.",
      `Based on this journal entry, provide optimized next steps:\n\n${journalEntry.entry}`
    );
    
    journalEntry.aiSuggestions = suggestions;
    await kv.set(`journal:${entryId}`, journalEntry);
    
    return c.json({ journalEntry });
  } catch (error) {
    console.error("Error optimizing journal entry:", error);
    return c.json({ error: "Failed to optimize journal entry", details: String(error) }, 500);
  }
});

// Summarize voice transcript for journal entry
app.post("/make-server-7ea82c69/journal/summarize", async (c) => {
  try {
    const { transcript } = await c.req.json();
    
    if (!transcript) {
      return c.json({ error: "Transcript is required" }, 400);
    }
    
    const provider = await kv.get("settings:llm_provider");
    if (!provider) {
      return c.json({ error: "LLM provider not configured. Please configure your LLM settings first." }, 400);
    }
    
    const apiKey = await kv.get(`settings:${provider}_api_key`);
    if (!apiKey) {
      return c.json({ error: "LLM API key not configured. Please add your API key in settings." }, 400);
    }
    
    // Call LLM API to generate summary
    const summary = await callLLM(provider, apiKey, 
      "You are a helpful assistant that summarizes voice journal entries. Take the raw transcript and create a clear, concise journal entry that captures the main points, thoughts, and feelings expressed. Keep the first-person perspective and maintain the personal nature of the entry.",
      `Please summarize this voice journal transcript into a well-written journal entry:\n\n${transcript}`
    );
    
    return c.json({ summary });
  } catch (error) {
    console.error("Error summarizing transcript:", error);
    return c.json({ error: "Failed to summarize transcript", details: String(error) }, 500);
  }
});

// Save LLM API key
app.post("/make-server-7ea82c69/settings/api-key", async (c) => {
  try {
    const { provider, apiKey } = await c.req.json();
    
    // Save provider-specific API key
    await kv.set(`settings:${provider}_api_key`, apiKey);
    
    // Save the active provider
    await kv.set("settings:llm_provider", provider);
    
    return c.json({ success: true });
  } catch (error) {
    console.error("Error saving API key:", error);
    return c.json({ error: "Failed to save API key", details: String(error) }, 500);
  }
});

// Get API key status
app.get("/make-server-7ea82c69/settings/api-key", async (c) => {
  try {
    const provider = c.req.query("provider") || "openai";
    const apiKey = await kv.get(`settings:${provider}_api_key`);
    return c.json({ configured: !!apiKey });
  } catch (error) {
    console.error("Error checking API key:", error);
    return c.json({ error: "Failed to check API key", details: String(error) }, 500);
  }
});

Deno.serve(app.fetch);