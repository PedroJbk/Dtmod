<h1 align="center">
  <img src="https://i.ibb.co/7SMc2NX/logo.jpg" alt="DTunnel" style="width: 80px; height: 80px; border-radius: 50%;">
</h1>

<p align="center">
 <img src="https://img.shields.io/static/v1?label=DTunnel&message=Mod&color=E51C44&labelColor=0A1033" alt="DTunnelMod" />
 <img src="https://img.shields.io/static/v1?label=Open&message=Source&color=E51C44&labelColor=0A1033" alt="DTunnelMod" />
</p>

![cover](https://i.ibb.co/0yPYBjy/preview.png)

## 🔔 Atualizações

- [x] Suporte DTunnelMod 4.5.7
- [x] Adicionado CDN
- [x] App Text atualizado
- [x] App Layout atualizado
- [x] Adicionado modo HYSTERIA, SSH_DNSTT
- [x] Adicionado gerenciador simples de versões
- [x] Adicionado runtime integrado para `SSH_XHTTP`, com validação de base APK e geração assinada

## SSH_XHTTP

O modo `SSH_XHTTP` agora é encaminhado para um runtime XHTTP real dentro da APK base, eliminando a falha `Invalid mode: SSH_XHTTP`. Os campos obrigatórios e o mapeamento de compatibilidade estão documentados em [docs/XHTTP.md](docs/XHTTP.md). A integração incorpora código de terceiros sob GPLv3; consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) e [LICENSES/GPL-3.0.txt](LICENSES/GPL-3.0.txt) antes de redistribuir a APK.

## :rocket: Principais funções

- [x] Layout storages
- [x] Edição de textos
- [x] Edição de layouts
- [x] Edição de categorias
- [x] Edição de configurações

## Iniciando o projeto

Primeiro você deve criar seu arquivo de variável ambiente `.env` na pasta do projeto.
Exemplo:

```cl
PORT=                // 3000
NODE_ENV=            // "production"
DATABASE_URL=        // "file:./database.db"
CSRF_SECRET=         //
JWT_SECRET_KEY=      //
JWT_SECRET_REFRESH=  //
```

`CSRF_SECRET`, `JWT_SECRET_KEY`, `JWT_SECRET_REFRESH` são chaves secretas sensíveis, ninguém além de você deve ter acesso a elas, para garantir a segurança do painel recomendo que utilizem este comando para gerar chaves privadas:

```js
node -e "console.log(require('crypto').randomBytes(256).toString('base64'));"
```

### 1. Instale as dependências:

```bash
npm install
```

### 2. Gerar artefactos do prisma

```bash
npx prisma generate
```

### 3. Crie as migrations do banco de dados

```bash
npx prisma migrate deploy
```

### 4. Rodando o projeto

```bash
npm run start
```

<br />
