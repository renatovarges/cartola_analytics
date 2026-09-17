# Atualização do site para a rodada 28

## Escopo da publicação

- Motor de indicações individuais, recorrência e cruzamento com scouts cedidos.
- Frases sem limite fixo de cinco destaques; divisão para copiar no Telegram.
- Histórico de AF atualizado até a planilha pós-R27 de 17/09/2026.
- Tela inicial na R28, com três jogos por mando e corte em 18/09/2026.
- O PIN é lido de `pin` nos Secrets do Streamlit ou de `TCC_PIN` no ambiente.

## Dados da planilha

O repositório GitHub é público. A planilha `Scouts_Reorganizado.xlsx` e o
pacote `entrega_r28` ficam locais. No site, use **Carregar Scouts_Reorganizado.xlsx** e envie a
planilha pós-R27 mais recente. Os nomes históricos aparecem como
`a confirmar` quando a API do Cartola não traz escalações atuais.

## Conferência após publicar

1. Abrir o endereço do site e confirmar que a versão exibida é `2026.09.17-4`.
2. Entrar com o PIN configurado nos Secrets da hospedagem.
3. Enviar a planilha pós-R27. Confirmar R28, três jogos e `POR_MANDO`.
4. Gerar a tabela de meias e conferir dez confrontos, frases individuais e
   a trilha de auditoria. Repetir a geração nas demais posições.
5. Confirmar cópia das frases longas em partes e geração de PNG.

Os testes locais passaram com 49 testes e 9 subtestes. O teste da interface
Streamlit gerou a tabela de meias com dez confrontos e uma legenda sem erros.
