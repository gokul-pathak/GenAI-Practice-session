import { GoogleGenerativeAI } from "@google/generative-ai";
import readlineSync from "readline-sync";
import { join } from "node:path";

// This makes sure it finds the .env at the root,
// even if you run the file from inside the session-1 folder.
try {
  process.loadEnvFile(join(import.meta.dirname, "../.env"));
} catch (e) {
  // Fallback to default load if the above fails
  process.loadEnvFile();
}

const ai = new GoogleGenerativeAI(process.env.API_KEY);
const model = ai.getGenerativeModel({ model: "gemini-2.0-flash" });

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
    main();
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();
