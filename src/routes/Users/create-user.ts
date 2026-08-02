import { z } from 'zod';
import BCrypt from '../../utils/bcrypt';
import prisma from '../../config/prisma-client';
import SafeCallback from '../../utils/safe-callback';
import AppTextDefault from '../DTunnel/AppText/defaults';
import csrfProtection from '../../middlewares/csrf-protection';
import AdminAuthentication from '../../middlewares/admin-auth';
import { FastifyReply, FastifyRequest, RouteOptions } from 'fastify';

const createUserSchema = z.object({
  username: z.string().min(6).max(20),
  password: z.string().min(6).max(20),
  email: z.string().email(),
  is_admin: z.boolean().optional().default(false),
});

export default {
  url: '/users',
  method: 'POST',
  onRequest: [AdminAuthentication.user, csrfProtection],
  handler: async (req: FastifyRequest, reply: FastifyReply) => {
    const { username, email, password, is_admin } = createUserSchema.parse(req.body);

    const usernameAlreadyExists = await SafeCallback(() =>
      prisma.user.findFirst({
        where: {
          username: username.toLowerCase(),
        },
      })
    );

    if (usernameAlreadyExists) {
      reply.status(409);
      reply.header('csrf-token', req.csrfProtection.generateCsrf());
      throw new Error('Nome de usuário já está sendo utilizado');
    }

    const emailAlreadyExists = await SafeCallback(() =>
      prisma.user.findFirst({
        where: { email },
      })
    );

    if (emailAlreadyExists) {
      reply.status(409);
      reply.header('csrf-token', req.csrfProtection.generateCsrf());
      throw new Error('Ja existe uma conta com esse e-mail');
    }

    const passwordHash = BCrypt.hash(password);

    const user = await SafeCallback(() =>
      prisma.user.create({
        data: {
          email,
          username: username.toLowerCase(),
          password: passwordHash,
          is_admin: is_admin,
        },
      })
    );

    if (!user) {
      throw new Error('Não foi possível criar usuário');
    }

    // Criar textos padrão para o novo usuário
    for await (const AppText of AppTextDefault) {
      await SafeCallback(() =>
        prisma.appText.create({
          data: {
            user_id: user.id,
            label: AppText.label,
            text: AppText.text,
          },
        })
      );
    }

    reply.status(201).send({ status: 201, message: 'Usuário criado com sucesso', user: { username: user.username, is_admin: user.is_admin } });
  },
} as RouteOptions;
