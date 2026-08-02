import { z } from 'zod';
import BCrypt from '../../utils/bcrypt';
import prisma from '../../config/prisma-client';
import SafeCallback from '../../utils/safe-callback';
import AdminAuthentication from '../../middlewares/admin-auth';
import csrfProtection from '../../middlewares/csrf-protection';
import { FastifyReply, FastifyRequest, RouteOptions } from 'fastify';

const paramsSchema = z.object({
  id: z.string(),
});

const updateUserSchema = z.object({
  password: z.string().min(6).max(20).optional(),
  email: z.string().email().optional(),
  is_admin: z.boolean().optional(),
  username: z.string().min(6).max(20).optional(),
});

export default {
  url: '/users/:id',
  method: 'PUT',
  onRequest: [AdminAuthentication.user, csrfProtection],
  handler: async (req: FastifyRequest, reply: FastifyReply) => {
    const { id: userId } = paramsSchema.parse(req.params);
    const data = updateUserSchema.parse(req.body);

    const user = await SafeCallback(() =>
      prisma.user.findUnique({ where: { id: userId } })
    );

    if (!user) {
      reply.status(404);
      reply.header('csrf-token', req.csrfProtection.generateCsrf());
      throw new Error('Usuario nao encontrado');
    }

    // Se tentar mudar username, verificar se ja existe
    if (data.username && data.username.toLowerCase() !== user.username) {
      const newUsername = data.username.toLowerCase();
      const exists = await SafeCallback(() =>
        prisma.user.findFirst({
          where: { username: newUsername },
        })
      );
      if (exists) {
        reply.status(409);
        reply.header('csrf-token', req.csrfProtection.generateCsrf());
        throw new Error('Nome de usuario ja esta sendo utilizado');
      }
    }

    // Se tentar mudar email, verificar se ja existe
    if (data.email && data.email !== user.email) {
      const exists = await SafeCallback(() =>
        prisma.user.findFirst({
          where: { email: data.email },
        })
      );
      if (exists) {
        reply.status(409);
        reply.header('csrf-token', req.csrfProtection.generateCsrf());
        throw new Error('Ja existe uma conta com esse e-mail');
      }
    }

    const updateData: any = {};
    if (data.password) updateData.password = BCrypt.hash(data.password);
    if (data.email) updateData.email = data.email;
    if (data.username) updateData.username = data.username.toLowerCase();
    if (data.is_admin !== undefined) updateData.is_admin = data.is_admin;

    const updated = await SafeCallback(() =>
      prisma.user.update({
        where: { id: userId },
        data: updateData,
        select: {
          id: true,
          username: true,
          email: true,
          is_admin: true,
        },
      })
    );

    if (!updated) {
      throw new Error('Nao foi possivel atualizar o usuario');
    }

    reply.send({ status: 200, message: 'Usuario atualizado com sucesso', user: updated });
  },
} as RouteOptions;
