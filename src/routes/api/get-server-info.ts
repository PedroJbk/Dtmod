import { FastifyReply, FastifyRequest, RouteOptions } from 'fastify';
export default {
  url: '/api/dtunnelmod/server-info',
  method: 'GET',
  handler: async (_req: FastifyRequest, reply: FastifyReply) => {
    reply.header('Content-Type', 'application/json');
    return reply.send({
      device_url: process.env.DEVICE_DOMAIN || '',
      app_url: process.env.APP_DOMAIN || '',
      panel_url: `http://${process.env.SERVER_IP || ''}:${process.env.PORT || '3000'}`,
    });
  },
} as RouteOptions;
