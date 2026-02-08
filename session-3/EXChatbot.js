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
const chatHistory = [];

const model = ai.getGenerativeModel({
  model: "gemini-3-flash-preview",
  systemInstruction: process.env.EX_PROMPT,
});

const chat = model.startChat({
  history: chatHistory,
});

async function main() {
  const userProblem = readlineSync.question("Ask me anything --> ");

  if (userProblem.toLowerCase() === "exit") {
    console.log("Goodbye 👋");
    return;
  }

  try {
    const result = await chat.sendMessage(userProblem);
    const responseText = result.response.text();
    chatHistory.push(
      {
        role: "user",
        parts: [{ text: userProblem }],
      },
      {
        role: "model",
        parts: [{ text: responseText }],
      },
    );

    console.log("Your EX:", responseText);
    main(); // keep the conversation going
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();
