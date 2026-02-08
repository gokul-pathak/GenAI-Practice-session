import { OpenRouter } from "@openrouter/sdk";
import readlineSync from "readline-sync";
import { join } from "node:path";

// Load .env safely
try {
  process.loadEnvFile(join(import.meta.dirname, "../.env"));
} catch (e) {
  process.loadEnvFile();
}

// =========================
// OPENROUTER SETUP
// =========================
const openRouter = new OpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

console.log("OPENROUTER_API_KEY:", process.env.OPENROUTER_API_KEY);

// =========================
// CHAT HISTORY (PERSISTED)
// =========================
const chatHistory = [];

// =========================
// SYSTEM INSTRUCTION
// =========================
const SYSTEM_INSTRUCTION = `
You are a helpful AI assistant.
If the user input is a command for a tool, respond **ONLY** with JSON in the following format:
{ "tool": "toolName", "args": { ... } }
Available tools:

1. loveCalculator - Calculate love percentage between a boy and a girl.
   Args: { "boyName": "string", "girlName": "string" }

2. getGithubUser - Get public GitHub user details.
   Args: { "username": "string" }

3. getCryptoPrice - Get current price of a cryptocurrency in USD.
   Args: { "coin": "string" }

**Examples**
User: "Calculate love between Hari and Priya"
AI: { "tool": "loveCalculator", "args": { "boyName": "Hari", "girlName": "Priya" } }

User: "github user octocat"
AI: { "tool": "getGithubUser", "args": { "username": "octocat" } }

Do not include any extra text. Only output JSON.
If input is normal chat, respond normally.
`;

// =========================
// TOOL DEFINITIONS
// =========================
const loveCalculatorTool = {
  name: "loveCalculator",
  description: "Calculate love percentage between a boy and a girl",
  parameters: {
    type: "object",
    properties: {
      boyName: { type: "string", description: "Name of the boy" },
      girlName: { type: "string", description: "Name of the girl" },
    },
    required: ["boyName", "girlName"],
  },
};

const githubUserTool = {
  name: "getGithubUser",
  description: "Get public GitHub user details",
  parameters: {
    type: "object",
    properties: {
      username: { type: "string", description: "GitHub username" },
    },
    required: ["username"],
  },
};

const cryptoPriceTool = {
  name: "getCryptoPrice",
  description: "Get current price of a cryptocurrency in USD",
  parameters: {
    type: "object",
    properties: {
      coin: { type: "string", description: "Cryptocurrency name" },
    },
    required: ["coin"],
  },
};

// =========================
// TOOL IMPLEMENTATIONS
// =========================
function loveCalculator({ boyName, girlName }) {
  const percentage = Math.floor(Math.random() * 101);
  return { boyName, girlName, lovePercentage: percentage };
}

async function getGithubUser({ username }) {
  const res = await fetch(`https://api.github.com/users/${username}`);
  if (res.status === 404) return { error: "User not found" };
  return await res.json();
}

async function getCryptoPrice({ coin }) {
  const res = await fetch(
    `https://api.coingecko.com/api/v3/simple/price?ids=${coin}&vs_currencies=usd`,
  );
  return await res.json();
}

// =========================
// TOOL FUNCTION MAP
// =========================
const toolFunctions = { loveCalculator, getGithubUser, getCryptoPrice };

// =========================
// HELPER TO SEND MESSAGE
// =========================
async function sendMessage(messages) {
  const completion = await openRouter.chat.send({
    chatGenerationParams: {
      model: "openai/gpt-5.2",
      messages,
      stream: false,
    },
  });
  return completion.choices[0].message.content;
}

function preprocessInput(userInput) {
  // Matches: "name1 rw name2" or "name1 and name2"
  const match = userInput.match(/(\w+)\s*(?:rw|and)\s*(\w+)/i);
  if (match) {
    return `Calculate love percentage for boy ${match[1]} and girl ${match[2]}`;
  }
  return userInput;
}

// =========================
// MAIN LOOP
// =========================
async function main() {
  //   const userProblem = readlineSync.question("Ask me anything --> ");
  let userProblem = readlineSync.question("Ask me anything --> ");
  userProblem = preprocessInput(userProblem); // <-- preprocess

  if (userProblem.toLowerCase() === "exit") return console.log("Bye 👋");

  try {
    // Save user message
    chatHistory.push({ role: "user", content: userProblem });

    // Send to AI
    const messages = [
      { role: "system", content: SYSTEM_INSTRUCTION },
      ...chatHistory,
    ];

    const aiResponse = await sendMessage(messages);

    let finalText = aiResponse;

    try {
      const parsed = JSON.parse(aiResponse);

      if (parsed.tool && toolFunctions[parsed.tool]) {
        console.log(`Tool Called: ${parsed.tool}`, parsed.args);

        const toolResult = await toolFunctions[parsed.tool](parsed.args);

        chatHistory.push({
          role: "assistant",
          content: JSON.stringify(toolResult),
        });

        finalText = `Tool Result: ${JSON.stringify(toolResult)}`;
      }
    } catch {
      // Normal chat, not JSON
    }

    console.log("AI:", finalText);
    chatHistory.push({ role: "assistant", content: finalText });

    main();
  } catch (err) {
    console.error("Error:", err.message);
  }
}

main();
