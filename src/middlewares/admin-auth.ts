import CookieManager from '../utils/cookie-manager';
import { FastifyReply, FastifyRequest } from 'fastify';
import Authentication from './authentication';

export default class AdminAuthentication {
  static async user(req: FastifyRequest, reply: FastifyReply) {
    // Primeiro autentica o usuário normalmente
    await Authentication.user(req, reply);

    // Verifica se o usuário é admin
    if (req.user && !req.user.is_admin) {
      reply.status(403);
      throw new Error('Acesso restrito a administradores');
    }
  }
}
