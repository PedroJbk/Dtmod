import { Render } from '../../../config/render-config';
import formatDate from '../../../utils/format-date';
import AdminAuthentication from '../../../middlewares/admin-auth';
import { FastifyRequest, FastifyReply, RouteOptions } from 'fastify';

export default {
  url: '/users',
  method: 'GET',
  onRequest: [AdminAuthentication.user],
  handler: async (req: FastifyRequest, reply: FastifyReply) => {
    Render.page(req, reply, '/users/index.html', {
      user: req.user,
      formatDate,
      active: 'users',
      csrfToken: req.csrfProtection.generateCsrf(),
    });
  },
} as RouteOptions;
