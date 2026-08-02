import prisma from '../../config/prisma-client';
import SafeCallback from '../../utils/safe-callback';
import AdminAuthentication from '../../middlewares/admin-auth';
import csrfProtection from '../../middlewares/csrf-protection';
import { FastifyReply, FastifyRequest, RouteOptions } from 'fastify';

export default {
  url: '/users/:id',
  method: 'DELETE',
  onRequest: [AdminAuthentication.user, csrfProtection],
  handler: async (req: FastifyRequest, reply: FastifyReply) => {
    const userId = req.params.id;

    // Não permitir que o admin remova a si mesmo
    if (userId === req.user.id) {
      reply.status(403);
      reply.header('csrf-token', req.csrfProtection.generateCsrf());
      throw new Error('Voce nao pode remover sua propria conta');
    }

    const user = await SafeCallback(() =>
      prisma.user.findUnique({ where: { id: userId } })
    );

    if (!user) {
      reply.status(404);
      reply.header('csrf-token', req.csrfProtection.generateCsrf());
      throw new Error('Usuário não encontrado');
    }

    // Cascade delete já configurado no schema para AppConfig, Category, Cdn, AppText, AppLayout
    const deleted = await SafeCallback(() =>
      prisma.user.delete({ where: { id: userId } })
    );

    if (!deleted) {
      throw new Error('Não foi possível remover o usuário');
    }

    reply.send({ status: 200, message: 'Usuário removido com sucesso' });
  },
} as RouteOptions;
