# Avisos de terceiros

## Runtime XHTTP

Esta distribuição inclui um runtime de transporte **XHTTP sobre SSH** derivado do projeto [SocksRevive-XHTTP-DEMO](https://git.dr2.site/penguinehis/SocksRevive-XHTTP-DEMO), na revisão pública `Compiled` (`3d36f2421ec83a41ee4f0958ea10dc7f6ed71854`). O runtime foi incorporado à APK base para que o modo `SSH_XHTTP` execute uma ponte XHTTP real, em vez de somente aceitar o texto do modo.

| Componente | Origem | Licença | Integração no projeto |
|---|---|---|---|
| Runtime XHTTP, ponte GET/POST, serviço VPN e dependências selecionadas | `penguinehis/SocksRevive-XHTTP-DEMO` | GPL-3.0-or-later | Estagiado e integrado por `scripts/stage_xhttp_core.py` e `scripts/integrate_xhttp_base.py` |
| Licença completa | Projeto de referência | GPL-3.0-or-later | `LICENSES/GPL-3.0.txt` |

A integração local acrescenta a ponte `XHttpLauncher`, que converte o perfil remoto entregue pelo painel para as chaves consumidas pelo runtime e inicia o serviço XHTTP. Os scripts, a base `scripts/base.apk` e a documentação de configuração permanecem disponíveis neste repositório como parte do código-fonte correspondente da integração.

> Ao distribuir uma APK baseada neste runtime, mantenha este aviso, a licença GPLv3 e o acesso ao código-fonte correspondente da integração e da referência.
