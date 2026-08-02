import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  const username = 'Bk2026@12';
  const password = '2012@bk2520';
  const email = 'admin@dtunnel.com';

  const passwordHash = bcrypt.hashSync(password, 10);

  const user = await prisma.user.upsert({
    where: { username: username.toLowerCase() },
    update: {
      password: passwordHash,
      is_admin: true,
    },
    create: {
      username: username.toLowerCase(),
      password: passwordHash,
      email,
      is_admin: true,
    },
  });

  console.log({ message: 'Super Administrador configurado com sucesso', user: user.username, is_admin: user.is_admin });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
