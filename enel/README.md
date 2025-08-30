# Pasta ENEL - Dados e Configurações

Esta pasta contém os dados específicos da ENEL que devem estar no OneDrive para acesso da tesouraria.

## Estrutura

```
enel/
├── relação_enel.xlsx             # Mapeamento Casas de Oração → Instalações ENEL
├── config/
│   └── onedrive_config.json      # Configurações estrutura OneDrive
└── templates/
    └── (modelos de planilhas)
```

## ARQUIVO BASE DO SISTEMA (IGUAL BRK)

### `relação_enel.xlsx` - NA PASTA RAIZ ONEDRIVE ENEL

Este é o **arquivo mais importante** do sistema! Deve estar na pasta raiz `/ENEL/relação_enel.xlsx` no OneDrive.

**Estrutura obrigatória:**
- **Coluna A**: Casa de Oração (ex: "BR 21-0270 - CENTRO")
- **Coluna B**: Número da Instalação ENEL  
- **Coluna C**: Dia de Vencimento (1-31)

**TODA** inclusão/exclusão de Casa de Oração ou alteração de data de vencimento deve ser feita neste arquivo!

## Configurações OneDrive

O arquivo `config/onedrive_config.json` define:
- Estrutura de pastas no OneDrive ENEL
- Permissões de acesso
- Configurações do sistema

## IMPORTANTE

**TODOS** os dados ENEL devem estar no OneDrive para acesso da tesouraria. 
**NUNCA** usar fallback local no disco do Render.