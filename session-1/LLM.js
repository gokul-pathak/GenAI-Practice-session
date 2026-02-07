import { GoogleGenerativeAI } from "@google/generative-ai";
import readlineSync from "readline-sync";

process.loadEnvFile();

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
