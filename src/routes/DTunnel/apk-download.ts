import path from 'path';
import fs from 'fs';
import Authentication from '../../middlewares/authentication';
import { FastifyReply, FastifyRequest, RouteOptions } from 'fastify';

export default {
  url: '/apk/download/:version',
  method: 'GET',
  onRequest: [Authentication.user],
  handler: async (req: FastifyRequest, reply: FastifyReply) => {
    const { version } = (req.params as { version: string });
    const validVersions = ['ssh', 'pro', 'v2ray'];
    
    if (!validVersions.includes(version)) {
      return reply.status(400).send({ message: 'Versão inválida' });
    }

    const apkDir = path.resolve(process.cwd(), 'frontend', 'public', 'apk');
    const apkFile = path.join(apkDir, `dtunnel-${version}.apk`);

    if (!fs.existsSync(apkFile)) {
      return reply.status(404).send({ message: `APK ${version} não disponível` });
    }

    reply.header('Content-Type', 'application/vnd.android.package-archive');
    reply.header('Content-Disposition', `attachment; filename="dtunnel-${version}.apk"`);
    return reply.send(fs.createReadStream(apkFile));
  },
} as RouteOptions;
