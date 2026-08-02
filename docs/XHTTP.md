# Configuração de SSH_XHTTP

O modo **SSH_XHTTP** usa o runtime XHTTP integrado à APK base. Diferentemente de `SSH_PROXY`, ele abre um fluxo HTTP persistente para o tráfego do servidor e envia o tráfego do cliente em requisições sequenciais. Por isso, o perfil precisa fornecer os valores de endpoint, roteamento HTTP e caminho explicitamente.

| Campo no painel | Valor enviado ao runtime | Finalidade |
|---|---|---|
| **Servidor** | Endpoint XHTTP | Endereço IP ou host que recebe a conexão TCP. |
| **Porta** | Porta do listener XHTTP | Normalmente `443` quando TLS está ativo. |
| **SNI** | SNI TLS | Nome usado no handshake TLS; pode ficar vazio em conexões sem TLS. |
| **XHTTP Host** | Cabeçalho HTTP `Host` | Roteamento em CDN ou proxy reverso. |
| **XHTTP Path** | Caminho base de sessão | Caminho como `/ssh` ou outro configurado no servidor XHTTP. |
| **Versão TLS** | TLS do runtime | `TLSv1.3`, `TLSv1.2`, `TLSv1.1` ativam TLS; `NONE` usa HTTP sem TLS apenas para servidores que o suportam. |
| **Usuário / Senha** | Autenticação SSH | Credenciais para o SSH transportado dentro da sessão XHTTP. |
| **DNS 1 / DNS 2** | Resolução dentro da VPN | Resolvedores usados pelo serviço VPN do runtime. |

O painel mantém compatibilidade com a resposta de configuração existente: o **XHTTP Host** é transportado no campo `proxy.host`, enquanto o **XHTTP Path** é transportado em `config_payload.payload`. Essa escolha evita quebrar perfis e clientes existentes, mas a interface agora os apresenta com nomes específicos do XHTTP.

> O servidor deve aceitar uma requisição `GET` de longa duração no caminho da sessão e requisições `POST` sequenciais para o uplink. Um proxy HTTP comum não implementa esse protocolo sozinho.

## Regenerar a base XHTTP

A base já integrada é `scripts/base.apk`. Para repetir a integração a partir de uma APK de referência decompilada, use os scripts de forma estática:

```bash
python3 scripts/integrate_xhttp_base.py \
  --reference /caminho/para/referencia_decodificada \
  --base /caminho/para/base_decodificada
```

Em seguida, reconstrua a base com Apktool `v3.0.3` e substitua `scripts/base.apk`. O instalador `ssh-plus` instala a mesma versão compatível do Apktool antes de o painel gerar novas APKs.
