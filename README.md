# Cache Cleaner

Limpeza segura de arquivos temporários e caches do Windows, criada para ajudar a recuperar espaço em disco e reduzir resíduos deixados por jogos e aplicativos.

## Limpeza completa

Execute no terminal do Windows:

```powershell
python cleancache.py
```

Ao executar sem argumentos, o programa:

- limpa temporários do usuário e do Windows;
- limpa caches de navegadores, Steam, AMD, NVIDIA e Windows;
- limpa logs e dumps de aplicativos;
- limpa caches de launchers como Discord, Epic Games e Battle.net;
- limpa Prefetch e downloads pendentes do Windows Update;
- limpa o cache DNS;
- esvazia a Lixeira;
- solicita permissão de Administrador quando necessário.

## Modo prévia

Para visualizar o que seria removido sem apagar arquivos:

```powershell
python cleancache.py --teste
```

## Opções

```text
--teste                 Executa sem apagar arquivos
--sem-prefetch          Não limpa o Prefetch do Windows
--sem-windows-update    Não limpa downloads pendentes do Windows Update
--jogos                 Alias da limpeza completa padrão
--dns                   Limpa somente o cache DNS
--lixeira               Esvazia somente a Lixeira
```

## Requisitos

- Windows
- Python 3.10 ou superior
- Permissão de Administrador para limpar os diretórios protegidos

## Recomendações

- Feche jogos e launchers antes da limpeza.
- Execute uma ou duas vezes por semana.
- Comece pelo modo `--teste`.
- Não use limpeza forçada de RAM: o Windows já gerencia a memória automaticamente.
- Prefetch e downloads do Windows Update podem ser preservados com `--sem-prefetch` e `--sem-windows-update`.

## Aviso

Alguns caches serão recriados pelos aplicativos. Arquivos em uso são ignorados. Prefira fechar navegadores e programas antes de executar a limpeza completa.
