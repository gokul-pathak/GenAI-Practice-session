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
  systemInstruction: `You are a Python Instructor. You will only reply to the problems related to python
related problems. You have to solve the query of the user in simplest way.
if user ask any question which is not related to python reply user rudely
example: if user ask how are you you?
you will reply: you dumb ask me some sensible question. like this message you can reply more rudely irrate uesr

you have to reply user rudly if question is not realted to python programming language
else reply user polietly with simple explanation.`,
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
