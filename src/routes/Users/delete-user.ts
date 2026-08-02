import { z } from 'zod';
import prisma from '../../config/prisma-client';
import SafeCallback from '../../utils/safe-callback';
import AdminAuthentication from '../../middlewares/admin-auth';
import csrfProtection from '../../middlewares/csrf-protection';
import { FastifyReply, FastifyRequest, RouteOptions } from 'fastify';

const paramsSchema = z.object({
  id: z.string(),
});

export default {
  url: '/users/:id',
  method: 'DELETE',
  onRequest: [AdminAuthentication.user, csrfProtection],
  handler: async (req: FastifyRequest, reply: FastifyReply) => {
    const { id: userId } = paramsSchema.parse(req.params);

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
      throw new Error('Usuario nao encontrado');
    }

    // Cascade delete ja configurado no schema para AppConfig, Category, Cdn, AppText, AppLayout
    const deleted = await SafeCallback(() =>
      prisma.user.delete({ where: { id: userId } })
    );

    if (!deleted) {
      throw new Error('Nao foi possivel remover o usuario');
    }

    reply.send({ status: 200, message: 'Usuario removido com sucesso' });
  },
} as RouteOptions;
