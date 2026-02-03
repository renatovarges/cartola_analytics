# Próximas Funcionalidades - Cartola Analytics

## ✅ CONCLUÍDO

### Upload de Planilha
- [x] Implementar upload via Streamlit
- [x] Validação de estrutura
- [x] Sistema de cache
- [x] Substituir arquivo atual

### Sistema de Aliases de Times
- [x] Mapeamento de nomes variados (ATLÉTICO → ATLÉTICO-MG)
- [x] Integração na engine
- [x] Correção de bugs de matching

---

## FASE 1: Fundação de Dados Pendente

### Separação Meias/Volantes
- [x] Criar tabela de mapeamento jogador → classificação
- [x] Implementar lógica de filtro
- [x] Interface para atualização manual

### Assistência para Finalização (AF)
- [x] Receber fórmula do usuário (Cálculo via Delta)
- [x] Implementar cálculo jogo a jogo (Injeção via Merge)
- [x] Adicionar coluna AF na tabela

## FASE 2: Visualização Avançada

### Coloração Inteligente
- [x] Receber regras dos 3 tons de verde (Aplicado Tercis)
- [x] Implementar lógica por coluna (renderer_v2.py)
- [ ] Adicionar legenda opcional

### Sombreado nos Escudos
- [x] Implementar drop shadow
- [x] Ajustar opacidade/offset

### Qualidade e Resolução
- [x] Aumentar DPI (300→600)
- [x] Otimizar anti-aliasing (Via alta resolução)
- [x] Testar qualidade final

## FASE 3: Expansão de Posições

### Tabela de Zagueiros
- [x] Configurar Loader (SG, DS)
- [x] Engine: Calcular métricas defensivas (SG, DE, CHUTES, PTS)
- [x] Renderer: Layout específico com Coloração Inteligente
- [x] App: Integração no seletor lateral
- [x] Teste final de geração
