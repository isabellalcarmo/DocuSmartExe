// supabase/functions/classify-document-file/index.ts
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { corsHeaders } from '../_shared/cors.ts'

const GEMINI_API_KEY = Deno.env.get("GEMINI_API_KEY_EDGE")
const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { file_data_base64, mime_type, categories } = await req.json();

    if (!file_data_base64 || !mime_type || !categories) {
      throw new Error("Dados ausentes: file_data_base64, mime_type e categories são obrigatórios.");
    }

    const categoryNamesList = Object.keys(categories);
    const categoryNamesStr = categoryNamesList.join(", ");

    const prompt_text = `Analise o conteúdo do arquivo fornecido e classifique-o em UMA das seguintes categorias: ${categoryNamesStr}. Responda APENAS com o NOME EXATO da categoria.`;

    const geminiResponse = await fetch(GEMINI_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{
          parts: [
            { text: prompt_text },
            { inlineData: {
                mimeType: mime_type,
                data: file_data_base64
            }}
          ]
        }],
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
    let confidence = 0.3; // (Vamos adicionar a confiança também)

    if (rawCategory && categoryNamesList.includes(rawCategory)) {
        chosenCategory = rawCategory;
        confidence = 0.95;
    } else if (rawCategory) {
        // Lógica de fallback robusta (copiada da sua outra função)
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

    return new Response(JSON.stringify({ category: chosenCategory, confidence: 0.98 }), {
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