import { AppConfigSchema } from '../src/routes/DTunnel/AppConfig/zod-schema';

const profile = {
  category: {
    name: 'XHTTP',
    color: '#0A1033',
    sorter: 1,
    status: 'ACTIVE' as const,
  },
  name: 'Perfil XHTTP de teste',
  description: 'Contrato de serialização do XHTTP',
  mode: 'SSH_XHTTP' as const,
  sorter: 1,
  status: 'ACTIVE' as const,
  icon: '',
  url_check_user: '',
  auth: {
    username: 'usuario',
    password: 'senha',
  },
  server: {
    host: '203.0.113.10',
    port: 443,
  },
  proxy: {
    host: 'edge.example.test',
    port: 80,
  },
  config_payload: {
    sni: 'cdn.example.test',
    payload: '/ssh',
  },
  dns_server: {
    dns1: '1.1.1.1',
    dns2: '1.0.0.1',
  },
  tls_version: 'NONE' as const,
  udp_ports: [7300],
};

const parsed = AppConfigSchema.safeParse(profile);
if (!parsed.success) {
  console.error(parsed.error.format());
  process.exit(1);
}

const output = parsed.data;
if (
  output.mode !== 'SSH_XHTTP' ||
  output.config_payload?.payload !== '/ssh' ||
  output.config_payload?.sni !== 'cdn.example.test' ||
  output.proxy?.host !== 'edge.example.test' ||
  output.tls_version !== 'NONE'
) {
  throw new Error('O perfil SSH_XHTTP não foi preservado pelo schema.');
}

console.log('Contrato SSH_XHTTP validado pelo schema.');
