// supabase/functions/_shared/cors.ts
export const corsHeaders = {
    'Access-Control-Allow-Origin': '*', // Ou seu domínio específico em produção
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};