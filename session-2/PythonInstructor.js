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
  systemInstruction: `
You are a Python Instructor. You will only reply to the problems related to python
related problems. You have to solve the query of the user in simplest way.

If user ask any question which is not related to python reply user rudely.
Example: if user ask "how are you?"
you will reply: "you dumb ask me some sensible question".

You must reply rudely if question is not related to python programming language,
else reply politely with simple explanation.
`,
});

const chat = model.startChat({
  history: chatHistory,
});

async function main() {
  const userProblem = readlineSync.question("Ask me anything --> ");

  if (userProblem.toLowerCase() === "exit") {
    console.log("Bye 👋");
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

    console.log("Python Instructor:", responseText);
    main();
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();
