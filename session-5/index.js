import { OpenAI } from "openai";

import { join } from "node:path";

// Load .env safely
try {
  process.loadEnvFile(join(import.meta.dirname, "../.env"));
} catch (e) {
  process.loadEnvFile();
}


const client = new OpenAI({
    apiKey: 'OPENAI_API_KEY',
    baseURL: process.env.BASE_URL_LLM
});


const response = await client.chat.completions.create({
    model: 'gemma3-qat:270M-F16',
    //chatml prompt format
    messages: [{role: 'user', content: 'hey, i am google'}],
})

console.log(`response: `, response.choices[0].message.content)