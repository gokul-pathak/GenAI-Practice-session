import "dotenv/config";
import { GoogleGenerativeAI } from "@google/generative-ai";

const ai = new GoogleGenerativeAI(process.env.API_KEY);

async function main() {
  const model = ai.getGenerativeModel({ model: "gemini-2.5-flash" });
  try {
    const result = await model.generateContent(
      "Explain how AI works in a few words",
    );
    const response = await result.response;
    console.log(response.text());
  } catch (error) {
    console.error("Error during content generation:", error.message);
  }
}

await main();
