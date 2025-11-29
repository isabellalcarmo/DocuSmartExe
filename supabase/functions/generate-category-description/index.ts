// supabase/functions/generate-category-description/index.ts

import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { corsHeaders } from '../_shared/cors.ts'

const GEMINI_API_KEY = Deno.env.get("GEMINI_API_KEY_EDGE")
const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${GEMINI_API_KEY}`

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { category_name } = await req.json();
    if (!category_name) {
      throw new Error("O nome da categoria é obrigatório.");
    }

    const prompt = `
      Você é um assistente para um aplicativo de organização de documentos. Sua tarefa é gerar uma descrição concisa e útil em português do Brasil sobre quais tipos de arquivos devem ser colocados em uma nova categoria criada pelo usuário.

      A descrição deve ser otimizada para que um modelo de IA possa usá-la posteriormente para classificar documentos. Responda apenas com a descrição, sem frases introdutórias como "Esta categoria serve para...".

      Baseie o estilo, o tom e o formato da sua resposta no exemplo de alta qualidade abaixo:
      ---
      EXEMPLO:
      Categoria de Exemplo: "Saúde"
      Descrição de Exemplo: "Registros e informações médicas, como resultados de exames laboratoriais (sangue, urina, imagem como raio-x, ultrassom, ressonância), laudos médicos, receitas de medicamentos, atestados médicos, relatórios de consultas, histórico de vacinação, comprovantes de planos de saúde ou despesas médicas."
      ---

      Agora, gere uma descrição no mesmo estilo para a seguinte categoria (não responda com a categoria, apenas com a descrição da mesma):
      Descrição exata da categoria: "${category_name}"`;

    const geminiResponse = await fetch(GEMINI_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          candidateCount: 1,
          maxOutputTokens: 256,
          temperature: 0.4,
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

    const generatedDescription = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text?.trim();

    if (generatedDescription) {
      return new Response(JSON.stringify({ description: generatedDescription }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    } else {
      console.warn("A resposta do Gemini não continha texto:", JSON.stringify(geminiData));
      return new Response(JSON.stringify({ error: "A resposta da IA veio em um formato inesperado ou vazia." }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      });
    }

  } catch (error) {
    console.error("Erro crítico na Edge Function:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 500,
    });
  }
});