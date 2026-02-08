import { GoogleGenerativeAI } from "@google/generative-ai";
import readlineSync from "readline-sync";
import { join } from "node:path";

// Load .env safely
try {
  process.loadEnvFile(join(import.meta.dirname, "../.env"));
} catch (e) {
  process.loadEnvFile();
}

const ai = new GoogleGenerativeAI(process.env.API_KEY);

const model = ai.getGenerativeModel({
  model: "gemini-3-flash-preview",
  systemInstruction: process.env.EX_PROMPT,
});

const chat = model.startChat({
  history: [],
});

async function main() {
  const userProblem = readlineSync.question("Ask me anything --> ");

  if (userProblem.toLowerCase() === "exit") return;

  try {
    const result = await chat.sendMessage(userProblem);
    const response = await result.response;

    console.log("AI:", response.text());
    main(); // keep the conversation going
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();
