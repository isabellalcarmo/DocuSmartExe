// supabase/functions/classify-document-gemini/index.ts
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { corsHeaders } from '../_shared/cors.ts'

const GEMINI_API_KEY = Deno.env.get("GEMINI_API_KEY_EDGE")
const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
    }

    const { document_text, categories } = await req.json();

    if (!document_text || !categories) {
      return new Response(JSON.stringify({ error: "Dados ausentes: document_text e categories são obrigatórios." }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 400,
      });
    }

    const categoryNamesList = Object.keys(categories);
    const categoryNamesStr = categoryNamesList.join(", ");
    const categoryDescriptionsPrompt = Object.entries(categories)
      .map(([name, desc]) => `- ${name}: ${desc}`)
      .join("\n");

    const prompt = `
      Analise o seguinte texto de um documento e classifique-o em UMA das seguintes categorias.
      Responda APENAS com o NOME EXATO da categoria da lista. Não adicione nenhuma outra palavra, explicação ou pontuação.

      Categorias Disponíveis (escolha uma da lista abaixo):
      ${categoryNamesStr}

      Descrições para ajudar na escolha (não responda com a descrição, apenas com o nome da categoria):
      ${categoryDescriptionsPrompt}

      Texto do Documento para classificar:
      ---
      ${document_text.substring(0, 15000)} 
      ---

      Nome Exato da Categoria Escolhida:`;

    const geminiResponse = await fetch(GEMINI_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          candidateCount: 1,
          maxOutputTokens: 1000,
          temperature: 0.1,
        }
      }),
    });

    if (!geminiResponse.ok) {
      const errorBody = await geminiResponse.text();
      console.error("Erro da API Gemini:", errorBody);
      return new Response(JSON.stringify({ error: `Erro da API Gemini: ${geminiResponse.statusText}`, details: errorBody }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: geminiResponse.status,
      });
    }

    const geminiData = await geminiResponse.json();
    const rawCategory = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text?.trim().replace(/['"]/g, "");

    console.log("RESPOSTA CRUA DO GEMINI:", geminiData);
    console.log("!!! RESPOSTA EXTRAÍDA (rawCategory):", rawCategory);

    let chosenCategory = "Outros";
    let confidence = 0.3;

    if (geminiData.candidates && geminiData.candidates.length > 0 && geminiData.candidates[0].content && geminiData.candidates[0].content.parts && geminiData.candidates[0].content.parts.length > 0) {
        const rawCategory = geminiData.candidates[0].content.parts[0].text.trim().replace(/['"]/g, ""); // Remove aspas
        
        if (categoryNamesList.includes(rawCategory)) {
          chosenCategory = rawCategory;
          confidence = 0.95;
        } else {
          for (const catName of categoryNamesList) {
            if (catName.toLowerCase() === rawCategory.toLowerCase()) {
              chosenCategory = catName;
              confidence = 0.90;
              break;
            }
            if (catName.toLowerCase().includes(rawCategory.toLowerCase()) || rawCategory.toLowerCase().includes(catName.toLowerCase())) {
              chosenCategory = catName;
              confidence = 0.85;
              break; 
            }
          }
        }
    } else {
      console.warn("Resposta inesperada do Gemini ou sem candidatos:", geminiData);
    }

    return new Response(JSON.stringify({ category: chosenCategory, confidence: confidence, raw_gemini_response: geminiData }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 200,
    });

  } catch (error) {
    console.error("Erro na Edge Function:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 500,
    });
  }
});