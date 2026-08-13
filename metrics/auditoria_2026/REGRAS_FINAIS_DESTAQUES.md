# Regras finais de destaque

Princípio: a cor não tem cota. Toda célula que alcançar uma faixa validada recebe cor; número mediano permanece branco.

Os cortes abaixo têm base de três jogos. Métricas de soma crescem proporcionalmente nas janelas de 5 e 10 jogos. Médias permanecem absolutas.

| Posição | Scout | Destaque | Forte | Excepcional |
|---|---:|---:|---:|---:|
| Atacantes | Finalizações | 17 | 20 | 23 |
| Atacantes | Média básica | 2,6 | 3,0 | 3,5 |
| Meias | Passes para finalização | 8 | 9 | 12 |
| Meias | Finalizações | 7 | 9 | 12 |
| Meias | G+A | 2 | 3 | 5 |
| Meias | Média básica | 2,4 | 2,9 | 3,3 |
| Volantes | Desarmes | 11 | 14 | 17 |
| Volantes | G+A | 2 | 3 | 4 |
| Volantes | Média básica | 3,4 | 4,0 | 4,8 |
| Laterais | Desarmes | 6 | 8 | 10 |
| Laterais | G+A | 1 | 2 | 3 |
| Laterais | Média básica | 3,1 | 3,7 | 4,2 |
| Zagueiros | Desarmes | 9 | 11 | 14 |
| Zagueiros | Finalizações individuais | 3 | 4 | 5 |
| Zagueiros | Média básica | 2,7 | 3,1 | 3,5 |

## Regras específicas

- Finalizações de zagueiros: o número é o total do zagueiro que mais finalizou no recorte, e não a soma de todos os zagueiros.
- Média básica de zagueiros: 2,7, 3,1 e 3,5 representam aproximadamente os 7,5%, 2,5% e 1% superiores das 350 janelas históricas de três jogos por mando avaliadas em 2026.
- Pontuação média de zagueiros continua visível, mas sem cor automática.
- SG é um scout do time e não um scout individual.
- Goleiros mantêm dois caminhos independentes: SG e defesas. Um goleiro pode ser forte em um caminho e ruim no outro.
- A cor azul mais forte dos goleiros é `#60A5FA`, preservando contraste com fonte preta.

## Validação operacional

- 18 testes automatizados aprovados.
- Seis posições renderizadas com 10 confrontos em cada janela de 3, 5 e 10 jogos.
- Total: 18 tabelas completas inspecionadas, sem falhas de geração, colunas ausentes ou textos cortados.

## Régua editorial das frases

- Cor e frase têm funções diferentes: toda marca estatística validada continua colorida na tabela.
- A frase exige valor excepcional ou cruzamento em que produção e concessão estejam, ambas, na faixa forte.
- A legenda mostra no máximo os dois melhores casos por scout.
- Goleiros mostram no máximo cinco perfis e precisam ter pelo menos um caminho classificado como forte.
- SG permanece na tabela de defensores, mas não entra nas frases de zagueiros e laterais.
